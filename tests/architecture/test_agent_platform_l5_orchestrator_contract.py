from __future__ import annotations

import ast
from dataclasses import fields, replace
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
    assert l5_agent_ids == c1_agent_ids | {ORCHESTRATOR_AGENT_ID}
    assert build_phase11_l5_agent_definitions()[-1].agent_id == ORCHESTRATOR_AGENT_ID
    assert ORCHESTRATOR_SKILL_IDS <= {skill.skill_id for skill in build_phase11_l5_skill_definitions()}
    assert ORCHESTRATOR_TOOL_IDS <= {tool.tool_id for tool in build_phase11_l5_tool_definitions()}
    assert c1_registries.agent_definitions.get("polish_question_agent") == l5_registries.agent_definitions.get(
        "polish_question_agent"
    )
    l5_registries.agent_definitions.validate_references(l5_registries.skills, l5_registries.tools)


def test_orchestrator_definition_is_contract_only_candidate_only_and_non_release() -> None:
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

    assert orchestrator.lifecycle_status in {"contract_only", "implementation_planned"}
    assert "release" not in orchestrator.lifecycle_status
    assert "L5 target contract" in orchestrator.maturity_level
    assert set(orchestrator.candidate_outputs) == ORCHESTRATOR_CANDIDATE_OUTPUTS
    assert set(orchestrator.candidate_outputs) <= ALLOWED_CANDIDATE_OUTPUTS
    assert "direct formal writes disallowed" in orchestrator.formal_write_boundary
    assert isinstance(orchestrator.input_contract, CrossAgentPlan)
    assert isinstance(orchestrator.handoff_contract, CrossAgentHandoffRoute)
    assert isinstance(orchestrator.trace_contract, CrossAgentTraceContract)
    assert isinstance(orchestrator.input_contract.state_contract, CrossAgentStateContract)
    assert ORCHESTRATOR_SKILL_IDS == set(orchestrator.skills)
    assert ORCHESTRATOR_TOOL_IDS == set(orchestrator.tools)

    non_goal_text = " ".join(orchestrator.non_goals).lower()
    for required_non_claim in (
        "no l5 release claim",
        "no runtime execution",
        "no product workflow execution",
        "no direct db or repository write",
        "no prompt/provider/api/db/domain behavior change",
        "no real-provider quality certification",
    ):
        assert required_non_claim in non_goal_text
    for forbidden_field in ("formal_outputs", "formal_refs", "formal_write_result"):
        assert forbidden_field not in {field.name for field in fields(type(orchestrator))}


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


def test_orchestrator_is_not_runtime_wired_or_provider_bound() -> None:
    from app.application.agents.definitions.catalog import build_default_agent_platform_l5_contract_registries

    build_default_agent_platform_l5_contract_registries()

    wired_files = [
        _relative(path)
        for root in FORBIDDEN_WIRING_ROOTS
        for path in _python_files(root)
        if ORCHESTRATOR_AGENT_ID in path.read_text(encoding="utf-8")
    ]
    assert wired_files == []

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
