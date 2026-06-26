from __future__ import annotations

import ast
from dataclasses import fields, replace
from pathlib import Path
import re

import pytest


REQUIRED_TOOL_FORBIDDEN_DATA = frozenset(
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


FORBIDDEN_DIRECT_EXPOSURE_TERMS = (
    "repository",
    "repositories",
    "db",
    "database",
    "sqlalchemy",
    "session",
    "unit_of_work",
    "uow",
    "raw_prompt",
    "provider_payload",
    "full_resume",
    "full_jd",
    "secrets",
)

EXPECTED_C_TARGET_CANDIDATE_OUTPUTS = frozenset(
    {
        "question_candidate",
        "feedback_candidate",
        "asset_update_candidate",
        "progress_update_candidate",
        "weakness_candidate",
        "training_plan_candidate",
        "report_candidate",
        "review_candidate",
    }
)

AGENT_PLATFORM_ROOT = Path(__file__).resolve().parents[2] / "apps/api/app/application/agents"
REPO_ROOT = Path(__file__).resolve().parents[2]
AI_RUNTIME_ROOT = REPO_ROOT / "apps/api/app/application/ai_runtime"
CATALOG_PATH = AGENT_PLATFORM_ROOT / "definitions/catalog.py"
CATALOG_REVISION = "2026-06-05.p4-w1.fix01"
LEGACY_PHASE_SCHEMA_MARKER = "p4" + ".c1"
LEGACY_PHASE_VERSION_CONSTANT = "C1" + "_VERSION"
EXPECTED_RUNTIME_TOOL_AUTHORIZATION_CALL_FILES = frozenset(
    {
        "apps/api/app/application/ai_runtime/business_graphs/polish_feedback_graph.py",
        "apps/api/app/application/ai_runtime/business_graphs/polish_question_graph.py",
    }
)


def _metadata_tokens(*values: str) -> set[str]:
    return {token for value in values for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def _contains_forbidden_direct_exposure(*values: str) -> bool:
    tokens = _metadata_tokens(*values)
    return any(term in tokens for term in FORBIDDEN_DIRECT_EXPOSURE_TERMS)


def _public_ast_nodes_missing_docstrings(path: Path, node_type: type[ast.AST]) -> list[str]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    missing = []
    for node in ast.walk(module):
        if isinstance(node, node_type) and not node.name.startswith("_") and ast.get_docstring(node) is None:
            missing.append(f"{path.relative_to(AGENT_PLATFORM_ROOT)}:{node.name}")
    return sorted(missing)


def _runtime_tool_authorization_calls() -> list[tuple[Path, ast.Call]]:
    calls: list[tuple[Path, ast.Call]] = []
    for path in sorted(AI_RUNTIME_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "authorize_tool_call":
                    calls.append((path, node))
    return calls


def test_agent_platform_public_contract_and_catalog_api_has_docstrings() -> None:
    definitions_files = sorted((AGENT_PLATFORM_ROOT / "definitions").rglob("*.py"))
    contract_class_files = (
        sorted((AGENT_PLATFORM_ROOT / "contracts").rglob("*.py"))
        + definitions_files
        + sorted((AGENT_PLATFORM_ROOT / "registry").rglob("*.py"))
    )

    missing_module_docstrings = [
        str(path.relative_to(AGENT_PLATFORM_ROOT))
        for path in definitions_files
        if ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))) is None
    ]
    missing_class_docstrings = [
        item
        for path in contract_class_files
        for item in _public_ast_nodes_missing_docstrings(path, ast.ClassDef)
    ]
    missing_function_docstrings = [
        item
        for path in definitions_files
        for item in _public_ast_nodes_missing_docstrings(path, ast.FunctionDef)
    ]

    assert missing_module_docstrings == []
    assert missing_class_docstrings == []
    assert missing_function_docstrings == []


