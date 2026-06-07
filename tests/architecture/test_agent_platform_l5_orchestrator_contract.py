from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass, replace
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_ROOT = REPO_ROOT / "apps/api/app/application/agents"
FORBIDDEN_WIRING_ROOTS = (
    REPO_ROOT / "apps/api/app/application/agents/runtime",
    REPO_ROOT / "apps/api/app/application/agents/handoff",
    REPO_ROOT / "apps/api/app/application/ai_runtime",
    REPO_ROOT / "apps/api/app/application/polish",
    REPO_ROOT / "apps/api/app/api",
    REPO_ROOT / "apps/api/app/domain",
    REPO_ROOT / "apps/api/app/infrastructure",
)
ALLOWED_DEFAULT_OFF_LOCAL_RUNTIME_WIRING = frozenset(
    {
        "apps/api/app/application/ai_runtime/business_graphs/local_multi_agent_orchestrator.py",
        "apps/api/app/application/ai_runtime/facade.py",
        "apps/api/app/application/ai_runtime/registry.py",
        "apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py",
    }
)
ORCHESTRATOR_AGENT_ID = "interview_orchestrator_agent"
ORCHESTRATOR_SKILL_IDS = frozenset(
    {
        "orch_goal_decomposition_skill",
        "orch_agent_route_planning_skill",
        "orch_cross_agent_handoff_validation_skill",
        "orch_state_checkpoint_planning_skill",
        "orch_trace_timeline_planning_skill",
        "orch_hitl_trigger_planning_skill",
    }
)
ORCHESTRATOR_TOOL_IDS = frozenset(
    {
        "orch_read_agent_catalog_contract",
        "orch_validate_cross_agent_plan_contract",
        "orch_validate_cross_agent_handoff_contract",
        "orch_validate_cross_agent_state_contract",
        "orch_validate_cross_agent_trace_contract",
        "orch_validate_hitl_trigger_contract",
    }
)
ORCHESTRATOR_CANDIDATE_OUTPUTS = frozenset(
    {
        "cross_agent_plan_candidate",
        "cross_agent_handoff_candidate",
        "cross_agent_state_candidate",
        "cross_agent_trace_candidate",
    }
)
PRODUCT_SLICE_AGENT_IDS = frozenset({"asset_candidate_agent", "training_plan_agent"})
PRODUCT_SLICE_CANDIDATE_OUTPUTS = {
    "asset_candidate_agent": {"asset_update_candidate"},
    "training_plan_agent": {"training_plan_candidate"},
}
REQUIRED_CROSS_AGENT_FORBIDDEN_DATA = frozenset(
    {
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "raw_provider_payload",
        "provider_payload",
        "raw_completion",
        "full_resume",
        "full_jd",
        "full_answer",
        "full_asset_body",
        "secrets",
        "tokens",
        "cookies",
        "api_key",
        "api_keys",
    }
)


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _python_files(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    return tuple(sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts))


