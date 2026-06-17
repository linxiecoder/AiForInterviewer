from __future__ import annotations

from app.application.polish.feedback_agent import (
    FEEDBACK_GENERATION_MAX_TOKENS,
    FeedbackGenerationAgent,
)
from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset
from tests.api.test_ai_runtime_token_budget import _SettingsRecordingTransport, _feedback_context


def test_feedback_llm_budget_is_carried_on_request_not_transport_settings() -> None:
    transport = _SettingsRecordingTransport()

    FeedbackGenerationAgent(transport=transport).invoke_provider_v1(
        prompt_asset=build_feedback_prompt_asset(_feedback_context()),
        input_refs=("answer_001",),
    )

    assert transport.request_max_tokens == [FEEDBACK_GENERATION_MAX_TOKENS]
    assert transport.settings_max_tokens_during_generate == [8000]
