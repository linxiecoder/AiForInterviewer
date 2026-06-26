from __future__ import annotations

from typing import Any

from app.application.polish.payload_normalization import payload_normalization
from app.application.polish.score_evolution import build_score_evolution


def test_score_evolution_tracks_score_and_dimension_over_time_from_generated_feedback() -> None:
    history = [
        _history_item("feedback_1", "answer_1", 1, _payload(64, correctness=60, depth=68)),
        _history_item("feedback_2", "answer_2", 2, _payload(86, correctness=82, depth=90)),
    ]

    evolution = build_score_evolution(history)

    assert [point.score for point in evolution.score_over_time] == [64.0, 86.0]
    assert [point.score for point in evolution.dimension_score_evolution["correctness"]] == [60.0, 82.0]
    assert [trace.feedback_id for trace in evolution.source_trace_refs] == ["feedback_1", "feedback_2"]
    assert evolution.source_basis == "step2_effective_generated_feedback + step5_effective_feedback_history"


def test_score_evolution_excludes_pending_failed_and_validation_failed_records() -> None:
    history = [
        _history_item("feedback_generated", "answer_1", 1, _payload(72)),
        _history_item("feedback_pending", "answer_2", 2, _payload(99, status="pending"), status="pending"),
        _history_item(
            "feedback_validation_failed",
            "answer_3",
            3,
            _payload(100, status="validation_failed"),
            status="validation_failed",
        ),
        _history_item(
            "feedback_generation_failed",
            "answer_4",
            4,
            _payload(100, status="generation_failed"),
            status="generation_failed",
        ),
    ]

    evolution = build_score_evolution(history)

    assert [point.feedback_id for point in evolution.score_over_time] == ["feedback_generated"]
    assert evolution.included_feedback_count == 1
    assert evolution.excluded_feedback_count == 3


def test_score_evolution_accepts_real_step5_effective_feedback_history_shape() -> None:
    normalized = payload_normalization(
        {
            "same_question_answers": [
                {
                    "answer_id": "answer_step5_history",
                    "answer_round": 2,
                    "answer_text": "我补充了失败恢复和观测指标。",
                    "generated_feedback_payload": _payload(81, correctness=78, depth=84),
                }
            ]
        }
    )

    evolution = build_score_evolution(normalized["step5_effective_feedback_history"])

    assert [point.score for point in evolution.score_over_time] == [81.0]
    assert evolution.score_over_time[0].feedback_id is None
    assert evolution.source_trace_refs[0].source_kind == "step5_effective_feedback_history"
    assert evolution.source_trace_refs[0].source_fields == (
        "answer_id",
        "answer_round",
        "step5_effective_feedback_history.score_result",
        "step5_effective_feedback_history.loss_point_ids",
    )
    assert evolution.included_feedback_count == 1
    assert evolution.excluded_feedback_count == 0


def test_scoreless_generated_feedback_is_counted_as_excluded_not_mastery_source() -> None:
    history = [
        _history_item("feedback_scored", "answer_1", 1, _payload(72)),
        _history_item(
            "feedback_scoreless",
            "answer_2",
            2,
            {"status": "generated", "feedback_text": "历史反馈缺少可用分数。", "loss_points": []},
        ),
    ]

    evolution = build_score_evolution(history)

    assert [point.feedback_id for point in evolution.score_over_time] == ["feedback_scored"]
    assert [trace.feedback_id for trace in evolution.source_trace_refs] == ["feedback_scored"]
    assert evolution.included_feedback_count == 1
    assert evolution.excluded_feedback_count == 1


def _history_item(
    feedback_id: str,
    answer_id: str,
    answer_round: int,
    payload: dict[str, Any],
    *,
    status: str = "generated",
) -> dict[str, Any]:
    return {
        "feedback_id": feedback_id,
        "answer_id": answer_id,
        "answer_round": answer_round,
        "status": status,
        "generated_feedback_payload": payload,
    }


def _payload(
    score: float,
    *,
    status: str = "generated",
    correctness: float | None = None,
    depth: float | None = None,
) -> dict[str, Any]:
    dimensions = {
        "correctness": correctness if correctness is not None else score,
        "depth": depth if depth is not None else score,
    }
    return {
        "status": status,
        "feedback_text": "历史有效反馈。",
        "score_result": {
            "score_type": "polish_answer",
            "score_value": score,
            "dimension_scores": [
                {"dimension": dimension, "score": value} for dimension, value in dimensions.items()
            ],
        },
        "loss_points": [],
        "answer_change_analysis": {},
    }