def _imported_modules(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
    return tuple(modules)


def test_phase11_l5_catalog_registers_orchestrator_without_replacing_c1() -> None:
    from app.application.agents.definitions.catalog import (
        build_default_agent_platform_c1_registries,
        build_default_agent_platform_l5_contract_registries,
        build_phase11_l5_agent_definitions,
        build_phase11_l5_skill_definitions,
        build_phase11_l5_tool_definitions,
    )

    c1_registries = build_default_agent_platform_c1_registries()
    l5_registries = build_default_agent_platform_l5_contract_registries()

    c1_agent_ids = {agent.agent_id for agent in c1_registries.agent_definitions.list()}
    l5_agent_ids = {agent.agent_id for agent in l5_registries.agent_definitions.list()}

    assert c1_agent_ids == {"polish_question_agent", "polish_feedback_agent"}
    assert ORCHESTRATOR_AGENT_ID not in c1_agent_ids
    assert l5_agent_ids == c1_agent_ids | {ORCHESTRATOR_AGENT_ID} | PRODUCT_SLICE_AGENT_IDS
    assert ORCHESTRATOR_AGENT_ID in {agent.agent_id for agent in build_phase11_l5_agent_definitions()}
    assert ORCHESTRATOR_SKILL_IDS <= {skill.skill_id for skill in build_phase11_l5_skill_definitions()}
    assert ORCHESTRATOR_TOOL_IDS <= {tool.tool_id for tool in build_phase11_l5_tool_definitions()}
    assert c1_registries.agent_definitions.get("polish_question_agent") == l5_registries.agent_definitions.get(
        "polish_question_agent"
    )
    l5_registries.agent_definitions.validate_references(l5_registries.skills, l5_registries.tools)


def test_phase11_l5_catalog_registers_product_slice_agents_without_changing_c1() -> None:
    from app.application.agents.definitions.catalog import (
        build_default_agent_platform_c1_registries,
        build_default_agent_platform_l5_contract_registries,
    )
    from app.application.agents.registry import ALLOWED_CANDIDATE_OUTPUTS

    c1_registries = build_default_agent_platform_c1_registries()
    l5_registries = build_default_agent_platform_l5_contract_registries()

    assert {agent.agent_id for agent in c1_registries.agent_definitions.list()} == {
        "polish_question_agent",
        "polish_feedback_agent",
    }
    for agent_id, expected_outputs in PRODUCT_SLICE_CANDIDATE_OUTPUTS.items():
        agent = l5_registries.agent_definitions.get(agent_id)
        assert set(agent.candidate_outputs) == expected_outputs
        assert set(agent.candidate_outputs) <= ALLOWED_CANDIDATE_OUTPUTS
        assert agent.lifecycle_status == "contract_only"
        assert "not L5 release" in agent.maturity_level
        assert agent.trace_contract.provider_refs == ()
        assert agent.handoff_contract.allowed_formal_targets == ()
        assert agent.handoff_contract.formal_write_policy == "handoff_required"
        assert "no provider or LLM call".lower() in " ".join(agent.non_goals).lower()
        assert "no direct DB or repository write".lower() in " ".join(agent.non_goals).lower()
        assert l5_registries.skills.list_by_agent_id(agent_id)
        assert l5_registries.tools.list_by_agent_id(agent_id)

    asset_agent = l5_registries.agent_definitions.get("asset_candidate_agent")
    assert asset_agent.handoff_contract.user_confirmation_required is True
    assert asset_agent.handoff_contract.candidate_ref_types == ("asset_update_candidate",)

    training_agent = l5_registries.agent_definitions.get("training_plan_agent")
    assert training_agent.handoff_contract.user_confirmation_required is False
    assert training_agent.handoff_contract.candidate_ref_types == ("training_plan_candidate",)


def test_phase11_l5_product_slice_integrates_three_business_agents_typed_handoff_and_trace() -> None:
    from app.application.agents.orchestration.minimal_three_agent_slice import PRODUCT_SLICE_STATUS_READY

    result = _build_p11_w5_product_slice(low_confidence_flags=("source_gap",))

    assert result.status == PRODUCT_SLICE_STATUS_READY
    assert result.orchestrator_agent_id == ORCHESTRATOR_AGENT_ID
    assert len(result.participant_agent_ids) >= 3
    assert set(result.participant_agent_ids) == {
        "polish_feedback_agent",
        "asset_candidate_agent",
        "training_plan_agent",
    }
    assert set(result.candidate_refs) == {
        "feedback_candidate",
        "asset_update_candidate",
        "training_plan_candidate",
    }
    assert result.formal_write_blocked is True
    assert result.hitl_required is True
    assert result.asset_update_user_confirmation_required is True
    assert result.metadata["candidate_only"] is True
    assert result.metadata["formal_write_blocked"] is True
    assert result.metadata["llm_call_count"] == 0
    assert result.metadata["provider_call_count"] == 0
    assert result.metadata["external_call_count"] == 0

    handoff_edges = {
        (handoff.source_agent_id, handoff.target_agent_id, handoff.candidate_type)
        for handoff in result.handoff_refs
    }
    assert handoff_edges == {
        ("polish_feedback_agent", "asset_candidate_agent", "asset_update_candidate"),
        ("asset_candidate_agent", "training_plan_agent", "training_plan_candidate"),
    }
    for handoff in result.handoff_refs:
        assert is_dataclass(handoff)
        assert handoff.handoff_ref
        assert handoff.source_candidate_ref
        assert handoff.candidate_ref
        assert handoff.trace_refs == result.trace_refs
        assert handoff.validation_refs == result.validation_refs
        assert handoff.side_effect_policy == "candidate_write"
        assert handoff.formal_write_blocked is True

    for candidate in result.candidates:
        assert candidate.formal_write_blocked is True
        assert candidate.trace_refs == result.trace_refs
        assert candidate.validation_refs == result.validation_refs

    handoff_refs = tuple(handoff.handoff_ref for handoff in result.handoff_refs)
    for event in result.timeline_events:
        assert event["handoff_refs"] == handoff_refs
        assert event["trace_refs"] == result.trace_refs
        assert event["validation_refs"] == result.validation_refs
        assert event["low_confidence_flags"] == ("source_gap",)
        assert event["formal_write_blocked"] is True
        assert set(event["handoff_refs"]).isdisjoint(event["validation_refs"])


def test_phase11_l5_formal_write_request_is_blocked_before_candidate_or_handoff_success() -> None:
    from app.application.agents.orchestration.minimal_three_agent_slice import (
        PRODUCT_SLICE_STATUS_BLOCKED,
        PRODUCT_SLICE_STATUS_READY,
    )

    result = _build_p11_w5_product_slice(
        formal_write_requested=True,
        formal_write_requested_ref="formal_write_interrupt_ref_p11w5",
    )

    assert result.status == PRODUCT_SLICE_STATUS_BLOCKED
    assert result.status != PRODUCT_SLICE_STATUS_READY
    assert result.failure_reason == "formal_write_requested"
    assert result.blocking_reasons == ("formal_write_requested",)
    assert result.candidate_refs == {}
    assert result.handoff_refs == ()
    assert result.formal_write_blocked is True
    assert result.metadata["interrupt_refs"] == ("formal_write_interrupt_ref_p11w5",)
    assert result.metadata["formal_write_blocked"] is True
    assert "formal_refs" not in result.metadata
    assert "formal_write_result" not in result.metadata


def test_phase11_l5_asset_conflict_blocks_before_asset_or_training_candidates() -> None:
    from app.application.agents.orchestration.minimal_three_agent_slice import PRODUCT_SLICE_STATUS_BLOCKED

    result = _build_p11_w5_product_slice(asset_conflict_ref="asset_conflict_interrupt_ref_p11w5")

    assert result.status == PRODUCT_SLICE_STATUS_BLOCKED
    assert result.failure_reason == "asset_conflict"
    assert result.blocking_reasons == ("asset_conflict",)
    assert result.candidate_refs == {"feedback_candidate": "feedback_candidate_ref_p11w5"}
    assert "asset_update_candidate" not in result.candidate_refs
    assert "training_plan_candidate" not in result.candidate_refs
    assert result.formal_write_blocked is True
    assert result.metadata["asset_conflict_ref"] == "asset_conflict_interrupt_ref_p11w5"
    assert result.metadata["interrupt_refs"] == ("asset_conflict_interrupt_ref_p11w5",)
    assert result.timeline_events[0]["failure_reason"] == "asset_conflict"


def test_orchestrator_definition_is_default_off_local_candidate_only_and_non_release() -> None:
    from app.application.agents.contracts import (
        CROSS_AGENT_ALLOWED_SIDE_EFFECT_POLICIES,
        CROSS_AGENT_HITL_TRIGGER_TYPES,
        CrossAgentPlan,
        CrossAgentHandoffRoute,
        CrossAgentStateContract,
        CrossAgentTraceContract,
    )
    from app.application.agents.definitions.catalog import build_default_agent_platform_l5_contract_registries
    from app.application.agents.registry import ALLOWED_CANDIDATE_OUTPUTS

    registries = build_default_agent_platform_l5_contract_registries()
    orchestrator = registries.agent_definitions.get(ORCHESTRATOR_AGENT_ID)

    assert orchestrator.lifecycle_status == "default_off_local_runtime_validated"
    assert "release" not in orchestrator.lifecycle_status
    assert "default-off local runtime" in orchestrator.maturity_level
    assert "not production L5 release" in orchestrator.maturity_level
    assert set(orchestrator.candidate_outputs) == ORCHESTRATOR_CANDIDATE_OUTPUTS
    assert set(orchestrator.candidate_outputs) <= ALLOWED_CANDIDATE_OUTPUTS
    assert "direct formal writes disallowed" in orchestrator.formal_write_boundary
    assert isinstance(orchestrator.input_contract, CrossAgentPlan)
    assert isinstance(orchestrator.handoff_contract, CrossAgentHandoffRoute)
    assert isinstance(orchestrator.trace_contract, CrossAgentTraceContract)
    assert isinstance(orchestrator.input_contract.state_contract, CrossAgentStateContract)
    assert ORCHESTRATOR_SKILL_IDS == set(orchestrator.skills)
    assert ORCHESTRATOR_TOOL_IDS == set(orchestrator.tools)
    assert set(orchestrator.hitl_triggers) == {
        "asset_conflict",
        "formal_write_requested",
        "low_confidence",
        "ambiguous_ownership",
        "validation_failed_partial_result",
    }

    non_goal_text = " ".join(orchestrator.non_goals).lower()
    for required_non_claim in (
        "no l5 release claim",
        "no default-on runtime execution",
        "no production workflow release or traffic rollout",
        "no direct db or repository write",
        "no prompt/provider/api/db/domain behavior change",
        "no real-provider quality certification",
    ):
        assert required_non_claim in non_goal_text
    for forbidden_field in ("formal_outputs", "formal_refs", "formal_write_result"):
        assert forbidden_field not in {field.name for field in fields(type(orchestrator))}


def test_orchestrator_metadata_uses_default_off_local_runtime_language() -> None:
    from app.application.agents.definitions.catalog import build_default_agent_platform_l5_contract_registries

    orchestrator = build_default_agent_platform_l5_contract_registries().agent_definitions.get(
        ORCHESTRATOR_AGENT_ID
    )

    metadata_text = " ".join(
        (
            orchestrator.maturity_level,
            orchestrator.lifecycle_status,
            orchestrator.mission,
            orchestrator.user_goal,
            orchestrator.autonomous_goal,
            *orchestrator.non_goals,
            orchestrator.formal_write_boundary,
            orchestrator.memory_state,
            orchestrator.planning_strategy,
            *orchestrator.guardrails,
            orchestrator.failure_semantics,
            orchestrator.eval_contract.contract_id,
            *orchestrator.eval_contract.eval_suite_ids,
            *orchestrator.eval_contract.metrics,
            *orchestrator.eval_contract.dataset_refs,
            *orchestrator.eval_contract.grader_refs,
            *orchestrator.eval_contract.regression_cases,
            orchestrator.eval_contract.minimum_pass_criteria,
            orchestrator.eval_contract.failure_triage_policy,
            orchestrator.catalog_revision,
        )
    ).lower()

    for stale_phrase in ("no_runtime_wiring", "contract_deferred", "no_product_workflow_execution"):
        assert stale_phrase not in metadata_text

    assert "default-off local runtime" in metadata_text
    assert "default_off_local_runtime_guard" in orchestrator.guardrails
    assert "no_production_workflow_release" in orchestrator.guardrails
    assert "candidate_only" in orchestrator.guardrails
    assert "direct formal writes disallowed" in orchestrator.formal_write_boundary
    assert "real-provider quality certification" in metadata_text


def test_cross_agent_contracts_fail_closed_and_forbid_raw_payloads() -> None:
    from app.application.agents.contracts import (
        CROSS_AGENT_ALLOWED_SIDE_EFFECT_POLICIES,
        CROSS_AGENT_HITL_TRIGGER_TYPES,
        CrossAgentHandoffRoute,
        CrossAgentPlan,
        CrossAgentTraceContract,
    )
    from app.application.agents.definitions.catalog import build_default_agent_platform_l5_contract_registries

    orchestrator = build_default_agent_platform_l5_contract_registries().agent_definitions.get(
        ORCHESTRATOR_AGENT_ID
    )
    plan = orchestrator.input_contract
    handoff = orchestrator.handoff_contract
    trace = orchestrator.trace_contract

    assert isinstance(plan, CrossAgentPlan)
    assert isinstance(handoff, CrossAgentHandoffRoute)
    assert isinstance(trace, CrossAgentTraceContract)
    assert plan.steps
    assert plan.participant_agent_ids == ("polish_question_agent", "polish_feedback_agent")
    assert plan.max_steps > 0
    assert plan.max_retries >= 0
    assert plan.timeout_seconds > 0
    assert plan.stop_conditions
    assert plan.state_ref
    assert plan.trace_ref
    assert handoff.required_trace_refs
    assert handoff.required_validation_refs
    assert handoff.side_effect_policy in CROSS_AGENT_ALLOWED_SIDE_EFFECT_POLICIES
    assert set(orchestrator.hitl_triggers) <= set(CROSS_AGENT_HITL_TRIGGER_TYPES)
    assert "formal_write_requested" in handoff.user_confirmation_required_when
    assert "asset_update_candidate" in handoff.user_confirmation_required_when
    assert set(handoff.user_confirmation_required_when) <= set(CROSS_AGENT_HITL_TRIGGER_TYPES) | {
        "asset_update_candidate",
    }
    assert trace.required_trace_refs
    assert trace.validation_refs
    assert REQUIRED_CROSS_AGENT_FORBIDDEN_DATA <= set(handoff.forbidden_data)
    assert REQUIRED_CROSS_AGENT_FORBIDDEN_DATA <= set(plan.state_contract.forbidden_data)
    assert REQUIRED_CROSS_AGENT_FORBIDDEN_DATA <= set(trace.forbidden_data)

    with pytest.raises(ValueError, match="required_trace_refs"):
        replace(handoff, route_id="bad_missing_trace_refs", required_trace_refs=())
    with pytest.raises(ValueError, match="validation_refs"):
        replace(trace, trace_schema_id="bad_missing_validation_refs", validation_refs=())
    with pytest.raises(ValueError, match="max_steps"):
        replace(plan, plan_id="bad_max_steps", max_steps=0)


def test_orchestrator_tools_are_contract_only_and_registry_blocks_direct_exposure() -> None:
    from app.application.agents.contracts import ToolDefinition
    from app.application.agents.definitions.catalog import build_default_agent_platform_l5_contract_registries
    from app.application.agents.registry import RegistryValidationError, ToolRegistry

    registries = build_default_agent_platform_l5_contract_registries()
    tools = tuple(registries.tools.get(tool_id) for tool_id in ORCHESTRATOR_TOOL_IDS)

    for tool in tools:
        assert tool.side_effect_policy in {"read_only", "forbidden"}
        assert tool.allowed_callers == (ORCHESTRATOR_AGENT_ID,)
        assert REQUIRED_CROSS_AGENT_FORBIDDEN_DATA <= set(tool.forbidden_data)
        assert "runtime" not in tool.permission_scope.lower()
        assert "repository" not in " ".join(
            (tool.tool_id, tool.tool_name, tool.input_schema_id, tool.output_schema_id, tool.permission_scope)
        ).lower()

    forbidden_tool = ToolDefinition(
        tool_id="orch_direct_repository_reader",
        tool_name="direct_repository_reader",
        input_schema_id="tool.repository.input.v1",
        output_schema_id="tool.repository.output.v1",
        permission_scope="repository_read",
        owner_scope="sqlalchemy_session",
        side_effect_policy="read_only",
        timeout_seconds=5,
        retry_policy="none",
        allowed_callers=(ORCHESTRATOR_AGENT_ID,),
        forbidden_data=tuple(sorted(REQUIRED_CROSS_AGENT_FORBIDDEN_DATA)),
        trace_events=("tool.repository.requested",),
    )
    with pytest.raises(RegistryValidationError, match="direct exposure"):
        ToolRegistry((forbidden_tool,))


def test_orchestrator_is_only_default_off_local_runtime_wired_and_not_provider_bound() -> None:
    from app.application.agents.definitions.catalog import build_default_agent_platform_l5_contract_registries

    build_default_agent_platform_l5_contract_registries()

    wired_files = [
        _relative(path)
        for root in FORBIDDEN_WIRING_ROOTS
        for path in _python_files(root)
        if ORCHESTRATOR_AGENT_ID in path.read_text(encoding="utf-8")
    ]
    assert [path for path in wired_files if path not in ALLOWED_DEFAULT_OFF_LOCAL_RUNTIME_WIRING] == []

    checked_files = (
        AGENTS_ROOT / "definitions" / "catalog.py",
        AGENTS_ROOT / "definitions" / "orchestrator.py",
    )
    forbidden_import_prefixes = (
        "app.api",
        "app.application.ai_runtime",
        "app.application.llm",
        "app.application.polish",
        "app.domain",
        "app.infrastructure",
        "langgraph",
        "sqlalchemy",
    )
    import_violations = [
        f"{_relative(path)} imports {module}"
        for path in checked_files
        for module in _imported_modules(path)
        if any(module == prefix or module.startswith(f"{prefix}.") for prefix in forbidden_import_prefixes)
    ]
    assert import_violations == []


def _build_p11_w5_product_slice(**overrides: object):
    from app.application.agents.orchestration import build_minimal_three_agent_product_slice

    params: dict[str, object] = {
        "owner_id": "owner_p11w5",
        "session_ref": "session_ref_p11w5",
        "feedback_candidate_ref": "feedback_candidate_ref_p11w5",
        "answer_ref": "answer_ref_p11w5",
        "question_ref": "question_ref_p11w5",
        "evidence_refs": ("evidence_ref_p11w5_1", "evidence_ref_p11w5_2"),
        "source_trace_refs": ("trace_ref_p11w5_feedback",),
        "validation_refs": ("validation_ref_p11w5_feedback", "validation_ref_p11w5_asset"),
        "idempotency_key": "idem_p11w5",
    }
    params.update(overrides)
    return build_minimal_three_agent_product_slice(**params)
