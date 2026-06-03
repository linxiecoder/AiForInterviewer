from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.test_application_boundary import (
    API_ROOT,
    _forbidden_import_violations,
    _imported_modules,
    _python_files,
    _relative,
)


POLISH_POLICY_ROOT = API_ROOT / "app" / "domain" / "polish" / "policies"
POLISH_APPLICATION_ROOT = API_ROOT / "app" / "application" / "polish"

PHASE3_DOMAIN_POLICY_FILES = {
    "answer_change_policy.py",
    "answer_coverage_policy.py",
    "asset_consistency_policy.py",
    "feedback_next_action_policy.py",
    "follow_up_coverage_policy.py",
    "question_grounding_policy.py",
    "source_support_policy.py",
}

PHASE3_APPLICATION_POLICY_BRIDGES = {
    "feedback_rules.py": (
        "app.domain.polish.policies.answer_change_policy",
        "app.domain.polish.policies.answer_coverage_policy",
        "app.domain.polish.policies.asset_consistency_policy",
        "app.domain.polish.policies.feedback_next_action_policy",
    ),
    "question_generation_service.py": (
        "app.domain.polish.policies.source_support_policy",
    ),
    "question_grounding.py": (
        "app.domain.polish.policies.question_grounding_policy",
    ),
    "use_cases.py": (
        "app.domain.polish.policies.follow_up_coverage_policy",
    ),
}

PHASE3_APPLICATION_POLICY_CALLS = {
    "feedback_rules.py": (
        "AnswerChangePolicy.evaluate",
        "AnswerCoveragePolicy.evaluate",
        "AssetConsistencyPolicy.evaluate",
        "FeedbackNextActionPolicy.decide",
    ),
    "question_generation_service.py": (
        "SourceSupportPolicy.classify_question_context",
    ),
    "question_grounding.py": (
        "QuestionGroundingPolicy.evaluate",
    ),
    "use_cases.py": (
        "FollowUpCoveragePolicy.decide",
    ),
}

PHASE3_THIN_POLICY_ADAPTERS = (
    POLISH_APPLICATION_ROOT / "feedback_rules.py",
    POLISH_APPLICATION_ROOT / "question_grounding.py",
)

DOMAIN_POLISH_POLICY_FORBIDDEN_IMPORTS = (
    "app.api",
    "app.infrastructure",
    "app.application.agents",
    "app.application.ai_provider",
    "app.application.ai_runtime",
    "app.application.llm",
    "app.application.polish.feedback_prompt_assets",
    "app.application.polish.progress_prompts",
    "app.application.polish.question_generation_prompts",
    "fastapi",
    "sqlalchemy",
    "alembic",
    "asyncpg",
    "psycopg",
    "langgraph",
    "openai",
    "anthropic",
    "cohere",
    "google.genai",
    "google.generativeai",
)

THIN_POLICY_ADAPTER_FORBIDDEN_IMPORTS = DOMAIN_POLISH_POLICY_FORBIDDEN_IMPORTS


def _imported_module_names(path: Path) -> set[str]:
    return {module_name for _, module_name in _imported_modules(path)}


def _called_attribute_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    called: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        value = node.func.value
        if isinstance(value, ast.Name):
            called.add(f"{value.id}.{node.func.attr}")
    return called


def test_phase3_domain_policy_files_are_present() -> None:
    assert POLISH_POLICY_ROOT.exists()

    present_files = {path.name for path in POLISH_POLICY_ROOT.glob("*.py")}

    assert sorted(PHASE3_DOMAIN_POLICY_FILES - present_files) == []


def test_phase3_application_bridges_import_domain_policies() -> None:
    missing: list[str] = []

    for relative_path, expected_imports in PHASE3_APPLICATION_POLICY_BRIDGES.items():
        bridge_path = POLISH_APPLICATION_ROOT / relative_path
        imported_modules = _imported_module_names(bridge_path)
        for expected_import in expected_imports:
            if expected_import not in imported_modules:
                missing.append(f"{_relative(bridge_path)} missing {expected_import}")

    assert missing == []


def test_phase3_application_bridges_call_domain_policy_entrypoints() -> None:
    missing: list[str] = []

    for relative_path, expected_calls in PHASE3_APPLICATION_POLICY_CALLS.items():
        bridge_path = POLISH_APPLICATION_ROOT / relative_path
        called_attributes = _called_attribute_names(bridge_path)
        for expected_call in expected_calls:
            if expected_call not in called_attributes:
                missing.append(f"{_relative(bridge_path)} missing {expected_call}")

    assert missing == []


def test_phase3_thin_policy_adapters_do_not_import_forbidden_runtime_boundaries() -> None:
    assert _forbidden_import_violations(
        PHASE3_THIN_POLICY_ADAPTERS,
        THIN_POLICY_ADAPTER_FORBIDDEN_IMPORTS,
    ) == []


def test_domain_polish_policies_import_no_forbidden_dependencies() -> None:
    assert POLISH_POLICY_ROOT.exists()

    assert _forbidden_import_violations(
        _python_files(POLISH_POLICY_ROOT),
        DOMAIN_POLISH_POLICY_FORBIDDEN_IMPORTS,
    ) == []
