from __future__ import annotations

import json

import app.api.v1.polish as polish_api
from app.application.polish.entities import PolishTaskStatus
from app.application.polish.feedback_application_service import _failed_feedback_payload_for_storage
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.refs import TraceRef


def _serialized(payload: object) -> str:
    return json.dumps(payload, default=str, ensure_ascii=False, sort_keys=True)


def test_failed_feedback_payload_contract_is_retryable_and_sanitized() -> None:
    payload = _failed_feedback_payload_for_storage(
        session_id="ses_failed_contract",
        question_id="que_failed_contract",
        answer_id="ans_failed_contract",
        feedback_id="fb_failed_contract",
        validation_errors=("llm_transport_generation_failed",),
        metadata={
            "provider_status": "failed",
            "llm_called": True,
            "provider_payload": {"secret": "provider_payload_should_not_render"},
            "raw_prompt": "raw_prompt_should_not_render",
            "raw_completion": "raw_completion_should_not_render",
            "raw_provider": "raw_provider_should_not_render",
        },
    )
    serialized = _serialized(payload)

    assert payload["status"] == "generation_failed"
    assert payload["retryable"] is True
    assert payload["user_visible_status"] == "反馈生成失败，可重试"
    assert payload["error"]["code"] == "llm_transport_generation_failed"
    assert payload["next_recommended_actions"] == ["retry_same_question", "continue_same_question"]
    assert payload["feedback_metadata"]["provider_status"] == "failed"
    assert payload["feedback_metadata"]["llm_called"] is True
    for forbidden in (
        "provider_payload_should_not_render",
        "raw_prompt_should_not_render",
        "raw_completion_should_not_render",
        "raw_provider_should_not_render",
    ):
        assert forbidden not in serialized


def test_feedback_generation_failed_task_response_aligns_status_and_display_contract() -> None:
    now = utc_now()
    task = PolishTaskStatus(
        ai_task_id="task_feedback_failed_contract",
        task_type="polish_feedback_generation",
        status=AiTaskStatus.GENERATION_FAILED,
        contract_ids=("P-POLISH-005",),
        retryable=True,
        result_ref=TraceRef(
            trace_ref_id="task_feedback_failed_contract",
            trace_type="validation_result",
            created_at=now,
        ),
        user_visible_status="反馈生成失败，可重试",
        validation_errors=("llm_transport_generation_failed",),
    )

    payload = polish_api._task_response(task)
    serialized = _serialized(payload)

    assert payload["status"] == AiTaskStatus.GENERATION_FAILED
    assert payload["retryable"] is True
    assert payload["user_visible_status"] == "反馈生成失败，可重试"
    assert payload["validation_errors"] == ["llm_transport_generation_failed"]
    assert "provider_payload" not in payload
    assert "raw_prompt" not in serialized
    assert "raw_completion" not in serialized
    assert "raw_provider" not in serialized
