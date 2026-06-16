from __future__ import annotations

import json
from types import SimpleNamespace

import app.api.v1.polish as polish_api
from app.application.polish.feedback_application_service import _failed_feedback_payload_for_storage
from app.domain.shared.clock import utc_now


FORBIDDEN_EXECUTION_AUTHORIZATION_KEYS = (
    "NextQuestionExecutionGrant",
    "next_question_execution_grant",
    "grant_id",
    "grant_token",
    "consumeGrant",
    "createGrant",
)


def test_pending_feedback_fallback_actions_are_display_only() -> None:
    answer = SimpleNamespace(
        answer_id="ans_pending_display_only",
        session_id="ses_pending_display_only",
        question_id="que_pending_display_only",
        feedback_id=None,
        feedback_payload=None,
        answer_created_at=utc_now(),
    )

    payload = polish_api._answer_feedback_payload(answer)

    assert payload["status"] == "pending"
    assert payload["feedback_metadata"]["pending_reason"] == "feedback_not_generated"
    assert payload["next_recommended_actions"] == list(polish_api.ANSWER_NEXT_RECOMMENDED_ACTIONS)
    serialized = json.dumps(payload, default=str, ensure_ascii=False, sort_keys=True)
    for forbidden in FORBIDDEN_EXECUTION_AUTHORIZATION_KEYS:
        assert forbidden not in serialized


def test_failed_feedback_fallback_actions_are_display_only() -> None:
    payload = _failed_feedback_payload_for_storage(
        session_id="ses_failed_display_only",
        question_id="que_failed_display_only",
        answer_id="ans_failed_display_only",
        feedback_id="trc_failed_display_only",
        validation_errors=("llm_transport_generation_failed",),
        metadata={"provider_status": "failed", "llm_called": True},
    )

    assert payload["status"] == "generation_failed"
    assert payload["next_recommended_actions"] == ["retry_same_question", "continue_same_question"]
    assert payload["feedback_metadata"]["llm_called"] is True
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden in FORBIDDEN_EXECUTION_AUTHORIZATION_KEYS:
        assert forbidden not in serialized