def test_runtime_tool_authorization_call_sites_require_tool_definition_keyword() -> None:
    calls = _runtime_tool_authorization_calls()
    call_files = {path.relative_to(REPO_ROOT).as_posix() for path, _node in calls}
    missing_tool_keyword = []
    none_tool_keyword = []

    for path, node in calls:
        keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg is not None}
        site = f"{path.relative_to(REPO_ROOT).as_posix()}:{node.lineno}"
        if "tool" not in keywords:
            missing_tool_keyword.append(site)
            continue
        tool_value = keywords["tool"]
        if isinstance(tool_value, ast.Constant) and tool_value.value is None:
            none_tool_keyword.append(site)

    assert call_files == EXPECTED_RUNTIME_TOOL_AUTHORIZATION_CALL_FILES
    assert missing_tool_keyword == []
    assert none_tool_keyword == []


def test_default_phase4_c1_catalog_registers_question_and_feedback_agents() -> None:
    from app.application.agents.definitions.catalog import build_default_agent_platform_c1_registries

    registries = build_default_agent_platform_c1_registries()
    agent_registry = registries.agent_definitions
    skill_registry = registries.skills
    tool_registry = registries.tools

    question_agent = agent_registry.get("polish_question_agent")
    feedback_agent = agent_registry.get("polish_feedback_agent")

    assert {agent.agent_id for agent in agent_registry.list()} >= {
        "polish_question_agent",
        "polish_feedback_agent",
    }
    assert question_agent.version == "1.0.0"
    assert feedback_agent.version == "1.0.0"
    assert question_agent.schema_version == "agent-definition.v1"
    assert feedback_agent.schema_version == "agent-definition.v1"
    assert question_agent.catalog_revision == CATALOG_REVISION
    assert feedback_agent.catalog_revision == CATALOG_REVISION
    assert question_agent.maturity_level == "L2 planned guarded workflow"
    assert feedback_agent.lifecycle_status == "planned_guarded_workflow"

    assert skill_registry.list_by_agent_id("polish_question_agent") == tuple(
        skill_registry.get(skill_id) for skill_id in question_agent.skills
    )
    assert tool_registry.list_by_agent_id("polish_question_agent") == tuple(
        tool_registry.get(tool_id) for tool_id in question_agent.tools
    )
    assert skill_registry.list_by_agent_id("polish_feedback_agent") == tuple(
        skill_registry.get(skill_id) for skill_id in feedback_agent.skills
    )
    assert tool_registry.list_by_agent_id("polish_feedback_agent") == tuple(
        tool_registry.get(tool_id) for tool_id in feedback_agent.tools
    )

    for agent in (question_agent, feedback_agent):
        for skill_id in agent.skills:
            assert skill_registry.get(skill_id).skill_id == skill_id
        for tool_id in agent.tools:
            assert tool_registry.get(tool_id).tool_id == tool_id

    assert len(question_agent.skills) == 8
    assert len(question_agent.tools) == 8
    assert len(feedback_agent.skills) == 10
    assert len(feedback_agent.tools) == 9

    agent_registry.validate_references(skill_registry, tool_registry)


def test_phase4_c1_catalog_uses_stable_versions_and_enriched_skill_contracts() -> None:
    from app.application.agents.contracts import AgentDefinition, SkillDefinition
    from app.application.agents.definitions.catalog import (
        CATALOG_REVISION as exported_catalog_revision,
        build_default_agent_platform_c1_registries,
    )

    registries = build_default_agent_platform_c1_registries()

    assert exported_catalog_revision == CATALOG_REVISION

    agent_field_names = {field.name for field in fields(AgentDefinition)}
    assert "schema_version" in agent_field_names
    assert "catalog_revision" in agent_field_names

    skill_field_names = {field.name for field in fields(SkillDefinition)}
    for expected_field in (
        "purpose",
        "implementation_ref",
        "preconditions",
        "postconditions",
        "fallback_policy",
        "lifecycle_status",
        "definition_version",
        "schema_version",
        "test_refs",
    ):
        assert expected_field in skill_field_names

    for agent in registries.agent_definitions.list():
        assert agent.version == "1.0.0"
        assert agent.schema_version == "agent-definition.v1"
        assert agent.catalog_revision == CATALOG_REVISION
        assert LEGACY_PHASE_SCHEMA_MARKER not in agent.version
        assert LEGACY_PHASE_SCHEMA_MARKER not in agent.input_contract
        assert LEGACY_PHASE_SCHEMA_MARKER not in agent.output_contract
        assert LEGACY_PHASE_SCHEMA_MARKER not in agent.handoff_contract.payload_schema_id

    for skill in registries.skills.list():
        assert skill.purpose
        assert skill.implementation_ref
        assert skill.preconditions
        assert skill.postconditions
        assert skill.fallback_policy
        assert skill.lifecycle_status == "contract_only"
        assert skill.definition_version == "1.0.0"
        assert skill.schema_version == "skill-definition.v1"
        assert skill.test_refs
        assert LEGACY_PHASE_SCHEMA_MARKER not in skill.definition_version
        assert LEGACY_PHASE_SCHEMA_MARKER not in skill.schema_version
        assert LEGACY_PHASE_SCHEMA_MARKER not in skill.input_schema_id
        assert LEGACY_PHASE_SCHEMA_MARKER not in skill.output_schema_id

    for tool in registries.tools.list():
        assert LEGACY_PHASE_SCHEMA_MARKER not in tool.input_schema_id
        assert LEGACY_PHASE_SCHEMA_MARKER not in tool.output_schema_id


