from __future__ import annotations

import json
from types import SimpleNamespace

import app.api.v1.polish as polish_api
from app.application.polish.entities import PolishAnswer, PolishFeedback
from app.application.polish.feedback_application_service import _failed_feedback_payload_for_storage
from app.application.polish.use_cases import _to_session_answer_detail
from app.domain.shared.clock import utc_now


FORBIDDEN_GRANT_CLIENT_KEYS = (
    "NextQuestionExecutionGrant",
    "next_question_execution_grant",
    "grant_id",
    "grant_token",
    "grantId",
    "consumeGrant",
    "createGrant",
)


def _serialized(payload: object) -> str:
    return json.dumps(payload, default=str, ensure_ascii=False, sort_keys=True)


def _assert_no_grant_client_fields(payload: object) -> None:
    serialized = _serialized(payload)
    for forbidden in FORBIDDEN_GRANT_CLIENT_KEYS:
        assert forbidden not in serialized


def test_old_generated_feedback_payload_remains_display_compatible() -> None:
    answer = SimpleNamespace(
        answer_id="ans_old_payload_display",
        answer_round=2,
        answer_text="旧回答正文仍可展示。",
        answer_created_at=utc_now(),
        session_id="ses_old_payload_display",
        question_id="que_old_payload_display",
        feedback_id="fb_old_payload_display",
        score_result_id="score_old_payload_display",
        feedback_created_at=utc_now(),
        feedback_payload={
            "status": "generated",
            "feedback_id": "fb_old_payload_display",
            "feedback_text": "旧版 feedback_summary 映射出的用户可见反馈。",
            "score_result": {"score_value": 76, "score_type": "polish_answer"},
            "loss_points": [{"title": "旧失分点", "reason": "旧 payload 失分原因。"}],
            "reference_answer": {"summary": "旧参考回答摘要。"},
            "next_recommended_actions": ["continue_same_question"],
            "raw_prompt": "raw_prompt_should_not_render",
            "provider_payload": "provider_payload_should_not_render",
        },
    )

    payload = polish_api._session_answer_payload(
        answer,
        session_id=answer.session_id,
        question_id=answer.question_id,
    )

    assert payload["feedback_text"] == "旧版 feedback_summary 映射出的用户可见反馈。"
    assert payload["feedback_payload"]["feedback_text"] == payload["feedback_text"]
    assert payload["feedback_payload"]["score_result"]["score_value"] == 76
    assert payload["feedback_payload"]["loss_points"][0]["title"] == "旧失分点"
    assert payload["feedback_payload"]["reference_answer"]["summary"] == "旧参考回答摘要。"
    assert payload["next_recommended_actions"] == ["continue_same_question"]
    assert payload["next_recommended_actions"] == payload["feedback_payload"]["next_recommended_actions"]
    assert "feedback_summary" not in payload["feedback_payload"]
    assert "raw_prompt" not in payload["feedback_payload"]
    assert "provider_payload" not in payload["feedback_payload"]
    _assert_no_grant_client_fields(payload)


