from __future__ import annotations

import pytest

from app.infrastructure.db.repositories.ai_runtime import (
    AgentInterruptRepository,
    AgentRunRepository,
    IdempotencyConflict,
    RecordVersionConflict,
)
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema


OWNER_A = "owner_a"
OWNER_B = "owner_b"


def test_interrupt_repository_creates_and_resumes_once_with_owner_scope() -> None:
    session_factory = _session_factory()
    run = _create_run(session_factory)
    repository = AgentInterruptRepository(session_factory)

    interrupt = repository.create_interrupt(
        owner_id=OWNER_A,
        actor_id="actor_a",
        agent_run_id=run["id"],
        agent_node_run_id=None,
        node_name="human_review",
        interrupt_type="approval_required",
        resume_schema_id="resume-schema-v1",
        prompt_summary_json={"message": "确认候选内容"},
        idempotency_key_hash="interrupt_key_1",
    )

    assert interrupt["id"].startswith("aint_")
    assert repository.get_open_interrupt_for_owner(OWNER_A, interrupt["id"])["id"] == interrupt["id"]
    assert repository.get_open_interrupt_for_owner(OWNER_B, interrupt["id"]) is None

    resumed = repository.resume_interrupt_once(
        owner_id=OWNER_A,
        interrupt_id=interrupt["id"],
        base_record_version=interrupt["record_version"],
        idempotency_key_hash="resume_key_1",
        resume_payload_summary_json={"action": "approve", "target_ref": "candidate_1"},
    )
    repeated = repository.resume_interrupt_once(
        owner_id=OWNER_A,
        interrupt_id=interrupt["id"],
        base_record_version=resumed["record_version"],
        idempotency_key_hash="resume_key_1",
        resume_payload_summary_json={"action": "approve", "target_ref": "candidate_1"},
    )

    assert resumed["status"] == "resumed"
    assert repeated["id"] == interrupt["id"]
    assert repeated["resume_payload_summary_json"] == {"action": "approve", "target_ref": "candidate_1"}


def test_interrupt_repository_rejects_stale_version_and_conflicting_idempotency() -> None:
    session_factory = _session_factory()
    run = _create_run(session_factory)
    repository = AgentInterruptRepository(session_factory)
    interrupt = repository.create_interrupt(
        owner_id=OWNER_A,
        actor_id="actor_a",
        agent_run_id=run["id"],
        agent_node_run_id=None,
        node_name="human_review",
        interrupt_type="approval_required",
        resume_schema_id="resume-schema-v1",
        prompt_summary_json={"message": "确认候选内容"},
        idempotency_key_hash="interrupt_key_2",
    )

    with pytest.raises(RecordVersionConflict):
        repository.resume_interrupt_once(
            owner_id=OWNER_A,
            interrupt_id=interrupt["id"],
            base_record_version=interrupt["record_version"] + 1,
            idempotency_key_hash="resume_key_2",
            resume_payload_summary_json={"action": "approve"},
        )

    resumed = repository.resume_interrupt_once(
        owner_id=OWNER_A,
        interrupt_id=interrupt["id"],
        base_record_version=interrupt["record_version"],
        idempotency_key_hash="resume_key_2",
        resume_payload_summary_json={"action": "approve"},
    )
    with pytest.raises(IdempotencyConflict):
        repository.resume_interrupt_once(
            owner_id=OWNER_A,
            interrupt_id=resumed["id"],
            base_record_version=resumed["record_version"],
            idempotency_key_hash="resume_key_3",
            resume_payload_summary_json={"action": "reject"},
        )


def _create_run(session_factory):
    return AgentRunRepository(session_factory).create_run(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_interrupt",
        graph_name="polish",
        graph_version="v1",
        entrypoint_name="start",
        thread_id="thread_interrupt",
        idempotency_key_hash="idem_interrupt",
    )


def _session_factory():
    factory = build_session_factory(DbSettings(database_url="sqlite+pysqlite:///:memory:"))
    initialize_schema(session_factory=factory)
    return factory
