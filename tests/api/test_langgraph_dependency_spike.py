from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "api" / "app"
ALLOWED_IMPORT_PATHS = {
    Path("tests/api/test_langgraph_dependency_spike.py"),
}
ALLOWED_IMPORT_PREFIX = Path("apps/api/app/infrastructure/ai_runtime/langgraph")
FORBIDDEN_IMPORT_ROOTS = (
    APP_ROOT / "application",
    APP_ROOT / "core",
    APP_ROOT / "domain",
    APP_ROOT / "api",
)


def test_pr4_lg_dep_spike_compiles_invokes_and_keeps_boundary() -> None:
    langgraph = importlib.import_module("langgraph")
    spike_module = importlib.import_module("app.infrastructure.ai_runtime.langgraph.dependency_spike")

    result = spike_module.run_dependency_spike()

    assert langgraph is not None
    assert result == {
        "graph_name": "pr4_lg_dep_fake_graph",
        "topic": "dependency-spike",
        "steps": ["compiled", "invoked"],
        "provider_calls": 0,
        "db_writes": 0,
        "formal_business_writes": 0,
    }
    assert "openai" not in sys.modules
    assert "anthropic" not in sys.modules
    assert _requirements_keep_spike_dependencies_pinned_and_provider_free()
    assert _business_graph_directories() == []
    assert _concrete_lang_import_violations() == []
    assert _forbidden_layer_lang_imports() == []


def _requirements_keep_spike_dependencies_pinned_and_provider_free() -> bool:
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    normalized = [line.strip().lower() for line in requirements if line.strip()]
    return (
        normalized.count("langgraph==1.2.1") == 1
        and not _has_direct_requirement(normalized, "langchain-core")
        and not _has_direct_requirement(normalized, "langgraph-checkpoint")
        and not _has_direct_requirement(normalized, "openai")
        and not _has_direct_requirement(normalized, "anthropic")
    )


def _has_direct_requirement(requirements: list[str], package_name: str) -> bool:
    normalized_name = package_name.lower()
    return any(
        line == normalized_name
        or line.startswith(
            (
                f"{normalized_name}==",
                f"{normalized_name}>=",
                f"{normalized_name}<=",
                f"{normalized_name}~=",
                f"{normalized_name}!=",
                f"{normalized_name}>",
                f"{normalized_name}<",
                f"{normalized_name}[",
                f"{normalized_name} ",
            )
        )
        for line in requirements
    )


def _business_graph_directories() -> list[str]:
    return [
        str(path.relative_to(REPO_ROOT))
        for path in sorted(APP_ROOT.rglob("business_graphs"))
        if path.is_dir()
    ]


def _concrete_lang_import_violations() -> list[str]:
    violations: list[str] = []
    for path in _python_files(APP_ROOT, REPO_ROOT / "tests" / "api"):
        rel = path.relative_to(REPO_ROOT)
        if rel in ALLOWED_IMPORT_PATHS or _is_under(rel, ALLOWED_IMPORT_PREFIX):
            continue
        for module_name in _imported_modules(path):
            if _is_langgraph_or_langchain(module_name):
                violations.append(f"{rel}: {module_name}")
    return violations


def _forbidden_layer_lang_imports() -> list[str]:
    violations: list[str] = []
    for root in FORBIDDEN_IMPORT_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            for module_name in _imported_modules(path):
                if _is_langgraph_or_langchain(module_name):
                    violations.append(f"{path.relative_to(REPO_ROOT)}: {module_name}")
    return violations


def _python_files(*roots: Path) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
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
