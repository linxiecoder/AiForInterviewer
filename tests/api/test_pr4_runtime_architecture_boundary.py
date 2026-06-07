from __future__ import annotations

import ast
from pathlib import Path

from app.application.agents.contracts import P8_REQUIRED_RUNTIME_STOP_CONDITIONS
from app.application.ai_runtime.contracts import AgentCommandEnvelope, AgentRunContext
from app.application.ai_runtime.business_graphs.polish_question_graph import (
    POLISH_QUESTION_GRAPH_NAME,
    POLISH_QUESTION_GRAPH_VERSION,
)
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.langgraph.in_memory_runtime import InMemoryLangGraphRuntime
from app.infrastructure.ai_runtime.langgraph.polish_question_runtime import PolishQuestionGraphRuntime


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "api" / "app"
ALLOWED_LANG_IMPORT_PREFIX = Path("apps/api/app/infrastructure/ai_runtime/langgraph")
BUSINESS_GRAPH_ROOT = APP_ROOT / "application" / "ai_runtime" / "business_graphs"
ALLOWED_PR5_BUSINESS_GRAPH_FILES = {
    BUSINESS_GRAPH_ROOT / "__init__.py",
    BUSINESS_GRAPH_ROOT / "local_multi_agent_orchestrator.py",
    BUSINESS_GRAPH_ROOT / "polish_feedback_graph.py",
    BUSINESS_GRAPH_ROOT / "polish_question_graph.py",
}
ALLOWED_TEST_IMPORTS = {
    Path("tests/api/test_langgraph_dependency_spike.py"),
    Path("tests/api/test_pr4_runtime_architecture_boundary.py"),
}
FORBIDDEN_BUSINESS_GRAPH_IMPORT_PREFIXES = (
    "langgraph",
    "langchain",
    "openai",
    "anthropic",
    "sqlalchemy",
    "fastapi",
    "app.infrastructure",
)
FORBIDDEN_BUSINESS_GRAPH_SOURCE_MARKERS = (
    "openai",
    "anthropic",
    "api_key",
    "provider.invoke",
    "provider.call",
    "chat.completions",
    "responses.create",
)


def test_pr4_concrete_langgraph_imports_do_not_leak_outside_infra_runtime_root() -> None:
    assert _concrete_lang_import_violations() == []


def test_pr4_pr5_boundary_allows_only_authorized_skeleton_and_no_formal_write_bypass() -> None:
    assert _business_graph_skeleton_boundary_violations() == []

    runtime = InMemoryLangGraphRuntime(
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True}
        )
    )
    context = AgentRunContext(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_arch",
        ai_task_id="aitask_arch",
        graph_name="pr4_fake_runtime",
        graph_version="pr4",
        command=AgentCommandEnvelope(
            entrypoint="start",
            input_refs=("input_ref_1",),
            requested_outputs=("candidate_refs",),
            idempotency_key="idem_arch",
            metadata={"runtime_loop_policy": _runtime_loop_policy_metadata()},
        ),
    )

    result = runtime.start(context, context.command)

    assert result.formal_refs == ()
    assert result.metadata["formal_business_writes"] == 0
    assert result.metadata["db_business_writes"] == 0


def test_polish_question_provider_draft_boundary_lives_in_dedicated_runtime() -> None:
    assert not hasattr(InMemoryLangGraphRuntime, "_polish_question_provider_draft")
    assert hasattr(PolishQuestionGraphRuntime, "_polish_question_provider_draft")


def test_in_memory_runtime_delegates_polish_question_start_to_dedicated_runtime() -> None:
    delegate = _RecordingPolishQuestionRuntime()
    runtime = InMemoryLangGraphRuntime(
        flag_resolver=RuntimeFlagResolver(
            test_overrides={
                "AIFI_AI_RUNTIME_ENABLED": True,
                "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True,
            }
        ),
        polish_question_runtime=delegate,
    )
    command = AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("session_ref_1", "progress_node_ref_1"),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_polish_question_delegate",
    )
    context = AgentRunContext(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_polish_question_delegate",
        ai_task_id="aitask_polish_question_delegate",
        graph_name=POLISH_QUESTION_GRAPH_NAME,
        graph_version=POLISH_QUESTION_GRAPH_VERSION,
        command=command,
    )

    result = runtime.start(context, command)

    assert result.run_id == context.run_id
    assert delegate.calls == [(context, command)]


def _business_graph_skeleton_boundary_violations() -> list[str]:
    if not BUSINESS_GRAPH_ROOT.exists():
        return []

    violations: list[str] = []
    business_graph_files = set(_python_files(BUSINESS_GRAPH_ROOT))
    unauthorized_files = business_graph_files - ALLOWED_PR5_BUSINESS_GRAPH_FILES
    violations.extend(
        f"unexpected business graph file: {path.relative_to(REPO_ROOT)}" for path in unauthorized_files
    )

    for path in sorted(business_graph_files & ALLOWED_PR5_BUSINESS_GRAPH_FILES):
        rel = path.relative_to(REPO_ROOT)
        for module_name in _imported_modules(path):
            if module_name.startswith(FORBIDDEN_BUSINESS_GRAPH_IMPORT_PREFIXES):
                violations.append(f"{rel}: forbidden import {module_name}")

        source = path.read_text(encoding="utf-8-sig").lower()
        for marker in FORBIDDEN_BUSINESS_GRAPH_SOURCE_MARKERS:
            if marker in source:
                violations.append(f"{rel}: forbidden provider marker {marker}")

    return sorted(violations)


def _concrete_lang_import_violations() -> list[str]:
    violations: list[str] = []
    for path in _python_files(APP_ROOT, REPO_ROOT / "tests" / "api"):
        rel = path.relative_to(REPO_ROOT)
        if _is_under(rel, ALLOWED_LANG_IMPORT_PREFIX) or rel in ALLOWED_TEST_IMPORTS:
            continue
        for module_name in _imported_modules(path):
            if _is_langgraph_or_langchain(module_name):
                violations.append(f"{rel}: {module_name}")
    return violations


def _runtime_loop_policy_metadata() -> dict[str, object]:
    return {
        "max_steps": 8,
        "max_retries": 1,
        "timeout_seconds": 30,
        "stop_conditions": P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
        "allowed_tools": ("generic_runtime_tool",),
        "allowed_callers": ("generic_runtime",),
        "side_effect_policy": "candidate_write",
    }


def _python_files(*roots: Path) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        if root.exists():
            paths.extend(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)
    return sorted(paths)


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def _is_langgraph_or_langchain(module_name: str) -> bool:
    return (
        module_name == "langgraph"
        or module_name.startswith("langgraph.")
        or module_name == "langchain"
        or module_name.startswith("langchain.")
    )


def _is_under(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


class _RecordingPolishQuestionRuntime:
    def __init__(self) -> None:
        self.calls: list[tuple[AgentRunContext, AgentCommandEnvelope]] = []

    def start(self, context: AgentRunContext, command: AgentCommandEnvelope):
        from app.application.ai_runtime.contracts import AgentRunResult

        self.calls.append((context, command))
        return AgentRunResult(run_id=context.run_id, status="delegated")
