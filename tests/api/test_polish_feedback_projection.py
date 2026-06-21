from __future__ import annotations

import json
from types import SimpleNamespace

from app.domain.shared.clock import utc_now
from app.infrastructure.db.repositories.ai_tasks import _result_projection


def _serialized(value: object) -> str:
    return json.dumps(value, default=str, ensure_ascii=False, sort_keys=True)


def test_response_safe_feedback_projection_contains_legacy_mapping_and_sanitizer() -> None:
    from app.application.polish.feedback_projection import response_safe_feedback_payload

    projected = response_safe_feedback_payload(
        {
            "status": "generated",
            "feedback_summary": "旧版 summary 仍应成为用户可见反馈。",
            "score_result": {"score_value": 78},
            "loss_points": [{"title": "旧失分点", "reason": "缺少恢复边界。"}],
            "reference_answer": {"summary": "旧参考答案。"},
            "next_recommended_actions": ["continue_same_question"],
            "raw_prompt": "must_not_leak",
            "provider_payload": {"completion": "must_not_leak"},
            "unknown_success_field": "must_not_be_contract",
        }
    )

    assert projected["feedback_text"] == "旧版 summary 仍应成为用户可见反馈。"
    assert projected["score_result"] == {"score_value": 78}
    assert projected["loss_points"] == [{"title": "旧失分点", "reason": "缺少恢复边界。"}]
    assert projected["reference_answer"] == {"summary": "旧参考答案。"}
    assert projected["next_recommended_actions"] == ["continue_same_question"]
    assert "feedback_summary" not in projected
    assert "unknown_success_field" not in projected
    serialized = _serialized(projected)
    assert "raw_prompt" not in serialized
    assert "provider_payload" not in serialized
    assert "must_not_leak" not in serialized


def test_pending_feedback_projection_is_canonical_and_display_only() -> None:
    from app.application.polish.feedback_projection import pending_feedback_payload

    projected = pending_feedback_payload(
        answer_id="answer_pending_projection",
        session_id="session_pending_projection",
        question_id="question_pending_projection",
        feedback_id=None,
        trace_refs=[],
    )

    assert projected["status"] == "pending"
    assert projected["feedback_text"] == "本轮反馈尚未生成"
    assert projected["next_recommended_actions"] == ["answer_again", "continue_same_question"]
    assert projected["feedback_metadata"] == {
        "llm_called": False,
        "pending_reason": "feedback_not_generated",
        "answer_id": "answer_pending_projection",
        "session_id": "session_pending_projection",
        "question_id": "question_pending_projection",
    }


def test_ai_task_feedback_result_projection_uses_response_safe_projection() -> None:
    from app.application.polish.feedback_projection import REDACTED_SENSITIVE_FEEDBACK_DETAIL

    now = utc_now()
    task = SimpleNamespace(
        id="task_feedback_projection",
        task_type="polish_feedback_generation",
        status="succeeded",
        trace_ref_ids=[],
        created_at=now,
    )
    result = SimpleNamespace(
        status="succeeded",
        result_ref_id="feedback_projection",
        validation_result_ref_id=None,
        trace_ref_id="trace_feedback_projection",
        created_at=now,
    )

    projected = _result_projection(
        task,
        result=result,
        payload={
            "status": "generated",
            "feedback_summary": "旧兼容 summary",
            "feedback_text": "新反馈文本",
            "trace_refs": ["trace_001"],
            "raw_prompt": "must_not_leak",
            "feedback_metadata": {
                "provider_status": "called",
                "debug_text": "raw_completion=must_not_leak",
            },
        },
    )

    result_payload = projected["result_payload"]
    assert result_payload["feedback_text"] == "新反馈文本"
    assert result_payload["feedback_metadata"]["provider_status"] == "called"
    assert result_payload["feedback_metadata"]["debug_text"] == REDACTED_SENSITIVE_FEEDBACK_DETAIL
    assert "feedback_summary" not in result_payload
    serialized = _serialized(projected)
    assert "raw_prompt" not in serialized
    assert "must_not_leak" not in serialized
