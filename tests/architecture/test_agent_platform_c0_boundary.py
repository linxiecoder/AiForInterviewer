from __future__ import annotations

import ast
import importlib
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_ROOT = REPO_ROOT / "apps" / "api" / "app" / "application" / "agents"
DOMAIN_ROOT = REPO_ROOT / "apps" / "api" / "app" / "domain"

AGENT_PLATFORM_FORBIDDEN_IMPORTS = (
    "app.api",
    "app.infrastructure",
    "app.application.llm",
    "fastapi",
    "sqlalchemy",
    "alembic",
    "asyncpg",
    "psycopg",
    "langgraph",
    "openai",
    "anthropic",
)

DOMAIN_FORBIDDEN_IMPORTS = (
    "app.api",
    "app.infrastructure",
    "app.application.llm",
)


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts))


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _imported_modules(path: Path) -> tuple[tuple[int, str], ...]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.lineno, node.module))
        elif isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name) for alias in node.names)
    return tuple(imports)


def _forbidden_import_violations(root: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    for path in _python_files(root):
        for lineno, module_name in _imported_modules(path):
            if any(module_name == prefix or module_name.startswith(f"{prefix}.") for prefix in forbidden_prefixes):
                violations.append(f"{_relative(path)}:{lineno}: {module_name}")
    return violations


def _sample_handoff_contract() -> Any:
    from app.application.agents.contracts import HandoffContract

    return HandoffContract(
        contract_id="handoff.polish.candidate.v1",
        candidate_ref_types=("agent_candidate_ref",),
        formal_write_policy="handoff_required",
        allowed_formal_targets=("polish_question",),
        confirmation_required=True,
    )


def _sample_eval_contract() -> Any:
    from app.application.agents.contracts import EvalContract

    return EvalContract(
        contract_id="eval.polish.question.v1",
        eval_suite_ids=("eval.polish.question.c0",),
        metrics=("candidate_contract_shape",),
        failure_policy="fail_closed",
    )


def _sample_agent_definition() -> Any:
    from app.application.agents.contracts import AgentDefinition

    return AgentDefinition(
        agent_id="polish-question-agent",
        agent_name="Polish Question Agent",
        domain="polish",
        version="c0",
        maturity_level="skeleton",
        lifecycle_status="draft",
        mission="Produce candidate question outputs for handoff.",
        user_goal="Receive a grounded interview question candidate.",
        autonomous_goal="Prepare candidate refs without formal writes.",
        non_goals=("formal persistence", "provider execution"),
        input_contract="polish.question.input.v1",
        output_contract="polish.question.candidate.v1",
        candidate_outputs=("question_candidate_ref",),
        formal_write_boundary="handoff_required",
        skills=("question_grounding_skill",),
        tools=("evidence_lookup_tool",),
        memory_state="stateless",
        planning_strategy="single_step",
        guardrails=("candidate_only",),
        hitl_triggers=("low_confidence",),
        failure_semantics="fail_closed",
        trace_contract="trace.polish.question.v1",
        eval_contract=_sample_eval_contract(),
        handoff_contract=_sample_handoff_contract(),
        versioning_policy="semver",
    )


def _sample_skill_definition() -> Any:
    from app.application.agents.contracts import SkillDefinition

    return SkillDefinition(
        skill_id="question_grounding_skill",
        skill_name="Question Grounding",
        owner_agent_ids=("polish-question-agent",),
        input_schema_id="skill.question_grounding.input.v1",
        output_schema_id="skill.question_grounding.output.v1",
        implementation_type="contract_only",
        deterministic_policy_refs=("policy.grounding.c0",),
        llm_refs=(),
        tool_refs=("evidence_lookup_tool",),
        timeout_policy="no_runtime_execution",
        retry_policy="not_applicable",
        failure_semantics="fail_closed",
        trace_events=("skill.grounding.checked",),
        eval_refs=("eval.polish.question.c0",),
    )


def _sample_tool_definition() -> Any:
    from app.application.agents.contracts import ToolDefinition

    return ToolDefinition(
        tool_id="evidence_lookup_tool",
        tool_name="Evidence Lookup",
        input_schema_id="tool.evidence_lookup.input.v1",
        output_schema_id="tool.evidence_lookup.output.v1",
        permission_scope="owner_read",
        owner_scope="same_owner_only",
        side_effect_policy="read_only",
        timeout_seconds=5,
        retry_policy="none",
        allowed_callers=("polish-question-agent",),
        forbidden_data=("repository_object", "provider_payload"),
        trace_events=("tool.evidence_lookup.requested",),
    )


def test_agent_platform_modules_import_without_forbidden_dependencies() -> None:
    assert AGENTS_ROOT.exists()

    for module_name in (
        "app.application.agents",
        "app.application.agents.contracts",
        "app.application.agents.definitions",
        "app.application.agents.registry",
        "app.application.agents.runtime",
        "app.application.agents.handoff",
    ):
        importlib.import_module(module_name)

    assert _forbidden_import_violations(AGENTS_ROOT, AGENT_PLATFORM_FORBIDDEN_IMPORTS) == []


def test_agent_definition_skill_tool_registries_are_deterministic_and_fail_closed() -> None:
    from app.application.agents.registry import (
        AgentDefinitionRegistry,
        RegistryValidationError,
        SkillRegistry,
        ToolRegistry,
    )

    agent = _sample_agent_definition()
    skill = _sample_skill_definition()
    tool = _sample_tool_definition()

    agent_registry = AgentDefinitionRegistry()
    skill_registry = SkillRegistry()
    tool_registry = ToolRegistry()

    agent_registry.register(agent)
    skill_registry.register(skill)
    tool_registry.register(tool)

    assert agent_registry.get("polish-question-agent") == agent
    assert agent_registry.list() == (agent,)
    assert skill_registry.get("question_grounding_skill") == skill
    assert skill_registry.list() == (skill,)
    assert tool_registry.get("evidence_lookup_tool") == tool
    assert tool_registry.list() == (tool,)

    with pytest.raises(RegistryValidationError):
        agent_registry.register(agent)
    with pytest.raises(RegistryValidationError):
        skill_registry.register(skill)
    with pytest.raises(RegistryValidationError):
        tool_registry.register(tool)
    with pytest.raises(RegistryValidationError):
        AgentDefinitionRegistry().register(replace(agent, agent_id=" "))


def test_tool_registry_exposes_definitions_not_repository_objects() -> None:
    from app.application.agents.registry import RegistryValidationError, ToolRegistry

    tool = _sample_tool_definition()
    registry = ToolRegistry((tool,))

    assert registry.list() == (tool,)
    assert all(item.__class__.__name__ == "ToolDefinition" for item in registry.list())
    for forbidden_handle in (
        "repository",
        "repositories",
        "db",
        "database",
        "engine",
        "session",
        "unit_of_work",
        "formal_writer",
        "formal_write",
        "write_formal",
    ):
        assert not hasattr(registry, forbidden_handle)

    with pytest.raises(RegistryValidationError):
        registry.register(object())


def test_agent_execution_result_is_candidate_only_until_handoff() -> None:
    from app.application.agents.contracts import AgentDefinition, AgentExecutionResult, HandoffContract

    result_field_names = {field.name for field in fields(AgentExecutionResult)}
    agent_field_names = {field.name for field in fields(AgentDefinition)}
    handoff_field_names = {field.name for field in fields(HandoffContract)}

    assert "candidate_refs" in result_field_names
    assert "trace" in result_field_names
    assert "formal_refs" not in result_field_names
    assert "formal_outputs" not in result_field_names
    assert "formal_write" not in result_field_names
    assert "formal_write_ref" not in result_field_names
    assert "formal_write_result" not in result_field_names
    assert "formal_write_results" not in result_field_names
    assert "formal_write_path" not in result_field_names
    assert "formal_write_boundary" in agent_field_names
    assert "formal_write_policy" in handoff_field_names


def test_agent_executor_port_is_independent_from_existing_graph_runtime_contracts() -> None:
    from app.application.ai_runtime.contracts import AgentGraphRunner, AgentRunContext, AgentRunResult
    from app.application.agents.runtime import AgentExecutor

    assert AgentGraphRunner is not AgentExecutor
    assert AgentRunContext.__name__ == "AgentRunContext"
    assert AgentRunResult.__name__ == "AgentRunResult"

    for method_name in ("start", "resume", "replay", "get_status", "get_timeline", "cancel"):
        assert hasattr(AgentExecutor, method_name)


def test_domain_layer_does_not_import_infrastructure_api_or_application_llm() -> None:
    assert _forbidden_import_violations(DOMAIN_ROOT, DOMAIN_FORBIDDEN_IMPORTS) == []