def test_phase4_c1_catalog_module_is_aggregation_only() -> None:
    source = CATALOG_PATH.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 160
    assert LEGACY_PHASE_VERSION_CONSTANT not in source
    assert "SkillDefinition(" not in source
    assert "ToolDefinition(" not in source
    assert "qag_source_support_classification_skill" not in source
    assert "fag_expected_point_building_skill" not in source


def test_phase4_c1_agents_are_candidate_only_and_handoff_guarded() -> None:
    from app.application.agents.contracts import AgentDefinition, HandoffContract
    from app.application.agents.definitions.catalog import build_default_agent_platform_c1_registries
    from app.application.agents.registry import ALLOWED_CANDIDATE_OUTPUTS

    registries = build_default_agent_platform_c1_registries()
    question_agent = registries.agent_definitions.get("polish_question_agent")
    feedback_agent = registries.agent_definitions.get("polish_feedback_agent")

    assert EXPECTED_C_TARGET_CANDIDATE_OUTPUTS <= ALLOWED_CANDIDATE_OUTPUTS
    assert question_agent.candidate_outputs == ("question_candidate",)
    assert feedback_agent.candidate_outputs == ("feedback_candidate", "asset_update_candidate")

    agent_field_names = {field.name for field in fields(AgentDefinition)}
    for forbidden_field in (
        "formal_outputs",
        "formal_refs",
        "formal_write",
        "formal_write_ref",
        "formal_write_result",
        "formal_write_results",
    ):
        assert forbidden_field not in agent_field_names
    assert "formal_write_boundary" in agent_field_names
    assert "direct formal writes disallowed" in question_agent.formal_write_boundary
    assert "direct formal writes disallowed" in feedback_agent.formal_write_boundary

    handoff_field_names = {field.name for field in fields(HandoffContract)}
    for expected_field in (
        "candidate_ref_types",
        "payload_schema_id",
        "validation_refs",
        "quality_gate",
        "side_effect_key",
        "idempotency_key",
        "formal_write_preconditions",
        "rollback_policy",
        "user_confirmation_required",
    ):
        assert expected_field in handoff_field_names

    feedback_handoff = feedback_agent.handoff_contract
    assert "asset_update_candidate" in feedback_handoff.candidate_ref_types
    assert feedback_handoff.payload_schema_id == "agent.polish_feedback.handoff_payload.v1"
    assert feedback_handoff.validation_refs
    assert feedback_handoff.quality_gate == "user_confirmed_asset_update"
    assert feedback_handoff.side_effect_key == "asset_update_candidate_handoff"
    assert feedback_handoff.idempotency_key == "feedback_asset_update_candidate_ref"
    assert feedback_handoff.formal_write_preconditions
    assert feedback_handoff.rollback_policy == "discard_candidate_before_formal_write"
    assert feedback_handoff.user_confirmation_required is True


