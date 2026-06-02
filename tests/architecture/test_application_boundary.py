from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPO_ROOT / "apps" / "api"
APP_ROOT = API_ROOT / "app"
DOMAIN_ROOT = APP_ROOT / "domain"
POLISH_ROOT = APP_ROOT / "application" / "polish"

DOMAIN_FORBIDDEN_IMPORTS = (
    "app.api",
    "app.infrastructure",
    "app.application.llm",
    "app.application.polish.feedback_prompt_assets",
    "app.application.polish.progress_prompts",
    "app.application.polish.question_generation_prompts",
    "fastapi",
    "sqlalchemy",
    "alembic",
    "langgraph",
    "openai",
    "anthropic",
)

FOCUSED_POLISH_SERVICE_FORBIDDEN_IMPORTS = (
    "app.api",
    "app.infrastructure",
    "app.application.agents",
    "app.application.ai_runtime",
    "app.application.llm",
    "app.application.polish.feedback_prompt_assets",
    "app.application.polish.progress_prompts",
    "app.application.polish.question_generation_prompts",
    "fastapi",
    "sqlalchemy",
    "alembic",
    "langgraph",
    "openai",
    "anthropic",
)


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts))


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(API_ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _package_name(path: Path) -> str:
    module_name = _module_name(path)
    if path.stem == "__init__":
        return module_name
    return ".".join(module_name.split(".")[:-1])


def _resolve_import_from(path: Path, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module

    current_package_parts = _package_name(path).split(".")
    base_parts = current_package_parts[: len(current_package_parts) - (node.level - 1)]
    module_parts = node.module.split(".") if node.module else []
    return ".".join((*base_parts, *module_parts)) if base_parts or module_parts else None


def _imported_modules(path: Path) -> tuple[tuple[int, str], ...]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = _resolve_import_from(path, node)
            if module:
                imports.append((node.lineno, module))
        elif isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name) for alias in node.names)
    return tuple(imports)


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _forbidden_import_violations(paths: tuple[Path, ...], forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    for path in paths:
        for lineno, module_name in _imported_modules(path):
            if any(module_name == prefix or module_name.startswith(f"{prefix}.") for prefix in forbidden_prefixes):
                violations.append(f"{_relative(path)}:{lineno}: {module_name}")
    return violations


def test_domain_layer_has_no_infra_api_db_llm_provider_or_prompt_imports() -> None:
    assert DOMAIN_ROOT.exists()

    assert _forbidden_import_violations(_python_files(DOMAIN_ROOT), DOMAIN_FORBIDDEN_IMPORTS) == []


def test_focused_polish_application_services_do_not_import_prompt_provider_db_api_runtime_or_agents() -> None:
    focused_service_paths = tuple(sorted(POLISH_ROOT.glob("*_application_service.py")))

    assert focused_service_paths
    assert _forbidden_import_violations(
        focused_service_paths,
        FOCUSED_POLISH_SERVICE_FORBIDDEN_IMPORTS,
    ) == []
