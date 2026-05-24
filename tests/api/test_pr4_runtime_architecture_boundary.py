from __future__ import annotations

import ast
from pathlib import Path

from app.application.ai_runtime.contracts import AgentCommandEnvelope, AgentRunContext
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.langgraph.fake_runtime import FakeLangGraphRuntime


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "api" / "app"
ALLOWED_LANG_IMPORT_PREFIX = Path("apps/api/app/infrastructure/ai_runtime/langgraph")
ALLOWED_TEST_IMPORTS = {
    Path("tests/api/test_langgraph_dependency_spike.py"),
    Path("tests/api/test_pr4_runtime_architecture_boundary.py"),
}


def test_pr4_concrete_langgraph_imports_do_not_leak_outside_infra_runtime_root() -> None:
    assert _concrete_lang_import_violations() == []


def test_pr4_no_business_graph_directory_or_formal_business_write_bypass() -> None:
    assert not (APP_ROOT / "application" / "ai_runtime" / "business_graphs").exists()
    runtime = FakeLangGraphRuntime(
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
        ),
    )

    result = runtime.start(context, context.command)

    assert result.formal_refs == ()
    assert result.metadata["formal_business_writes"] == 0
    assert result.metadata["db_business_writes"] == 0


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