def test_phase4_c1_tools_and_traces_omit_sensitive_runtime_exposure() -> None:
    from app.application.agents.contracts import AgentExecutionTrace, TraceContract
    from app.application.agents.definitions.catalog import build_default_agent_platform_c1_registries
    from app.application.agents.registry import REQUIRED_TOOL_FORBIDDEN_DATA as registry_required_data

    registries = build_default_agent_platform_c1_registries()

    assert REQUIRED_TOOL_FORBIDDEN_DATA <= registry_required_data

    for tool in registries.tools.list():
        assert REQUIRED_TOOL_FORBIDDEN_DATA <= set(tool.forbidden_data)
        assert not _contains_forbidden_direct_exposure(
            tool.tool_id,
            tool.tool_name,
            tool.input_schema_id,
            tool.output_schema_id,
            tool.permission_scope,
            tool.owner_scope,
            " ".join(tool.allowed_callers),
            " ".join(tool.trace_events),
        )

    trace_field_names = {field.name for field in fields(AgentExecutionTrace)}
    for expected_field in (
        "input_refs",
        "plan_refs",
        "skill_refs",
        "tool_refs",
        "policy_refs",
        "provider_refs",
        "candidate_refs",
        "validation_refs",
        "handoff_refs",
        "output_refs",
        "events",
    ):
        assert expected_field in trace_field_names

    trace_contract_field_names = {field.name for field in fields(TraceContract)}
    assert "forbidden_data" in trace_contract_field_names

    for agent in registries.agent_definitions.list():
        trace_contract = agent.trace_contract
        assert REQUIRED_TOOL_FORBIDDEN_DATA <= set(trace_contract.forbidden_data)
        assert trace_contract.input_refs
        assert trace_contract.plan_refs
        assert trace_contract.skill_refs
        assert trace_contract.tool_refs
        assert trace_contract.policy_refs
        assert trace_contract.provider_refs
        assert trace_contract.candidate_refs
        assert trace_contract.validation_refs
        assert trace_contract.handoff_refs
        assert trace_contract.output_refs
        assert trace_contract.events


def test_phase4_c1_registry_validation_fails_closed() -> None:
    from app.application.agents.contracts import ToolDefinition
    from app.application.agents.definitions.catalog import build_default_agent_platform_c1_registries
    from app.application.agents.registry import (
        AgentDefinitionRegistry,
        RegistryValidationError,
        ToolRegistry,
    )

    registries = build_default_agent_platform_c1_registries()
    question_agent = registries.agent_definitions.get("polish_question_agent")
    first_tool = registries.tools.list()[0]

    with pytest.raises(RegistryValidationError, match="unknown skill_id"):
        AgentDefinitionRegistry((replace(question_agent, skills=("missing_skill",)),)).validate_references(
            registries.skills,
            registries.tools,
        )

    with pytest.raises(RegistryValidationError, match="unknown tool_id"):
        AgentDefinitionRegistry((replace(question_agent, tools=("missing_tool",)),)).validate_references(
            registries.skills,
            registries.tools,
        )

    duplicate_registry = AgentDefinitionRegistry((question_agent,))
    with pytest.raises(RegistryValidationError, match="duplicate agent_id"):
        duplicate_registry.register(question_agent)

    with pytest.raises(RegistryValidationError, match="invalid side_effect_policy"):
        ToolRegistry((replace(first_tool, tool_id="invalid_side_effect", side_effect_policy="db_write"),))

    with pytest.raises(RegistryValidationError, match="missing forbidden_data"):
        ToolRegistry((replace(first_tool, tool_id="missing_forbidden_data", forbidden_data=("raw_prompt",)),))

    direct_exposure_tool = ToolDefinition(
        tool_id="repository_exposure",
        tool_name="Repository Exposure",
        input_schema_id="tool.repository.input",
        output_schema_id="tool.repository.output",
        permission_scope="repository_read",
        owner_scope="sqlalchemy_session",
        side_effect_policy="read_only",
        timeout_seconds=5,
        retry_policy="none",
        allowed_callers=("polish_question_agent",),
        forbidden_data=tuple(sorted(REQUIRED_TOOL_FORBIDDEN_DATA)),
        trace_events=("tool.repository.requested",),
    )
    with pytest.raises(RegistryValidationError, match="direct exposure"):
        ToolRegistry((direct_exposure_tool,))
