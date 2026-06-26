from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.application.polish.progress_mastery import build_progress_mastery_state


def test_progress_mastery_is_derived_only_and_does_not_mutate_feedback_payload() -> None:
    history = [
        _history_item("feedback_weak", 1, _payload(62, loss_ids=["lp_recovery"])),
        _history_item("feedback_strong", 2, _payload(88, loss_ids=[])),
    ]
    original = deepcopy(history)

    mastery = build_progress_mastery_state(history)

    assert history == original
    assert mastery.mastery_level == "mastered"
    assert mastery.latest_score == 88.0
    assert mastery.score_delta == 26.0
    assert mastery.source_trace_refs[0].feedback_id == "feedback_weak"
    assert mastery.source_basis == "step2_effective_generated_feedback + step5_effective_feedback_history"


def test_failure_pending_and_validation_failed_do_not_increment_positive_mastery() -> None:
    history = [
        _history_item("feedback_low_generated", 1, _payload(55, loss_ids=["lp_gap"])),
        _history_item(
            "feedback_pending_high",
            2,
            _payload(100, status="pending", loss_ids=[]),
            status="pending",
        ),
        _history_item(
            "feedback_failed_high",
            3,
            _payload(100, status="generation_failed", loss_ids=[]),
            status="generation_failed",
        ),
        _history_item(
            "feedback_invalid_high",
            4,
            _payload(100, status="validation_failed", loss_ids=[]),
            status="validation_failed",
        ),
    ]

    mastery = build_progress_mastery_state(history)

    assert mastery.included_feedback_count == 1
    assert mastery.excluded_feedback_count == 3
    assert mastery.positive_signal_count == 0
    assert mastery.mastery_level == "needs_focus"


def _history_item(
    feedback_id: str,
    answer_round: int,
    payload: dict[str, Any],
    *,
    status: str = "generated",
) -> dict[str, Any]:
    return {
        "feedback_id": feedback_id,
        "answer_id": f"answer_{answer_round}",
        "answer_round": answer_round,
        "status": status,
        "generated_feedback_payload": payload,
    }


def _payload(score: float, *, status: str = "generated", loss_ids: list[str]) -> dict[str, Any]:
    return {
        "status": status,
        "feedback_text": "历史有效反馈。",
        "score_result": {
            "score_type": "polish_answer",
            "score_value": score,
            "dimension_scores": [
                {"dimension": "correctness", "score": score},
                {"dimension": "engineering_awareness", "score": score},
            ],
        },
        "loss_points": [{"loss_point_id": loss_id} for loss_id in loss_ids],
        "answer_change_analysis": {},
    }
