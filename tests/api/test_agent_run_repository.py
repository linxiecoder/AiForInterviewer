from __future__ import annotations

import pytest

from app.infrastructure.db.repositories.ai_runtime import (
    AgentCheckpointRefRepository,
    AgentNodeRunRepository,
    AgentRunRepository,
    IdempotencyConflict,
)
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema


OWNER_A = "owner_a"
OWNER_B = "owner_b"


def test_agent_run_repository_is_owner_scoped_and_idempotent() -> None:
    session_factory = _session_factory()
    repository = AgentRunRepository(session_factory)

    created = repository.create_run(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_1",
        graph_name="polish",
        graph_version="v1",
        entrypoint_name="start",
        thread_id="thread_1",
        idempotency_key_hash="idem_1",
        input_refs_json=[{"resource_type": "resume", "resource_id": "res_1"}],
    )
    repeated = repository.create_run(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_1",
        graph_name="polish",
        graph_version="v1",
        entrypoint_name="start",
        thread_id="thread_1",
        idempotency_key_hash="idem_1",
        input_refs_json=[{"resource_type": "resume", "resource_id": "res_1"}],
    )

    assert created["id"].startswith("arun_")
    assert repeated["id"] == created["id"]
    assert repository.get_run_for_owner(OWNER_A, created["id"])["id"] == created["id"]
    assert repository.get_run_for_owner(OWNER_B, created["id"]) is None

    with pytest.raises(IdempotencyConflict):
        repository.create_run(
            owner_id=OWNER_A,
            actor_id="actor_a",
            ai_task_id="task_1",
            graph_name="polish",
            graph_version="v1",
            entrypoint_name="start",
            thread_id="thread_conflict",
            idempotency_key_hash="idem_1",
            input_refs_json=[{"resource_type": "resume", "resource_id": "res_changed"}],
        )


def test_agent_run_repository_updates_status_and_lists_timeline_newest_first() -> None:
    session_factory = _session_factory()
    repository = AgentRunRepository(session_factory)

    older = repository.create_run(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_old",
        graph_name="polish",
        graph_version="v1",
        entrypoint_name="start",
        thread_id="thread_old",
        idempotency_key_hash="idem_old",
    )
    newer = repository.create_run(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_new",
        graph_name="polish",
        graph_version="v1",
        entrypoint_name="start",
        thread_id="thread_new",
        idempotency_key_hash="idem_new",
    )

    running = repository.mark_running(OWNER_A, older["id"], base_record_version=older["record_version"])
    succeeded = repository.mark_succeeded(OWNER_A, running["id"], base_record_version=running["record_version"])

    assert succeeded["status"] == "succeeded"
    assert succeeded["record_version"] == older["record_version"] + 2
    assert [run["id"] for run in repository.list_timeline_runs(OWNER_A)] == [newer["id"], older["id"]]
    assert repository.list_timeline_runs(OWNER_B) == []


def test_checkpoint_repository_stores_refs_only_and_never_payload() -> None:
    session_factory = _session_factory()
    run_repository = AgentRunRepository(session_factory)
    checkpoint_repository = AgentCheckpointRefRepository(session_factory)
    run = run_repository.create_run(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_ckpt",
        graph_name="polish",
        graph_version="v1",
        entrypoint_name="start",
        thread_id="thread_ckpt",
        idempotency_key_hash="idem_ckpt",
    )

    ref = checkpoint_repository.record_checkpoint_ref(
        owner_id=OWNER_A,
        actor_id="actor_a",
        agent_run_id=run["id"],
        agent_node_run_id=None,
        graph_name="polish",
        node_name="question_planner",
        checkpoint_namespace="default",
        thread_id="thread_ckpt",
        checkpoint_id="checkpoint_1",
        checkpoint_metadata_json={"store_ref": "obj://checkpoint/1", "state_hash": "sha256:abc"},
    )

    assert ref["id"].startswith("ackpt_")
    assert ref["checkpoint_metadata_json"] == {"store_ref": "obj://checkpoint/1", "state_hash": "sha256:abc"}
    assert "checkpoint_payload" not in ref
    assert "payload" not in ref["checkpoint_metadata_json"]
    assert checkpoint_repository.get_latest_ref(OWNER_A, "default", "thread_ckpt")["id"] == ref["id"]
    assert checkpoint_repository.get_latest_ref(OWNER_B, "default", "thread_ckpt") is None


def test_agent_node_run_repository_tracks_node_timeline_and_side_effect_keys() -> None:
    session_factory = _session_factory()
    run = AgentRunRepository(session_factory).create_run(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_node",
        graph_name="polish",
        graph_version="v1",
        entrypoint_name="start",
        thread_id="thread_node",
        idempotency_key_hash="idem_node",
    )
    repository = AgentNodeRunRepository(session_factory)

    node_run = repository.start_node(
        owner_id=OWNER_A,
        actor_id="actor_a",
        agent_run_id=run["id"],
        graph_name="polish",
        node_name="question_planner",
        node_version="v1",
        attempt_number=1,
        input_digest="sha256:input",
    )
    with_llm_ref = repository.append_llm_call_ref(
        OWNER_A,
        node_run["id"],
        base_record_version=node_run["record_version"],
        llm_call_id="llmc_demo",
    )
    with_side_effect = repository.record_side_effect_key(
        OWNER_A,
        node_run["id"],
        base_record_version=with_llm_ref["record_version"],
        side_effect_key_hash="side_key_node",
        body_digest="sha256:body",
        ref_id="candidate_ref_1",
    )
    finished = repository.finish_node(
        OWNER_A,
        node_run["id"],
        base_record_version=with_side_effect["record_version"],
        output_digest="sha256:output",
        validation_summary_json={"status": "valid"},
    )

    assert finished["id"].startswith("anode_")
    assert finished["status"] == "succeeded"
    assert finished["llm_call_ids_json"] == ["llmc_demo"]
    assert finished["side_effect_keys_json"] == [
        {
            "side_effect_key_hash": "side_key_node",
            "body_digest": "sha256:body",
            "ref_id": "candidate_ref_1",
            "status": "recorded",
        }
    ]
    assert repository.list_by_run(OWNER_A, run["id"]) == [finished]
    assert repository.list_by_run(OWNER_B, run["id"]) == []

    repeated = repository.record_side_effect_key(
        OWNER_A,
        node_run["id"],
        base_record_version=finished["record_version"],
        side_effect_key_hash="side_key_node",
        body_digest="sha256:body",
        ref_id="candidate_ref_1",
    )
    assert repeated["side_effect_keys_json"] == finished["side_effect_keys_json"]


def _session_factory():
    factory = build_session_factory(DbSettings(database_url="sqlite+pysqlite:///:memory:"))
    initialize_schema(session_factory=factory)
    return factory
