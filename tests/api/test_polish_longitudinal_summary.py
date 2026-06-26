from __future__ import annotations

from typing import Any

from app.application.polish.longitudinal_summary import build_longitudinal_feedback_summary
from app.application.polish.stable_progress_view import build_stable_progress_view


def test_longitudinal_summary_reports_historical_improvement_gap_regression_only() -> None:
    history = [
        _history_item(
            "feedback_mixed",
            _payload(
                78,
                answer_change_analysis={
                    "derived_improvement_summary": {
                        "score_delta": 12,
                        "positive_dimension_deltas": {"depth": 8},
                        "fixed_loss_point_ids": ["lp_recovery"],
                    },
                    "derived_remaining_gap_summary": {
                        "remaining_loss_point_ids": ["lp_observability"],
                        "non_positive_dimension_deltas": {"structure": 0},
                    },
                    "derived_regression_summary": {
                        "score_delta": -2,
                        "negative_dimension_deltas": {"correctness": -2},
                        "regressed_points": ["lp_tradeoff"],
                    },
                },
            ),
        )
    ]

    summary = build_longitudinal_feedback_summary(history)

    assert "score_delta:+12.0" in summary.improvements
    assert "dimension:depth:+8.0" in summary.improvements
    assert "fixed_loss_point:lp_recovery" in summary.improvements
    assert "remaining_loss_point:lp_observability" in summary.remaining_gaps
    assert "dimension:correctness:-2.0" in summary.regressions
    assert summary.source_trace_refs[0].feedback_id == "feedback_mixed"


def test_stable_progress_view_does_not_emit_step7_or_learning_path_outputs() -> None:
    view = build_stable_progress_view([_history_item("feedback_latest", _payload(90))])
    payload = view.to_payload()
    forbidden = {
        "question_generation",
        "next_question",
        "next_question_recommendation",
        "adaptive_learning_path",
        "training_plan",
        "auto_tutoring_logic",
    }

    assert payload["schema_id"] == "polish_step6_stable_progress_view.v1"
    assert payload["source_traceability"]
    assert not (forbidden & set(payload))


def _history_item(feedback_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "feedback_id": feedback_id,
        "answer_id": f"answer_{feedback_id}",
        "answer_round": 1,
        "status": "generated",
        "generated_feedback_payload": payload,
    }


def _payload(
    score: float,
    *,
    answer_change_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": "generated",
        "feedback_text": "历史有效反馈。",
        "score_result": {
            "score_type": "polish_answer",
            "score_value": score,
            "dimension_scores": [{"dimension": "depth", "score": score}],
        },
        "loss_points": [],
        "answer_change_analysis": answer_change_analysis or {},
    }