def test_legacy_feedback_summary_json_renders_as_feedback_text_response() -> None:
    now = utc_now()
    answer = PolishAnswer(
        answer_id="ans_legacy_summary_json",
        owner_id="usr_legacy_summary_json",
        actor_id="usr_legacy_summary_json",
        session_id="ses_legacy_summary_json",
        question_id="que_legacy_summary_json",
        answer_round=1,
        answer_text="旧回答正文。",
        status="submitted",
        created_at=now,
        updated_at=now,
    )
    feedback = PolishFeedback(
        feedback_id="fb_legacy_summary_json",
        owner_id="usr_legacy_summary_json",
        actor_id="usr_legacy_summary_json",
        session_id="ses_legacy_summary_json",
        answer_id="ans_legacy_summary_json",
        ai_task_id="task_legacy_summary_json",
        score_result_id=None,
        feedback_summary=json.dumps(
            {
                "status": "generated",
                "feedback_summary": "旧 feedback_summary JSON 仍应作为用户可见反馈展示。",
                "score_result": {"score_value": 69, "score_type": "polish_answer"},
                "loss_points": [],
                "reference_answer": None,
                "next_recommended_actions": ["continue_same_question"],
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        status="generated",
        created_at=now,
        updated_at=now,
    )

    detail = _to_session_answer_detail(answer=answer, feedback=feedback)
    payload = polish_api._session_answer_payload(
        detail,
        session_id=answer.session_id,
        question_id=answer.question_id,
    )

    assert detail.feedback_text == "旧 feedback_summary JSON 仍应作为用户可见反馈展示。"
    assert payload["feedback_text"] == "旧 feedback_summary JSON 仍应作为用户可见反馈展示。"
    assert payload["feedback_payload"]["feedback_text"] == payload["feedback_text"]
    assert payload["next_recommended_actions"] == ["continue_same_question"]
    assert "feedback_summary" not in payload["feedback_payload"]
    _assert_no_grant_client_fields(payload)


def test_api_top_level_next_recommended_actions_is_display_mirror_only() -> None:
    answer = SimpleNamespace(
        answer_id="ans_top_level_actions_display",
        answer_round=1,
        answer_text="回答正文。",
        answer_created_at=utc_now(),
        session_id="ses_top_level_actions_display",
        question_id="que_top_level_actions_display",
        feedback_id="fb_top_level_actions_display",
        score_result_id=None,
        feedback_created_at=utc_now(),
        feedback_payload={
            "status": "generated",
            "feedback_id": "fb_top_level_actions_display",
            "feedback_text": "展示反馈。",
            "next_recommended_actions": ["retry_same_question", "continue_same_question"],
            "feedback_metadata": {
                "display_owner": "api_response_mirror",
                "authorization_owner": "backend_application_grant",
            },
        },
    )

    payload = polish_api._session_answer_payload(
        answer,
        session_id=answer.session_id,
        question_id=answer.question_id,
    )

    assert payload["next_recommended_actions"] == ["retry_same_question", "continue_same_question"]
    assert payload["next_recommended_actions"] is not payload["feedback_payload"]["next_recommended_actions"]
    assert payload["next_recommended_actions"] == payload["feedback_payload"]["next_recommended_actions"]
    assert payload["feedback_payload"]["feedback_metadata"]["display_owner"] == "api_response_mirror"
    _assert_no_grant_client_fields(payload)


def test_pending_feedback_actions_remain_display_only_without_execution_grant() -> None:
    answer = SimpleNamespace(
        answer_id="ans_pending_payload_compat",
        answer_round=1,
        answer_text="回答等待反馈。",
        answer_created_at=utc_now(),
        session_id="ses_pending_payload_compat",
        question_id="que_pending_payload_compat",
        feedback_id=None,
        feedback_payload=None,
    )

    payload = polish_api._answer_feedback_payload(answer)

    assert payload["status"] == "pending"
    assert payload["feedback_metadata"]["pending_reason"] == "feedback_not_generated"
    assert payload["next_recommended_actions"] == list(polish_api.ANSWER_NEXT_RECOMMENDED_ACTIONS)
    _assert_no_grant_client_fields(payload)


def test_failed_feedback_actions_remain_display_only_without_execution_grant() -> None:
    payload = _failed_feedback_payload_for_storage(
        session_id="ses_failed_payload_compat",
        question_id="que_failed_payload_compat",
        answer_id="ans_failed_payload_compat",
        feedback_id="fb_failed_payload_compat",
        validation_errors=("provider_timeout",),
        metadata={"provider_status": "failed", "llm_called": True},
    )

    assert payload["status"] == "generation_failed"
    assert payload["next_recommended_actions"] == ["retry_same_question", "continue_same_question"]
    assert payload["feedback_metadata"]["llm_called"] is True
    _assert_no_grant_client_fields(payload)
