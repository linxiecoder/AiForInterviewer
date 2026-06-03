from __future__ import annotations

from tests.architecture.test_application_boundary import API_ROOT, _forbidden_import_violations, _python_files


POLISH_POLICY_ROOT = API_ROOT / "app" / "domain" / "polish" / "policies"

DOMAIN_POLISH_POLICY_FORBIDDEN_IMPORTS = (
    "app.api",
    "app.infrastructure",
    "app.application.llm",
    "app.application.polish.question_generation_prompts",
    "app.application.polish.feedback_prompt_assets",
    "fastapi",
    "sqlalchemy",
    "langgraph",
    "openai",
    "anthropic",
    "cohere",
    "google.genai",
    "google.generativeai",
)


def test_domain_polish_policies_import_no_forbidden_dependencies() -> None:
    assert POLISH_POLICY_ROOT.exists()

    assert _forbidden_import_violations(
        _python_files(POLISH_POLICY_ROOT),
        DOMAIN_POLISH_POLICY_FORBIDDEN_IMPORTS,
    ) == []
