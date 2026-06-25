from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.application.polish.entities import PolishFeedback
from app.application.polish.feedback_generation_service import FeedbackGenerationService
from app.application.polish.use_cases import _latest_feedback_by_answer_id

from tests.api.test_polish_feedback_acceptance_support import (
    AcceptanceDeterministicTransport,
    candidate_payload,
    context,
    generate_payload,
    loss_point_ids,
    reference_answer_text,
    score_value,
)

BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_improved_answer_projects_positive_score_and_dimension_delta() -> None:
    weak_payload = _payload(candidate_payload(64, loss_ids=["lp_recovery", "lp_observability"]))
    improved_payload = _payload(
        candidate_payload(86, loss_ids=[]),
        answer_id="answer_step5_improved",
        answer_text="我会保留消息队列异步解耦，并补充失败恢复、幂等键、死信、观测指标、告警和人工介入边界。",
        previous_answers=[_previous_answer("answer_step5_weak", weak_payload, answer_round=1)],
    )
    change = improved_payload["answer_change_analysis"]
    assert change["score_delta"] > 0
    assert any(delta > 0 for delta in change["dimension_delta"].values())
    assert change["trend"] == "improved"


def test_improved_answer_dimension_delta_tracks_only_changed_dimensions() -> None:
    weak_candidate = candidate_payload(70, loss_ids=["lp_recovery"])
    _set_dimension_scores(weak_candidate, {
        "correctness": 70, "depth": 55, "tradeoff_reasoning": 60, "structure": 72,
        "engineering_awareness": 58,
    })
    weak_payload = _payload(weak_candidate)
    improved_candidate = candidate_payload(74, loss_ids=[])
    _set_dimension_scores(improved_candidate, {
        "correctness": 70, "depth": 55, "tradeoff_reasoning": 78, "structure": 72,
        "engineering_awareness": 80,
    })
    improved_payload = _payload(
        improved_candidate,
        answer_id="answer_step5_dimension_specific",
        answer_text="我会补充权衡依据、故障恢复指标、告警阈值和人工兜底边界。",
        previous_answers=[_previous_answer("answer_step5_dimension_weak", weak_payload)],
    )
    assert improved_payload["answer_change_analysis"]["dimension_delta"] == {
        "correctness": 0.0,
        "depth": 0.0,
        "engineering_awareness": 22.0,
        "structure": 0.0,
        "tradeoff_reasoning": 18.0,
    }


def test_same_answer_does_not_use_step4_stability_as_fake_improvement() -> None:
    answer_text = str(context()["answer_text"])
    previous_payload = _payload(candidate_payload(80), answer_text=answer_text)
    repeated_payload = _payload(
        candidate_payload(61),
        answer_id="answer_step5_repeated_same_answer",
        answer_text=answer_text,
        previous_answers=[
            _previous_answer("answer_step5_same_previous", previous_payload, answer_text=answer_text)
        ],
    )
    change = repeated_payload["answer_change_analysis"]
    assert score_value(repeated_payload) >= score_value(previous_payload)
    assert change["trend"] == "unchanged"
    assert change["score_delta"] == 0
    assert all(delta == 0 for delta in change["dimension_delta"].values())


def test_failure_statuses_do_not_override_current_effective_generated_feedback() -> None:
    generated = _feedback("feedback_step5_generated", "generated", _summary("generated", 82), created_at=_time(10))
    failures = (
        _feedback("feedback_step5_validation_failed", "validation_failed", _summary("validation_failed"), created_at=_time(20)),
        _feedback("feedback_step5_generation_failed", "generation_failed", _summary("generation_failed"), created_at=_time(30)),
        _feedback("feedback_step5_timed_out", "timed_out", _summary("timed_out"), created_at=_time(40)),
    )
    assert _latest_feedback_by_answer_id((generated, *failures))["answer_step5_effective"].feedback_id == generated.feedback_id


def test_step4_same_answer_stability_keeps_score_from_regressing() -> None:
    answer_text = str(context()["answer_text"])
    previous_payload = _payload(candidate_payload(80), answer_text=answer_text)
    repeated_payload = _payload(
        candidate_payload(61),
        answer_id="answer_step5_stability_guard",
        answer_text=answer_text,
        previous_answers=[
            _previous_answer("answer_step5_stability_previous", previous_payload, answer_text=answer_text)
        ],
    )
    assert score_value(repeated_payload) >= score_value(previous_payload)
    assert repeated_payload["feedback_metadata"]["same_answer_stability_applied"] is True


def test_step4_reference_replay_score_floor_does_not_create_positive_step5_trend() -> None:
    source_payload = _payload(candidate_payload(80))
    replay_payload = _payload(
        candidate_payload(61, loss_ids=[]),
        answer_id="answer_step5_reference_replay",
        answer_text=reference_answer_text(source_payload),
        previous_answers=[_previous_answer("answer_step5_reference_source", source_payload)],
    )
    change = replay_payload["answer_change_analysis"]
    assert score_value(replay_payload) >= 90
    assert change["trend"] == "unchanged"
    assert change["score_delta"] == 0
    assert all(delta == 0 for delta in change["dimension_delta"].values())
    assert change["derived_improvement_summary"]["fixed_loss_point_ids"] == []
    assert replay_payload["feedback_metadata"]["step5_reference_replay_trend_neutralized"] is True


