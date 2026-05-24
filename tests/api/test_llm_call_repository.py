from __future__ import annotations

from app.infrastructure.db.repositories.ai_runtime import AgentRunRepository, LlmCallRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema


OWNER_A = "owner_a"
OWNER_B = "owner_b"


def test_llm_call_repository_tracks_lifecycle_and_owner_scoped_summary() -> None:
    session_factory = _session_factory()
    run = _create_run(session_factory)
    repository = LlmCallRepository(session_factory)

    planned = repository.create_planned_call(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_llm",
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
    running = repository.mark_running(OWNER_A, planned["id"], base_record_version=planned["record_version"])
    succeeded = repository.mark_succeeded(
        OWNER_A,
        running["id"],
        base_record_version=running["record_version"],
        response_hash="sha256:resp",
        evidence_hash="sha256:evidence",
        usage_json={"total_units": 42},
        low_confidence_flags_json=["source_unavailable"],
    )
    failed = repository.create_planned_call(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_llm_failed",
        agent_run_id=run["id"],
        agent_node_run_id=None,
        graph_name="polish",
        node_name="feedback",
        contract_ids_json=["P-POLISH-FEEDBACK-001"],
        configured_model="fake-model",
        provider_model="fake-provider-model",
        prompt_version="prompt-v1",
        schema_id="schema-v1",
        request_hash="sha256:req-failed",
    )
    failed = repository.mark_failed(
        OWNER_A,
        failed["id"],
        base_record_version=failed["record_version"],
        error_summary_json={"category": "provider_unavailable", "detail": "timeout"},
        fallback_reason="fake_transport_only",
    )

    summary = repository.get_summary_for_owner(OWNER_A, succeeded["id"])
    assert planned["id"].startswith("llmc_")
    assert succeeded["status"] == "succeeded"
    assert failed["status"] == "failed"
    assert summary["id"] == succeeded["id"]
    assert summary["request_hash"] == "sha256:req"
    assert summary["response_hash"] == "sha256:resp"
    assert summary["usage_json"] == {"total_units": 42}
    assert repository.get_summary_for_owner(OWNER_B, succeeded["id"]) is None
    assert [item["id"] for item in repository.list_by_run(OWNER_A, run["id"])] == [planned["id"], failed["id"]]


def test_llm_call_summary_never_returns_raw_prompt_completion_or_provider_payload() -> None:
    session_factory = _session_factory()
    run = _create_run(session_factory)
    repository = LlmCallRepository(session_factory)
    planned = repository.create_planned_call(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_llm_sensitive",
        agent_run_id=run["id"],
        agent_node_run_id=None,
        graph_name="polish",
        node_name="question_planner",
        contract_ids_json=["P-POLISH-QUESTION-001"],
        configured_model="fake-model",
        provider_model="fake-provider-model",
        prompt_version="prompt-v1",
        schema_id="schema-v1",
        request_hash="sha256:req-sensitive",
        validation_errors_json=[{"raw_prompt": "should not persist"}],
    )
    succeeded = repository.mark_succeeded(
        OWNER_A,
        planned["id"],
        base_record_version=planned["record_version"],
        response_hash="sha256:resp-sensitive",
        evidence_hash="sha256:evidence-sensitive",
        usage_json={"provider_payload": {"secret": "should not persist"}},
        low_confidence_flags_json=["raw_completion should not persist"],
    )

    serialized = repr(repository.get_summary_for_owner(OWNER_A, succeeded["id"]))
    for forbidden in ("raw_prompt", "raw_completion", "provider_payload", "should not persist"):
        assert forbidden not in serialized
    assert "redacted_sensitive_detail" in serialized


def _create_run(session_factory):
    return AgentRunRepository(session_factory).create_run(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_llm_run",
        graph_name="polish",
        graph_version="v1",
        entrypoint_name="start",
        thread_id="thread_llm",
        idempotency_key_hash="idem_llm",
    )


def _session_factory():
    factory = build_session_factory(DbSettings(database_url="sqlite+pysqlite:///:memory:"))
    initialize_schema(session_factory=factory)
    return factory
