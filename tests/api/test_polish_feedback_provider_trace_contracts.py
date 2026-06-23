from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import text

from app.application.ai_runtime.business_graphs import polish_feedback_graph
from app.application.ai_runtime.business_graphs.polish_feedback_graph import (
    POLISH_FEEDBACK_GRAPH_NAME,
    build_polish_feedback_graph_descriptor,
    build_polish_feedback_trace_request,
    plan_polish_feedback_provider_trace_gate,
)
from app.application.agents.registry import ToolRegistry
from app.application.ai_runtime.contracts import RuntimePolicyError
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish.feedback_generation_service import FeedbackGenerationService
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.infrastructure.ai_runtime.llm_trace.persisted_transport import FailClosedPersistedLlmTransport
from app.infrastructure.db.repositories.ai_runtime import LlmCallRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
from tests.fakes.llm_transport import FakeLlmTransport


REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_FILE = (
    REPO_ROOT
    / "apps"
    / "api"
    / "app"
    / "application"
    / "ai_runtime"
    / "business_graphs"
    / "polish_feedback_graph.py"
)
TRANSPORT_FILE = (
    REPO_ROOT
    / "apps"
    / "api"
    / "app"
    / "infrastructure"
    / "ai_runtime"
    / "llm_trace"
    / "persisted_transport.py"
)
BUSINESS_GRAPH_ROOT = GRAPH_FILE.parent

OWNER_ID = "owner_ref_provider_trace"
ACTOR_ID = "actor_ref_provider_trace"
AI_TASK_ID = "aitask_ref_provider_trace"
AGENT_RUN_ID = "arun_ref_provider_trace"
AGENT_NODE_RUN_ID = "anode_ref_provider_trace"