def test_step5_derived_summaries_ignore_payload_claimed_fixed_or_repeated_points() -> None:
    previous_payload = _payload(candidate_payload(80, loss_ids=["lp_recovery"]))
    current_candidate = candidate_payload(80, loss_ids=["lp_recovery"])
    current_candidate["answer_change_analysis"] = {
        "fixed_loss_points": ["llm_claimed_fix"],
        "repeated_loss_points": ["llm_claimed_repeat"],
        "regressed_points": ["llm_claimed_regression"],
    }
    current_payload = _payload(
        current_candidate,
        answer_id="answer_step5_delta_owned_by_server",
        answer_text="我会说明失败恢复，但本轮仍没有新增幂等和观测指标证据。",
        previous_answers=[_previous_answer("answer_step5_delta_source", previous_payload)],
    )
    change = current_payload["answer_change_analysis"]
    assert change["score_delta"] == 0
    assert all(delta == 0 for delta in change["dimension_delta"].values())
    assert change["fixed_loss_points"] == []
    assert change["repeated_loss_points"] == ["lp_recovery"]
    assert change["regressed_points"] == []
    assert change["trend"] == "unchanged"
    assert change["derived_improvement_summary"]["fixed_loss_point_ids"] == []


def test_score_and_dimension_delta_summaries_do_not_create_step6_or_step7_outputs() -> None:
    weak_payload = _payload(candidate_payload(64, loss_ids=["lp_recovery"]))
    improved_payload = _payload(
        candidate_payload(86, loss_ids=[]),
        answer_id="answer_step5_delta_only",
        answer_text="我会保留消息队列异步解耦，并补充失败恢复、幂等键、观测指标和人工介入边界。",
        previous_answers=[_previous_answer("answer_step5_delta_previous", weak_payload)],
    )
    change = improved_payload["answer_change_analysis"]
    assert set(change["derived_improvement_summary"]) == {
        "score_delta", "positive_dimension_deltas", "fixed_loss_point_ids"
    }
    assert set(change["derived_remaining_gap_summary"]) == {"remaining_loss_point_ids", "non_positive_dimension_deltas"}
    assert set(change["derived_regression_summary"]) == {"score_delta", "negative_dimension_deltas", "regressed_points"}
    forbidden_fields = {
        "next_question", "next_question_id", "next_action", "review_plan", "training_plan",
        "progress_mastery", "step6", "step7",
    }
    assert not (forbidden_fields & set(improved_payload))
    assert not (forbidden_fields & set(change))


def _payload(
    candidate: dict[str, Any],
    *,
    answer_id: str = "answer_step5_current",
    answer_text: str | None = None,
    previous_answers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate])),
        context(answer_id=answer_id, answer_text=answer_text or str(context()["answer_text"]), previous_answers=previous_answers or []),
    )


def _previous_answer(
    answer_id: str,
    payload: dict[str, Any],
    *,
    answer_round: int = 1,
    answer_text: str | None = None,
) -> dict[str, Any]:
    return {
        "answer_id": answer_id,
        "answer_round": answer_round,
        "answer_text": answer_text or "上一轮回答只覆盖异步解耦，缺少失败恢复和观测指标。",
        "answer_coverage": payload["answer_coverage"],
        "loss_point_ids": sorted(loss_point_ids(payload)),
        "loss_points": payload["loss_points"],
        "score_result": payload["score_result"],
        "generated_feedback_payload": payload,
    }


def _set_dimension_scores(candidate: dict[str, Any], scores: dict[str, float]) -> None:
    dimension_scores = candidate["score_result"]["dimension_scores"]
    assert isinstance(dimension_scores, list)
    for item in dimension_scores:
        assert isinstance(item, dict)
        dimension = item["dimension"]
        assert isinstance(dimension, str)
        if dimension in scores:
            item["score"] = scores[dimension]


def _feedback(feedback_id: str, status: str, feedback_summary: str, *, created_at: datetime) -> PolishFeedback:
    return PolishFeedback(
        feedback_id=feedback_id,
        owner_id="owner_step5_effective",
        actor_id="actor_step5_effective",
        session_id="session_step5_effective",
        answer_id="answer_step5_effective",
        ai_task_id=f"task_{feedback_id}",
        score_result_id=f"score_{feedback_id}" if status == "generated" else None,
        feedback_summary=feedback_summary,
        status=status,
        created_at=created_at,
        updated_at=created_at,
    )


def _summary(status: str, score: int | None = None) -> str:
    payload: dict[str, Any] = {
        "status": status,
        "feedback_text": "当前有效 generated feedback。" if status == "generated" else "失败记录不应成为当前有效反馈。",
        "score_result": {"score_type": "polish_answer", "score_value": score or 1},
    }
    if status == "generated":
        payload.update({"loss_points": [], "reference_answer": None, "next_recommended_actions": ["continue_same_question"]})
    else:
        payload.update({"error": {"code": status}, "retryable": True})
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _time(seconds: int) -> datetime:
    return BASE_TIME + timedelta(seconds=seconds)
