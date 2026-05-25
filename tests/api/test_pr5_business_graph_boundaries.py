from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "api" / "app"
BUSINESS_GRAPH_ROOT = APP_ROOT / "application" / "ai_runtime" / "business_graphs"


def test_pr5_adds_only_polish_business_graph_files() -> None:
    assert BUSINESS_GRAPH_ROOT.exists()
    assert sorted(path.name for path in BUSINESS_GRAPH_ROOT.glob("*.py")) == [
        "__init__.py",
        "polish_feedback_graph.py",
        "polish_question_graph.py",
    ]


def test_pr5_business_graphs_do_not_import_concrete_runtime_or_providers() -> None:
    violations = _find_forbidden_imports(
        BUSINESS_GRAPH_ROOT,
        forbidden_prefixes=(
            "langgraph",
            "langchain",
            "openai",
            "anthropic",
            "sqlalchemy",
            "fastapi",
            "app.infrastructure",
        ),
    )

    assert violations == []


def test_pr5_business_graph_has_no_provider_call_or_api_key_path() -> None:
    forbidden_markers = (
        "openai",
        "anthropic",
        "api_key",
        "provider.invoke",
        "provider.call",
        "chat.completions",
        "responses.create",
    )
    source = "\n".join(path.read_text(encoding="utf-8").lower() for path in BUSINESS_GRAPH_ROOT.glob("*.py"))

    assert [marker for marker in forbidden_markers if marker in source] == []


def test_pr5_business_graph_boundary_keeps_application_core_domain_api_concrete_free() -> None:
    concrete_runtime = "lang" + "graph"
    concrete_chain = "lang" + "chain"

    assert _find_forbidden_imports(
        BUSINESS_GRAPH_ROOT,
        forbidden_prefixes=(concrete_runtime, concrete_chain),
    ) == []
    assert _find_forbidden_imports(
        APP_ROOT / "application",
        forbidden_prefixes=(concrete_runtime, concrete_chain),
    ) == []
    assert _find_forbidden_imports(
        APP_ROOT / "domain",
        forbidden_prefixes=(concrete_runtime, concrete_chain),
    ) == []
    assert _find_forbidden_imports(
        APP_ROOT / "api",
        forbidden_prefixes=(concrete_runtime, concrete_chain),
    ) == []


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
