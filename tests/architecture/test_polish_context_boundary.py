from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPO_ROOT / "apps" / "api"
POLISH_CONTEXT_ROOT = API_ROOT / "app" / "application" / "polish" / "context"

CONTEXT_FORBIDDEN_IMPORTS = (
    "app.api",
    "app.infrastructure",
    "app.application.llm",
    "app.application.polish.feedback_prompt_assets",
    "app.application.polish.question_generation_prompts",
    "app.application.polish.question_grounding",
    "fastapi",
    "sqlalchemy",
    "alembic",
    "langgraph",
    "openai",
    "anthropic",
)


def test_polish_context_layer_does_not_import_prompt_provider_db_api_or_runtime_boundaries() -> None:
    assert POLISH_CONTEXT_ROOT.exists()

    violations: list[str] = []
    for path in sorted(POLISH_CONTEXT_ROOT.glob("*.py")):
        for lineno, module_name in _imported_modules(path):
            if any(module_name == prefix or module_name.startswith(f"{prefix}.") for prefix in CONTEXT_FORBIDDEN_IMPORTS):
                violations.append(f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}: {module_name}")

    assert violations == []


def _imported_modules(path: Path) -> tuple[tuple[int, str], ...]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.lineno, _resolve_import_from(path, node)))
        elif isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name) for alias in node.names)
    return tuple(imports)


def _resolve_import_from(path: Path, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    package = _package_name(path)
    current_package_parts = package.split(".") if package else []
    base_parts = current_package_parts[: len(current_package_parts) - (node.level - 1)]
    module_parts = node.module.split(".") if node.module else []
    return ".".join((*base_parts, *module_parts))


def _package_name(path: Path) -> str:
    parts = list(path.relative_to(API_ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    module_name = ".".join(parts)
    if path.stem == "__init__":
        return module_name
    return ".".join(module_name.split(".")[:-1])
