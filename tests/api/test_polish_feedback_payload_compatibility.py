from __future__ import annotations

import json
from types import SimpleNamespace

import app.api.v1.polish as polish_api
from app.application.polish.entities import PolishAnswer, PolishFeedback, PolishTaskStatus
from app.application.polish.feedback_application_service import _failed_feedback_payload_for_storage
from app.application.polish.use_cases import _to_session_answer_detail
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.refs import ResourceRef, TraceRef
from app.infrastructure.db.repositories.ai_tasks import _result_projection


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


def test_ai_task_result_projection_preserves_feedback_result_payload_compatibility() -> None:
    now = utc_now()
    task = SimpleNamespace(
        id="ait_feedback_result_payload_compat",
        task_type="polish_feedback_generation",
        status="succeeded",
        trace_ref_ids=[],
        created_at=now,
    )
    result = SimpleNamespace(
        status="succeeded",
        result_ref_id="feedback_result_payload_compat",
        validation_result_ref_id=None,
        trace_ref_id="trace_feedback_result_payload_compat",
        created_at=now,
    )
    projected = _result_projection(
        task,
        result=result,
        payload={
            "status": "generated",
            "feedback_text": "结构化反馈仍通过 result_payload 暴露给旧客户端。",
            "score_result": {"score_value": 82, "score_type": "polish_answer"},
            "feedback_metadata": {
                "candidate_ref": "feedback_candidate_safe",
                "asset_update_candidate_refs": ["asset_candidate_safe"],
            },
            "suggestion_refs": [
                {"resource_type": "feedback_suggestion", "resource_id": "retry_same_question"}
            ],
            "validation_errors": [],
            "provider_payload": {"completion": "must_not_leak"},
            "raw_prompt": "must_not_leak",
        },
    )

    assert projected["result_payload"]["status"] == "generated"
    assert projected["result_payload"]["feedback_text"] == "结构化反馈仍通过 result_payload 暴露给旧客户端。"
    assert projected["result_payload"]["score_result"]["score_value"] == 82
    assert projected["candidate_refs"] == [
        {"resource_type": "feedback_candidate", "resource_id": "feedback_candidate_safe"},
        {"resource_type": "asset_update_candidate", "resource_id": "asset_candidate_safe"},
    ]
    assert projected["suggestion_refs"] == [
        {"resource_type": "feedback_suggestion", "resource_id": "retry_same_question"}
    ]
    assert projected["provider_payload"] is None
    serialized = _serialized(projected)
    assert "raw_prompt" not in serialized
    assert "provider_payload" in projected
    assert "must_not_leak" not in serialized


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
    assert "next_recommended_actions" not in payload
    assert payload["feedback_payload"]["next_recommended_actions"] == ["continue_same_question"]
    assert "feedback_summary" not in payload["feedback_payload"]
    assert "raw_prompt" not in payload["feedback_payload"]
    assert "provider_payload" not in payload["feedback_payload"]
    _assert_no_grant_client_fields(payload)


def test_feedback_post_response_uses_active_feedback_contract_top_level() -> None:
    now = utc_now()
    task = PolishTaskStatus(
        ai_task_id="ait_feedback_contract_top_level",
        task_type="polish_feedback_generation",
        status=AiTaskStatus.SUCCEEDED,
        contract_ids=("P-POLISH-005",),
        retryable=False,
        result_ref=TraceRef(trace_ref_id="fb_contract_top_level", trace_type="feedback", created_at=now),
        user_visible_status="反馈已生成",
        candidate_refs=(
            ResourceRef(resource_type="feedback_candidate", resource_id="feedback_candidate_contract"),
        ),
    )
    answer = SimpleNamespace(
        answer_id="ans_feedback_contract_top_level",
        answer_round=1,
        answer_text="回答正文。",
        answer_created_at=now,
        session_id="ses_feedback_contract_top_level",
        question_id="que_feedback_contract_top_level",
        feedback_id="fb_contract_top_level",
        score_result_id="score_contract_top_level",
        feedback_created_at=now,
        feedback_payload={
            "status": "generated",
            "feedback_id": "fb_contract_top_level",
            "feedback_text": "契约点评摘要。",
            "score_result": {"score_value": 88, "score_type": "polish_answer"},
            "loss_points": [
                {"loss_point_id": "loss_contract_1", "reason": "缺少失败补偿。"},
                {"id": "loss_contract_2", "reason": "缺少指标。"},
                {"reason": "无稳定引用的旧失分点。"},
            ],
            "reference_answer": {"sections": []},
            "next_recommended_actions": ["continue_same_question"],
            "low_confidence_flags": [],
            "trace_refs": [{"trace_ref_id": "trace_contract_top_level"}],
        },
    )

    payload = polish_api._feedback_response(
        task,
        answer,
        session_id=answer.session_id,
        question_id=answer.question_id,
    )

    assert payload["summary"] == "契约点评摘要。"
    assert payload["score_ref"] == "score_contract_top_level"
    assert payload["loss_point_refs"] == ["loss_contract_1", "loss_contract_2"]
    assert payload["candidate_refs"] == [
        {"resource_type": "feedback_candidate", "resource_id": "feedback_candidate_contract"}
    ]
    assert payload["feedback_payload"]["next_recommended_actions"] == ["continue_same_question"]
    assert "next_recommended_actions" not in payload
    assert "feedback_text" not in payload
    assert "score_result" not in payload
    assert "score_result_id" not in payload
    assert "low_confidence_flags" not in payload
    assert "trace_refs" not in payload


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
    assert "next_recommended_actions" not in payload
    assert payload["feedback_payload"]["next_recommended_actions"] == ["continue_same_question"]
    assert "feedback_summary" not in payload["feedback_payload"]
    _assert_no_grant_client_fields(payload)


def test_api_top_level_next_recommended_actions_mirror_is_removed() -> None:
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
                "display_owner": "feedback_payload",
                "authorization_owner": "backend_application_grant",
            },
        },
    )

    payload = polish_api._session_answer_payload(
        answer,
        session_id=answer.session_id,
        question_id=answer.question_id,
    )

    assert "next_recommended_actions" not in payload
    assert payload["feedback_payload"]["next_recommended_actions"] == ["retry_same_question", "continue_same_question"]
    assert payload["feedback_payload"]["feedback_metadata"]["display_owner"] == "feedback_payload"
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


def test_failure_payload_projection_keeps_stage_diagnostics_out_of_feedback_metadata() -> None:
    payload = _failed_feedback_payload_for_storage(
        session_id="ses_failed_stage_diagnostics",
        question_id="que_failed_stage_diagnostics",
        answer_id="ans_failed_stage_diagnostics",
        feedback_id="fb_failed_stage_diagnostics",
        validation_errors=("json_projection", "feedback_status_invalid"),
        metadata={
            "provider_status": "failed",
            "llm_called": True,
            "stage": "json_projection",
            "finish_reason": "stop",
            "completion_tokens": 320,
            "reasoning_tokens": 0,
            "generation_stages": [
                {"stage": "analysis_candidate", "finish_reason": "stop", "completion_tokens": 900},
                {"stage": "json_projection", "failure_reason": "json_projection", "completion_tokens": 320},
            ],
        },
    )

    assert payload["status"] == "generation_failed"
    assert payload["error"]["code"] == "json_projection"
    assert payload["error"]["metadata"]["stage"] == "json_projection"
    assert payload["error"]["metadata"]["completion_tokens"] == 320
    assert "generation_stages" not in payload["feedback_metadata"]
    assert payload["next_recommended_actions"] == ["retry_same_question", "continue_same_question"]
    _assert_no_grant_client_fields(payload)
