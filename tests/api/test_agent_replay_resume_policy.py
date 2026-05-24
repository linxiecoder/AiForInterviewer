from __future__ import annotations

import pytest

from app.infrastructure.db.repositories.ai_runtime import (
    AgentRunRepository,
    AgentSideEffectRepository,
    LlmCallPayloadRepository,
    LlmCallRepository,
    RuntimePolicyError,
)
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema


OWNER_A = "owner_a"


def test_production_resume_reuses_existing_sanitized_llm_refs() -> None:
    session_factory = _session_factory()
    run = _create_run(session_factory)
    llm_repository = LlmCallRepository(session_factory)
    call = llm_repository.create_planned_call(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_replay",
        agent_run_id=run["id"],
        agent_node_run_id=None,
        graph_name="polish",
        node_name="question_planner",
        contract_ids_json=["P-POLISH-QUESTION-001"],
        configured_model="fake-model",
        provider_model="fake-provider-model",
        prompt_version="prompt-v1",
        schema_id="schema-v1",
        request_hash="sha256:req",
    )
    call = llm_repository.mark_succeeded(
        OWNER_A,
        call["id"],
        base_record_version=call["record_version"],
        response_hash="sha256:resp",
        evidence_hash="sha256:evidence",
        usage_json={"total_units": 1},
    )

    replayed = llm_repository.mark_replay_reused(
        OWNER_A,
        call["id"],
        base_record_version=call["record_version"],
        replay_reason="production_resume_existing_sanitized_ref",
    )

    assert replayed["status"] == "replay_reused"
    assert replayed["response_hash"] == "sha256:resp"
    assert "production_resume_existing_sanitized_ref" in replayed["fallback_reason"]


def test_debug_replay_is_inert_and_does_not_write_formal_objects() -> None:
    session_factory = _session_factory()
    run = _create_run(session_factory)
    side_effect_repository = AgentSideEffectRepository(session_factory)
    pending = side_effect_repository.record_pending_write(
        owner_id=OWNER_A,
        agent_run_id=run["id"],
        side_effect_key_hash="debug_replay_side_key",
        body_digest="sha256:debug-body",
        target_kind="feedback_candidate",
        target_ref_id="candidate_feedback_1",
    )

    assert pending["status"] == "pending"
    assert pending["formal_write"] is False
    assert pending["target_kind"] == "feedback_candidate"


def test_replay_raw_debug_capture_fails_closed_in_pr2() -> None:
    session_factory = _session_factory()
    run = _create_run(session_factory)
    call = LlmCallRepository(session_factory).create_planned_call(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_replay_raw",
        agent_run_id=run["id"],
        agent_node_run_id=None,
        graph_name="polish",
        node_name="question_planner",
        contract_ids_json=["P-POLISH-QUESTION-001"],
        configured_model="fake-model",
        provider_model="fake-provider-model",
        prompt_version="prompt-v1",
        schema_id="schema-v1",
        request_hash="sha256:req-raw",
    )

    with pytest.raises(RuntimePolicyError, match="PR2"):
        LlmCallPayloadRepository(session_factory).capture_debug_raw_ref(
            owner_id=OWNER_A,
            actor_id="actor_a",
            llm_call_id=call["id"],
            payload_kind="debug_raw",
            raw_payload_ciphertext_ref="object://debug/raw",
            encryption_key_ref="kms://debug",
        )


def _create_run(session_factory):
    return AgentRunRepository(session_factory).create_run(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_replay_run",
        graph_name="polish",
        graph_version="v1",
        entrypoint_name="start",
        thread_id="thread_replay",
        idempotency_key_hash="idem_replay",
    )


def _session_factory():
    factory = build_session_factory(DbSettings(database_url="sqlite+pysqlite:///:memory:"))
    initialize_schema(session_factory=factory)
    return factory
