from __future__ import annotations

import pytest

from app.infrastructure.db.repositories.ai_runtime import (
    AgentRunRepository,
    LlmCallPayloadRepository,
    LlmCallRepository,
    RuntimePolicyError,
)
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema


OWNER_A = "owner_a"


def test_payload_capture_defaults_raw_off_and_redacts_forbidden_markers() -> None:
    session_factory = _session_factory()
    llm_call = _create_llm_call(session_factory)
    repository = LlmCallPayloadRepository(session_factory)

    payload = repository.capture_sanitized_summary(
        owner_id=OWNER_A,
        actor_id="actor_a",
        llm_call_id=llm_call["id"],
        payload_kind="request_response_summary",
        payload_summary_json={
            "safe_summary": "生成了结构化候选摘要",
            "raw_prompt": "full_resume must not persist",
            "nested": {
                "completion": "raw_completion must not persist",
                "provider_payload": {"api_key": "sk-test-secret"},
            },
            "markers": ["token=raw-token", "cookie=session-secret", "secret=plain-secret"],
        },
        payload_hash="sha256:payload",
    )

    assert payload["id"].startswith("llmp_")
    assert payload["sanitized"] is True
    assert payload["raw_enabled"] is False
    assert payload["raw_payload_ciphertext_ref"] is None
    assert payload["encryption_key_ref"] is None
    serialized = repr(payload)
    for forbidden in (
        "raw_prompt",
        "raw_completion",
        "provider_payload",
        "api_key",
        "token=raw-token",
        "cookie=session-secret",
        "secret=plain-secret",
        "full_resume",
    ):
        assert forbidden not in serialized
    assert "redacted_sensitive_detail" in serialized


def test_debug_raw_ref_capture_fails_closed_in_pr2() -> None:
    session_factory = _session_factory()
    llm_call = _create_llm_call(session_factory)
    repository = LlmCallPayloadRepository(session_factory)

    with pytest.raises(RuntimePolicyError, match="PR2"):
        repository.capture_debug_raw_ref(
            owner_id=OWNER_A,
            actor_id="actor_a",
            llm_call_id=llm_call["id"],
            payload_kind="debug_raw",
            raw_payload_ciphertext_ref="object://raw/debug",
            encryption_key_ref="kms://key",
        )


def _create_llm_call(session_factory):
    run = AgentRunRepository(session_factory).create_run(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_payload_run",
        graph_name="polish",
        graph_version="v1",
        entrypoint_name="start",
        thread_id="thread_payload",
        idempotency_key_hash="idem_payload",
    )
    return LlmCallRepository(session_factory).create_planned_call(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_payload",
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


def _session_factory():
    factory = build_session_factory(DbSettings(database_url="sqlite+pysqlite:///:memory:"))
    initialize_schema(session_factory=factory)
    return factory
