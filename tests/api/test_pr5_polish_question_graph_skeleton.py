from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.application.ai_runtime.contracts import AgentCommandEnvelope, AgentRunContext, GraphDisabledError
from app.application.ai_runtime.registry import AgentGraphRegistry
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "api" / "app"
FORBIDDEN_METADATA_KEYS = {
    "raw_prompt",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "checkpoint_payload",
}


def test_descriptor_is_default_off_and_pr5_owned() -> None:
    from app.application.ai_runtime.business_graphs.polish_question_graph import (
        POLISH_QUESTION_GRAPH_FLAG,
        POLISH_QUESTION_GRAPH_NAME,
        POLISH_QUESTION_GRAPH_VERSION,
        build_polish_question_graph_descriptor,
    )

    descriptor = build_polish_question_graph_descriptor()

    assert descriptor.graph_name == POLISH_QUESTION_GRAPH_NAME == "polish_question_graph"
    assert descriptor.graph_version == POLISH_QUESTION_GRAPH_VERSION == "pr9-agent-orchestration"
    assert descriptor.runtime_flag_key == POLISH_QUESTION_GRAPH_FLAG == "AIFI_GRAPH_POLISH_QUESTION_ENABLED"
    assert descriptor.default_enabled is False
    assert descriptor.migration_status == "agent_orchestration_with_deterministic_fallback"
    assert descriptor.implementation_pr == "Goal0526"
    assert descriptor.lifecycle_status == "active"
    assert descriptor.provider_enabled is False
    assert descriptor.formal_write_targets == ()
    assert descriptor.db_business_write_targets == ()
    assert descriptor.prompt_contract_ids == ("P-POLISH-002", "P-SHARED-001", "P-SHARED-003")


def test_registry_uses_polish_question_descriptor_builder() -> None:
    from app.application.ai_runtime.business_graphs.polish_question_graph import (
        build_polish_question_graph_descriptor,
    )

    registry = AgentGraphRegistry.default()
    descriptor = registry.get_graph_descriptor("polish_question_generation")

    assert descriptor == build_polish_question_graph_descriptor()
    assert descriptor.graph_name == "polish_question_graph"
    assert descriptor.graph_version == "pr9-agent-orchestration"
    assert descriptor.implementation_pr == "Goal0526"
    assert descriptor.prompt_contract_ids != ("P-POLISH-QUESTION-001",)
    assert registry.get_graph_descriptor("polish_question_graph") == descriptor


def test_skeleton_fails_closed_when_graph_flag_disabled() -> None:
    from app.application.ai_runtime.business_graphs.polish_question_graph import run_polish_question_skeleton

    context = _context()

    with pytest.raises(GraphDisabledError):
        run_polish_question_skeleton(context, context.command)


def test_skeleton_returns_refs_only_when_enabled() -> None:
    from app.application.ai_runtime.business_graphs.polish_question_graph import (
        POLISH_QUESTION_GRAPH_FLAG,
        run_polish_question_skeleton,
    )

    context = _context(
        command=AgentCommandEnvelope(
            entrypoint="start",
            input_refs=("session_ref_1", "progress_node_ref_1", "completed_focus_ref_1"),
            requested_outputs=("candidate_refs", "result_refs"),
            idempotency_key="idem_pr5_question",
            metadata={
                "safe_context_ref": "ctx_ref_1",
                "raw_prompt": "hidden",
                "raw_completion": "hidden",
                "provider_payload": {"secret": "sk-demo"},
                "checkpoint_payload": {"state": "hidden"},
            },
        )
    )
    resolver = RuntimeFlagResolver(test_overrides={POLISH_QUESTION_GRAPH_FLAG: True})

    result = run_polish_question_skeleton(context, context.command, flag_resolver=resolver)

    assert result.status == "skeleton_succeeded"
    assert len(result.output_refs) == 2
    assert result.output_refs[0].startswith("question_candidate_ref_")
    assert result.output_refs[1].startswith("question_result_ref_")
    assert result.trace_refs
    assert result.trace_refs[0].startswith("ackpt_")
    assert result.formal_refs == ()
    assert result.metadata["provider_calls"] == 0
    assert result.metadata["formal_business_writes"] == 0
    assert result.metadata["db_business_writes"] == 0
    assert result.metadata["checkpoint_refs_only"] is True
    assert result.metadata["checkpoint_refs_are_business_facts"] is False
    assert result.metadata["input_refs"] == context.command.input_refs
    assert result.metadata["requested_outputs"] == context.command.requested_outputs
    assert result.metadata["runtime_flag_source"] == "test_override"
    assert _metadata_has_forbidden_keys(result.metadata) is False
    assert "sk-demo" not in repr(result.metadata)


def test_application_layer_has_no_langgraph_import() -> None:
    violations = _find_forbidden_imports(
        APP_ROOT / "application",
        forbidden_prefixes=("langgraph", "langchain"),
    )

    assert violations == []


def _context(command: AgentCommandEnvelope | None = None) -> AgentRunContext:
    command = command or AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("session_ref_1",),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_pr5_question",
    )
    return AgentRunContext(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_pr5_question",
        ai_task_id="aitask_pr5_question",
        graph_name="polish_question_graph",
        graph_version="pr9-agent-orchestration",
        command=command,
    )


def _metadata_has_forbidden_keys(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key) in FORBIDDEN_METADATA_KEYS or _metadata_has_forbidden_keys(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set)):
        return any(_metadata_has_forbidden_keys(item) for item in value)
    return False


def _find_forbidden_imports(root: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    paths = [root] if root.is_file() else sorted(root.rglob("*.py"))
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            module_names: list[str] = []
            if isinstance(node, ast.Import):
                module_names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                module_names.append(node.module)
            for module_name in module_names:
                if module_name.startswith(forbidden_prefixes):
                    rel = path.relative_to(REPO_ROOT)
                    violations.append(f"{rel}: {module_name}")
    return violations