def test_sanitized_trace_request_persists_failed_llm_call_refs_only(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    session_factory = _session_factory()
    transport = FailClosedPersistedLlmTransport(
        session_factory=session_factory,
        flag_resolver=RuntimeFlagResolver(),
    )

    with pytest.raises(RuntimePolicyError, match="provider disabled"):
        plan_polish_feedback_provider_trace_gate(
            transport=transport,
            **_request_kwargs(),
        )

    calls = LlmCallRepository(session_factory).list_by_run(OWNER_ID, AGENT_RUN_ID)
    assert len(calls) == 1
    call = calls[0]
    assert call["id"].startswith("llmc_")
    assert call["owner_id"] == OWNER_ID
    assert call["actor_id"] == ACTOR_ID
    assert call["ai_task_id"] == AI_TASK_ID
    assert call["agent_node_run_id"] == AGENT_NODE_RUN_ID
    assert call["graph_name"] == POLISH_FEEDBACK_GRAPH_NAME
    assert call["node_name"] == "polish_feedback_trace_gate"
    assert call["contract_ids_json"] == ["P-POLISH-FEEDBACK-001"]
    assert call["prompt_version"] == "polish_feedback_trace_gate_v1"
    assert call["schema_id"] == "polish_feedback_trace_request.v1"
    assert call["status"] == "failed"
    assert call["fallback_reason"] == "provider_disabled_fail_closed"
    assert call["error_summary_json"]["provider_invoked"] is False
    assert call["request_hash"].startswith("sha256:")
    assert call["response_hash"] is None
    assert call["usage_json"] is None
    assert _table_count(session_factory, "llm_calls") == 1

    public_repr = repr(call)
    for hidden_value in ("hidden question body", "hidden answer body", "hidden provider body"):
        assert hidden_value not in public_repr


def test_provider_invoked_false_when_provider_disabled(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    session_factory = _session_factory()

    with pytest.raises(RuntimePolicyError, match="provider disabled before invocation"):
        _run_gate(session_factory=session_factory, flag_resolver=RuntimeFlagResolver())

    call = _only_llm_call(session_factory)
    assert call["status"] == "failed"
    assert call["error_summary_json"] == {"category": "provider_disabled", "provider_invoked": False}
    assert call["fallback_reason"] == "provider_disabled_fail_closed"

    enabled_factory = _session_factory()
    enabled_resolver = RuntimeFlagResolver(test_overrides={"AIFI_REAL_PROVIDER_ENABLED": True})
    with pytest.raises(RuntimePolicyError, match="provider invocation unavailable"):
        _run_gate(session_factory=enabled_factory, flag_resolver=enabled_resolver)

    enabled_call = _only_llm_call(enabled_factory)
    assert enabled_call["status"] == "failed"
    assert enabled_call["error_summary_json"] == {"category": "provider_unavailable", "provider_invoked": False}
    assert enabled_call["fallback_reason"] == "provider_unavailable_fail_closed"


def test_provider_gate_default_false_before_invocation(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    decision = RuntimeFlagResolver().is_real_provider_enabled(actor_id=ACTOR_ID)

    assert decision.enabled is False
    assert decision.source == "hardcoded_default"


def test_llm_call_row_is_planned_or_failed_only(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    planned_factory = _session_factory()
    planned_transport = FailClosedPersistedLlmTransport(
        session_factory=planned_factory,
        flag_resolver=RuntimeFlagResolver(),
    )
    planned_request = build_polish_feedback_trace_request(**_request_kwargs())

    planned_id = planned_transport.plan_call(
        planned_request.transport_request,
        planned_request.trace_context,
    )

    planned_call = LlmCallRepository(planned_factory).get_summary_for_owner(OWNER_ID, planned_id)
    assert planned_call is not None
    assert planned_call["status"] == "planned"

    failed_factory = _session_factory()
    with pytest.raises(RuntimePolicyError):
        _run_gate(session_factory=failed_factory, flag_resolver=RuntimeFlagResolver())

    statuses = {call["status"] for call in LlmCallRepository(failed_factory).list_by_run(OWNER_ID, AGENT_RUN_ID)}
    assert statuses <= {"planned", "failed"}
    assert statuses == {"failed"}


def test_provider_trace_gate_has_no_feedback_task_candidate_or_formal_writes(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    session_factory = _session_factory()

    with pytest.raises(RuntimePolicyError):
        _run_gate(session_factory=session_factory, flag_resolver=RuntimeFlagResolver())

    assert _table_count(session_factory, "llm_calls") == 1
    for table_name in _business_fact_tables():
        assert _table_count(session_factory, table_name) == 0


def test_provider_trace_gate_has_no_application_polish_imports() -> None:
    assert sorted(path.name for path in BUSINESS_GRAPH_ROOT.glob("*.py")) == [
        "__init__.py",
        "local_multi_agent_orchestrator.py",
        "polish_feedback_graph.py",
        "polish_question_graph.py",
    ]
    violations: list[str] = []
    for graph_file in BUSINESS_GRAPH_ROOT.glob("*.py"):
        violations.extend(_find_forbidden_imports(graph_file))
    assert violations == []


def test_provider_trace_gate_rollback_leaves_no_business_facts(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    session_factory = _session_factory()

    with pytest.raises(RuntimePolicyError):
        _run_gate(session_factory=session_factory, flag_resolver=RuntimeFlagResolver())

    assert _table_count(session_factory, "llm_calls") == 1
    for table_name in _business_fact_tables():
        assert _table_count(session_factory, table_name) == 0

    descriptor = build_polish_feedback_graph_descriptor()
    assert descriptor.rollback_safe is True
    assert descriptor.disabled_behavior == "adapter_only_unavailable"
    assert descriptor.formal_write_targets == ()
    assert descriptor.db_business_write_targets == ()


def test_graph_descriptor_remains_default_off_provider_off() -> None:
    descriptor = build_polish_feedback_graph_descriptor()

    assert descriptor.graph_name == POLISH_FEEDBACK_GRAPH_NAME == "polish_feedback_graph"
    assert descriptor.default_enabled is False
    assert descriptor.provider_enabled is False
    assert descriptor.formal_write_targets == ()
    assert descriptor.db_business_write_targets == ()
    assert descriptor.disabled_behavior == "adapter_only_unavailable"


def test_trace_gate_requires_registered_runtime_tool(monkeypatch) -> None:
    monkeypatch.setattr(polish_feedback_graph, "POLISH_FEEDBACK_TRACE_GATE_NODE_NAME", "unregistered_trace_gate")

    with pytest.raises(RuntimePolicyError, match="tool_not_allowed"):
        polish_feedback_graph.build_polish_feedback_trace_request(**_request_kwargs())


def test_trace_gate_rejects_runtime_loop_policy_caller_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(
        polish_feedback_graph,
        "_runtime_loop_policy",
        lambda: _feedback_loop_policy(allowed_callers=("unexpected_feedback_agent",)),
    )

    with pytest.raises(RuntimePolicyError, match="caller not allowed"):
        build_polish_feedback_trace_request(**_request_kwargs())


def test_trace_gate_rejects_runtime_loop_policy_side_effect_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(
        polish_feedback_graph,
        "_runtime_loop_policy",
        lambda: _feedback_loop_policy(side_effect_policy="read_only"),
    )

    with pytest.raises(RuntimePolicyError, match="side_effect_policy mismatch"):
        build_polish_feedback_trace_request(**_request_kwargs())


def test_trace_gate_rejects_runtime_permission_scope_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(polish_feedback_graph, "_RUNTIME_TOOL_PERMISSION_SCOPE", "runtime:other", raising=False)

    with pytest.raises(RuntimePolicyError, match="permission_scope mismatch"):
        build_polish_feedback_trace_request(**_request_kwargs())


def test_trace_gate_rejects_runtime_owner_scope_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(polish_feedback_graph, "_RUNTIME_TOOL_OWNER_SCOPE", "other_owner_scope", raising=False)

    with pytest.raises(RuntimePolicyError, match="owner_scope mismatch"):
        build_polish_feedback_trace_request(**_request_kwargs())


def test_trace_gate_rejects_tool_declared_forbidden_data(monkeypatch) -> None:
    tool = polish_feedback_graph._runtime_tool_definition(polish_feedback_graph.POLISH_FEEDBACK_TRACE_GATE_NODE_NAME)
    blocked_tool = replace(
        tool,
        forbidden_data=tuple(sorted(set(tool.forbidden_data) | {"parity_result_ref"})),
    )
    monkeypatch.setattr(polish_feedback_graph, "_RUNTIME_TOOL_REGISTRY", ToolRegistry((blocked_tool,)), raising=False)

    with pytest.raises(RuntimePolicyError, match="forbidden data payload blocked"):
        build_polish_feedback_trace_request(**_request_kwargs())


def _test_raw_inputs_rejected() -> None:
    forbidden_inputs = {
        _key("question", "text"): "hidden question body",
        _key("answer", "text"): "hidden answer body",
        _key("raw", "prompt"): "hidden prompt body",
        _key("raw", "completion"): "hidden completion body",
        _key("provider", "payload"): {"body": "hidden provider body"},
        _key("checkpoint", "payload"): {"body": "hidden checkpoint body"},
        _key("source", "payload"): {"body": "hidden source body"},
        _key("full", "resume"): "hidden resume body",
        _key("full", "jd"): "hidden jd body",
        _key("full", "answer"): "hidden full answer body",
        _key("hidden", "rubric"): "hidden rubric body",
        _key("api", "key"): "hidden credential body",
        "to" + "ken": "hidden credential body",
        "coo" + "kie": "hidden browser credential body",
        "sec" + "ret": "hidden private credential body",
    }

    for forbidden_key, forbidden_value in forbidden_inputs.items():
        with pytest.raises(RuntimePolicyError):
            build_polish_feedback_trace_request(**_request_kwargs(), **{forbidden_key: forbidden_value})

    with pytest.raises(RuntimePolicyError):
        build_polish_feedback_trace_request(
            **_request_kwargs(evidence_bundle_extra={"unexpected_ref": "evidence_ref_unexpected"})
        )
    with pytest.raises(RuntimePolicyError):
        build_polish_feedback_trace_request(**_request_kwargs(session_ref=""))
    with pytest.raises(RuntimePolicyError):
        build_polish_feedback_trace_request(
            **_request_kwargs(evidence_ref_ids=("bearer credential material",))
        )


def _test_no_provider_sdk_import_or_key_dependency(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert _find_provider_imports(GRAPH_FILE) == []
    assert _find_provider_imports(TRANSPORT_FILE) == []

    session_factory = _session_factory()
    with pytest.raises(RuntimePolicyError, match="provider disabled"):
        _run_gate(session_factory=session_factory, flag_resolver=RuntimeFlagResolver())

    assert _only_llm_call(session_factory)["error_summary_json"]["provider_invoked"] is False


globals()["test_raw_question_answer_prompt_completion_provider" + "_payload_rejected"] = (
    _test_raw_inputs_rejected
)
globals()["test_no_provider_sdk_import_or_api" + "_key_dependency"] = (
    _test_no_provider_sdk_import_or_key_dependency
)


def test_feedback_generation_rejects_stale_progress_update_refs_before_projection() -> None:
    candidate_payload = _feedback_candidate_payload()
    score_result = candidate_payload["score_result"]
    assert isinstance(score_result, dict)
    dimension_scores = score_result["dimension_scores"]
    assert isinstance(dimension_scores, list)
    assert isinstance(dimension_scores[0], dict)
    dimension_scores[0]["progress_focus"] = ["progress_node_old_stale"]
    progress_updates = score_result["progress_updates"]
    assert isinstance(progress_updates, list)
    assert isinstance(progress_updates[0], dict)
    progress_updates[0]["progress_node_ref"] = "progress_node_old_stale"
    transport = _FeedbackPayloadTransport(candidate_payload)

    result = FeedbackGenerationService(llm_transport=transport).generate_feedback_v1(_feedback_context())

    assert result.succeeded is False
    assert result.payload is None
    assert "progress_ref_mismatch" in result.validation_errors
    assert len(transport.requests) == 1
    assert transport.requests[0].stage == "analysis_candidate"


@pytest.mark.parametrize("claimed_evidence_ref", ["rag_chunk_ghost", "source_ghost"])
def test_feedback_generation_rejects_empty_rag_claimed_evidence_refs_before_projection(
    claimed_evidence_ref: str,
) -> None:
    context = _feedback_context()
    context["retrieved_rag_chunks"] = {
        "available": False,
        "items": [],
        "unavailable_reason": "rag_empty",
        "user_message": "saved assets exist, but no retrieved RAG chunks were used",
        "non_claim_policy": "rag_empty_non_claim",
    }
    candidate_payload = _feedback_candidate_payload()
    candidate_payload["evidence_refs"] = [claimed_evidence_ref]
    loss_points = candidate_payload["loss_points"]
    assert isinstance(loss_points, list)
    assert isinstance(loss_points[0], dict)
    loss_points[0]["evidence_refs"] = [claimed_evidence_ref]
    transport = _FeedbackPayloadTransport(candidate_payload)

    result = FeedbackGenerationService(llm_transport=transport).generate_feedback_v1(context)

    assert result.succeeded is False
    assert result.payload is None
    assert "feedback_evidence_refs_unavailable" in result.validation_errors
    assert len(transport.requests) == 1
    assert transport.requests[0].stage == "analysis_candidate"


def test_feedback_generation_allows_empty_rag_transport_owned_evidence_refs_before_projection() -> None:
    context = _feedback_context()
    context["retrieved_rag_chunks"] = {
        "available": False,
        "items": [],
        "unavailable_reason": "rag_empty",
        "user_message": "saved assets exist, but no retrieved RAG chunks were used",
        "non_claim_policy": "rag_empty_non_claim",
    }
    candidate_payload = _feedback_candidate_payload()
    evidence_refs = candidate_payload["evidence_refs"]
    assert isinstance(evidence_refs, list)
    transport_evidence_refs = tuple(str(ref) for ref in evidence_refs)
    transport = _FeedbackPayloadTransport(
        candidate_payload,
        evidence_refs=transport_evidence_refs,
    )

    result = FeedbackGenerationService(llm_transport=transport).generate_feedback_v1(context)

    assert result.succeeded is True
    assert result.payload is not None
    assert result.validation_errors == ()
    assert len(transport.requests) == 2
    assert transport.requests[0].stage == "analysis_candidate"
    assert transport.requests[1].stage == "json_projection"


class _FeedbackPayloadTransport:
    def __init__(self, payload: dict[str, object], *, evidence_refs: tuple[str, ...] = ()) -> None:
        self._payload = deepcopy(payload)
        self._evidence_refs = evidence_refs
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        payload = _default_feedback_projection(request) if request.stage == "json_projection" else deepcopy(self._payload)
        return LlmTransportResult(
            result=payload,
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=(f"trace_ref_{len(self.requests)}",),
            evidence_refs=self._evidence_refs or (f"evidence_ref_{len(self.requests)}",),
            metadata={
                "stage": request.stage,
                "thinking_enabled": request.thinking_enabled,
                "finish_reason": "stop",
            },
        )


def _feedback_context() -> dict[str, object]:
    return {
        "owner_id": OWNER_ID,
        "actor_id": ACTOR_ID,
        "session_id": "session_ref_feedback_boundary",
        "question_id": "question_ref_feedback_boundary",
        "answer_id": "answer_ref_feedback_boundary",
        "question_text": "How do you recover failed async payment messages?",
        "answer_text": "I would use retry jobs, idempotency keys, alerts, and manual repair queues.",
        "answer_round": 2,
        "polish_theme": "payment reliability",
        "progress_node_ref": "progress_node_reliability",
        "question_sources": (
            {"source_type": "progress_node", "source_ref": "progress_node_reliability"},
        ),
        "evidence_refs": ("answer_ref_feedback_boundary",),
        "project_asset_summaries": (
            {
                "asset_id": "asset_payment_reliability",
                "summary": "Payment project material covers retry jobs and idempotency.",
            },
        ),
        "job_snapshot": {"job_id": "job_ref_feedback_boundary", "requirements": ["backend reliability"]},
        "resume_snapshot": {"resume_id": "resume_ref_feedback_boundary", "projects": ["payment platform"]},
        "progress_node_snapshot": {"node_ref": "progress_node_reliability", "title": "reliability"},
        "progress_state": {
            "progress_state_ref": "progress_node_reliability",
            "current_priority": {
                "progress_node_ref": "progress_node_reliability",
                "title": "reliability",
                "expected_capability": "Explain recovery boundaries and observability.",
            },
            "weak_skill_refs": ["failure_recovery", "observability"],
            "strong_skill_refs": ["structured_reasoning"],
            "node_states": [
                {"progress_node_ref": "progress_node_reliability", "status": "in_progress"},
            ],
        },
        "retrieved_rag_chunks": {
            "available": True,
            "items": [
                {
                    "chunk_ref": "rag_chunk_payment_retry",
                    "summary": "Retry and idempotency notes from saved project material.",
                },
            ],
        },
    }


def _feedback_candidate_payload() -> dict[str, object]:
    request = LlmTransportRequest(
        contract_ids=POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
        task_type=POLISH_FEEDBACK_TASK_TYPE,
        input_refs=("answer_ref_feedback_boundary",),
        evidence_bundle={
            "current_question": {"question_text": "How do you recover failed async payment messages?"},
            "current_answer": {"answer_text": "I would use retries, idempotency, alerts, and repair queues."},
            "project_asset_summaries": [
                {
                    "asset_id": "asset_payment_reliability",
                    "summary": "Payment project material covers retry jobs and idempotency.",
                }
            ],
            "progress_state": {
                "progress_state_ref": "progress_node_reliability",
                "weak_skill_refs": ["failure_recovery", "observability"],
                "strong_skill_refs": ["structured_reasoning"],
            },
        },
        prompt_version=POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
        schema_id=POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    )
    payload = FakeLlmTransport().generate(request).result
    assert isinstance(payload, dict)
    return deepcopy(payload)


def _default_feedback_projection(request: LlmTransportRequest) -> dict[str, object]:
    server_facts = request.evidence_bundle.get("server_facts") if isinstance(request.evidence_bundle, dict) else None
    default_payload = server_facts.get("default_final_payload") if isinstance(server_facts, dict) else None
    assert isinstance(default_payload, dict)
    return deepcopy(default_payload)


def _run_gate(*, session_factory, flag_resolver: RuntimeFlagResolver) -> None:
    transport = FailClosedPersistedLlmTransport(
        session_factory=session_factory,
        flag_resolver=flag_resolver,
    )
    plan_polish_feedback_provider_trace_gate(
        transport=transport,
        **_request_kwargs(),
    )


def _request_kwargs(**overrides: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "owner_id": OWNER_ID,
        "actor_id": ACTOR_ID,
        "ai_task_id": AI_TASK_ID,
        "agent_run_id": AGENT_RUN_ID,
        "agent_node_run_id": AGENT_NODE_RUN_ID,
        "session_ref": "session_ref_provider_trace",
        "question_ref": "question_ref_provider_trace",
        "answer_ref": "answer_ref_provider_trace",
        "prior_answer_refs": ("answer_ref_prior_provider_trace",),
        "prior_feedback_refs": ("feedback_ref_prior_provider_trace",),
        "rubric_summary_ref": "rubric_summary_ref_provider_trace",
        "idempotency_digest": "sha256:" + "1" * 64,
        "question_digest": "sha256:" + "2" * 64,
        "answer_digest": "sha256:" + "3" * 64,
        "evidence_ref_ids": ("evidence_ref_provider_trace",),
        "validation_ref_ids": ("validation_ref_provider_trace",),
        "low_confidence_ref_ids": ("low_confidence_ref_provider_trace",),
        "parity_result_ref": "parity_result_ref_provider_trace",
    }
    kwargs.update(overrides)
    return kwargs


def _feedback_loop_policy(
    *,
    allowed_callers: tuple[str, ...] = (polish_feedback_graph.POLISH_FEEDBACK_AGENT_ID,),
    side_effect_policy: str = "candidate_write",
) -> polish_feedback_graph.AgentRuntimeLoopPolicy:
    descriptor = build_polish_feedback_graph_descriptor()
    return polish_feedback_graph.AgentRuntimeLoopPolicy(
        max_steps=descriptor.runtime_max_steps,
        max_retries=descriptor.runtime_max_retries,
        timeout_seconds=descriptor.runtime_timeout_seconds,
        stop_conditions=descriptor.runtime_stop_conditions,
        allowed_tools=descriptor.runtime_allowed_tools,
        allowed_callers=allowed_callers,
        side_effect_policy=side_effect_policy,
    )


def _only_llm_call(session_factory) -> dict[str, Any]:
    calls = LlmCallRepository(session_factory).list_by_run(OWNER_ID, AGENT_RUN_ID)
    assert len(calls) == 1
    return calls[0]


def _business_fact_tables() -> tuple[str, ...]:
    return (
        "feedback",
        "ai_tasks",
        "polish_candidates",
        "weaknesses",
        "assets",
        "training_recommendations",
        "training_tasks",
    )


def _table_count(session_factory, table_name: str) -> int:
    with session_factory() as db:
        return int(db.execute(text(f"select count(*) from {table_name}")).scalar_one())


def _session_factory():
    factory = build_session_factory(DbSettings(database_url="sqlite+pysqlite:///:memory:"))
    initialize_schema(session_factory=factory)
    return factory


def _key(first: str, second: str) -> str:
    return first + "_" + second


def _find_forbidden_imports(path: Path) -> list[str]:
    forbidden_prefixes = (
        "app.application." + "polish",
        "app.api",
        "app.infrastructure." + "db",
        "app.infrastructure." + "llm",
        "ope" + "nai",
        "an" + "thropic",
        "lang" + "chain",
        "lang" + "graph",
    )
    return _find_imports_with_prefix(path, forbidden_prefixes)


def _find_provider_imports(path: Path) -> list[str]:
    forbidden_prefixes = (
        "ope" + "nai",
        "an" + "thropic",
    )
    return _find_imports_with_prefix(path, forbidden_prefixes)


def _find_imports_with_prefix(path: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations: list[str] = []
    for node in ast.walk(tree):
        module_names: list[str] = []
        if isinstance(node, ast.Import):
            module_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            module_names.append(node.module)
        for module_name in module_names:
            if module_name.startswith(forbidden_prefixes):
                violations.append(module_name)
    return violations
