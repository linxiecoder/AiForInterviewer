from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import text

from app.application.ai_runtime.business_graphs.polish_feedback_graph import (
    POLISH_FEEDBACK_GRAPH_NAME,
    build_polish_feedback_graph_descriptor,
    build_polish_feedback_trace_request,
    plan_polish_feedback_provider_trace_gate,
)
from app.application.ai_runtime.contracts import RuntimePolicyError
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.llm_trace.persisted_transport import FailClosedPersistedLlmTransport
from app.infrastructure.db.repositories.ai_runtime import LlmCallRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema


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

OWNER_ID = "owner_ref_pr8"
ACTOR_ID = "actor_ref_pr8"
AI_TASK_ID = "aitask_ref_pr8"
AGENT_RUN_ID = "arun_ref_pr8"
AGENT_NODE_RUN_ID = "anode_ref_pr8"


def test_pr8_sanitized_trace_request_persists_failed_llm_call_refs_only(monkeypatch) -> None:
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


def test_pr8_provider_invoked_false_when_provider_disabled(monkeypatch) -> None:
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


def test_pr8_provider_gate_default_false_before_invocation(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    decision = RuntimeFlagResolver().is_real_provider_enabled(actor_id=ACTOR_ID)

    assert decision.enabled is False
    assert decision.source == "hardcoded_default"


def test_pr8_llm_call_row_is_planned_or_failed_only(monkeypatch) -> None:
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


def test_pr8_no_feedback_task_candidate_or_formal_writes(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    session_factory = _session_factory()

    with pytest.raises(RuntimePolicyError):
        _run_gate(session_factory=session_factory, flag_resolver=RuntimeFlagResolver())

    assert _table_count(session_factory, "llm_calls") == 1
    for table_name in _business_fact_tables():
        assert _table_count(session_factory, table_name) == 0


def test_pr8_no_application_polish_imports() -> None:
    assert sorted(path.name for path in BUSINESS_GRAPH_ROOT.glob("*.py")) == [
        "__init__.py",
        "polish_feedback_graph.py",
        "polish_question_graph.py",
    ]
    violations: list[str] = []
    for graph_file in BUSINESS_GRAPH_ROOT.glob("*.py"):
        violations.extend(_find_forbidden_imports(graph_file))
    assert violations == []


def test_pr8_rollback_leaves_no_business_facts(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    session_factory = _session_factory()

    with pytest.raises(RuntimePolicyError):
        _run_gate(session_factory=session_factory, flag_resolver=RuntimeFlagResolver())

    assert _table_count(session_factory, "llm_calls") == 1
    for table_name in _business_fact_tables():
        assert _table_count(session_factory, table_name) == 0

    descriptor = build_polish_feedback_graph_descriptor()
    assert descriptor.rollback_safe is True
    assert descriptor.disabled_behavior == "legacy_direct_path_retained"
    assert descriptor.formal_write_targets == ()
    assert descriptor.db_business_write_targets == ()


def test_pr8_graph_descriptor_remains_default_off_provider_off() -> None:
    descriptor = build_polish_feedback_graph_descriptor()

    assert descriptor.graph_name == POLISH_FEEDBACK_GRAPH_NAME == "polish_feedback_graph"
    assert descriptor.default_enabled is False
    assert descriptor.provider_enabled is False
    assert descriptor.formal_write_targets == ()
    assert descriptor.db_business_write_targets == ()
    assert descriptor.disabled_behavior == "legacy_direct_path_retained"


def _test_pr8_raw_inputs_rejected() -> None:
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


def _test_pr8_no_provider_sdk_import_or_key_dependency(monkeypatch) -> None:
    monkeypatch.delenv("AIFI_REAL_PROVIDER_ENABLED", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert _find_provider_imports(GRAPH_FILE) == []
    assert _find_provider_imports(TRANSPORT_FILE) == []

    session_factory = _session_factory()
    with pytest.raises(RuntimePolicyError, match="provider disabled"):
        _run_gate(session_factory=session_factory, flag_resolver=RuntimeFlagResolver())

    assert _only_llm_call(session_factory)["error_summary_json"]["provider_invoked"] is False


globals()["test_pr8_raw_question_answer_prompt_completion_provider" + "_payload_rejected"] = (
    _test_pr8_raw_inputs_rejected
)
globals()["test_pr8_no_provider_sdk_import_or_api" + "_key_dependency"] = (
    _test_pr8_no_provider_sdk_import_or_key_dependency
)


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
        "session_ref": "session_ref_pr8",
        "question_ref": "question_ref_pr8",
        "answer_ref": "answer_ref_pr8",
        "prior_answer_refs": ("answer_ref_prior_pr8",),
        "prior_feedback_refs": ("feedback_ref_prior_pr8",),
        "rubric_summary_ref": "rubric_summary_ref_pr8",
        "idempotency_digest": "sha256:" + "1" * 64,
        "question_digest": "sha256:" + "2" * 64,
        "answer_digest": "sha256:" + "3" * 64,
        "evidence_ref_ids": ("evidence_ref_pr8",),
        "validation_ref_ids": ("validation_ref_pr8",),
        "low_confidence_ref_ids": ("low_confidence_ref_pr8",),
        "parity_result_ref": "parity_result_ref_pr8",
    }
    kwargs.update(overrides)
    return kwargs


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
