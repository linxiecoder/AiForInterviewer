from __future__ import annotations

import pytest

from app.application.ai_runtime.contracts import AgentCommandEnvelope, AgentRunContext, RuntimePolicyError
from app.application.ai_runtime.llm_trace import LlmTraceContext
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.application.llm.types import LlmTransportRequest
from app.infrastructure.ai_runtime.langgraph.in_memory_runtime import InMemoryLangGraphRuntime
from app.infrastructure.ai_runtime.llm_trace.persisted_transport import FailClosedPersistedLlmTransport
from app.infrastructure.db.repositories.ai_runtime import LlmCallRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema


def test_pr4_provider_gate_defaults_false_and_in_memory_runtime_does_not_bypass_it(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    resolver = RuntimeFlagResolver(
        test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True}
    )
    runtime = InMemoryLangGraphRuntime(flag_resolver=resolver)
    context = _context()

    result = runtime.start(context, context.command)

    assert resolver.is_real_provider_enabled(actor_id=context.actor_id).enabled is False
    assert result.metadata["provider_gate_enabled"] is False
    assert result.metadata["provider_calls"] == 0


def test_pr4_persisted_transport_fails_closed_before_provider_invocation(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    session_factory = _session_factory()
    transport = FailClosedPersistedLlmTransport(
        session_factory=session_factory,
        flag_resolver=RuntimeFlagResolver(),
    )
    trace_context = LlmTraceContext(
        owner_id="owner_1",
        ai_task_id="aitask_1",
        agent_run_id="arun_1",
        agent_node_run_id="anode_1",
        contract_ids=("P-PR4-FAKE-001",),
        replay_mode="production_resume",
    )
    request = LlmTransportRequest(
        contract_ids=("P-PR4-FAKE-001",),
        task_type="pr4_fake_runtime",
        input_refs=("input_ref_1",),
        evidence_bundle={"summary_ref": "evidence_ref_1"},
    )

    with pytest.raises(RuntimePolicyError, match="provider disabled"):
        transport.generate(request, trace_context)

    calls = LlmCallRepository(session_factory).list_by_run("owner_1", "arun_1")
    assert len(calls) == 1
    assert calls[0]["status"] == "failed"
    assert calls[0]["fallback_reason"] == "provider_disabled_fail_closed"
    serialized = repr(calls[0])
    for forbidden in ("raw_prompt", "raw_completion", "provider_payload", "api_key"):
        assert forbidden not in serialized


def _context() -> AgentRunContext:
    command = AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("runtime_input_ref_1",),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_pr4",
    )
    return AgentRunContext(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_pr4_fake",
        ai_task_id="aitask_pr4_fake",
        graph_name="pr4_fake_runtime",
        graph_version="pr4",
        command=command,
    )


def _session_factory():
    factory = build_session_factory(DbSettings(database_url="sqlite+pysqlite:///:memory:"))
    initialize_schema(session_factory=factory)
    return factory
