from __future__ import annotations

from app.domain.polish.policies.answer_change_policy import (
    AnswerChangeInput,
    AnswerChangePolicy,
    AnswerChangeTrend,
    PreviousAnswerSnapshot,
)


def test_first_attempt_marks_current_covered_points_as_new() -> None:
    decision = AnswerChangePolicy.evaluate(
        AnswerChangeInput(current_covered_points=("幂等设计", "失败补偿"))
    )

    assert not decision.has_prior_attempts
    assert decision.trend == AnswerChangeTrend.FIRST_ATTEMPT
    assert decision.newly_added_points == ("幂等设计", "失败补偿")
    assert decision.to_legacy_dict()["trend"] == "first_attempt"


def test_repeated_answer_detects_retained_new_regressed_and_fixed_loss_points() -> None:
    decision = AnswerChangePolicy.evaluate(
        AnswerChangeInput(
            current_covered_points=("失败补偿", "上线验证"),
            current_loss_point_ids=("loss_metric",),
            current_score_value=4.5,
            previous_answers=(
                PreviousAnswerSnapshot(
                    answer_id="ans_1",
                    covered_points=("幂等设计", "失败补偿"),
                    loss_point_ids=("loss_metric", "loss_trace"),
                    score_value=3.0,
                ),
            ),
        )
    )

    assert decision.has_prior_attempts
    assert decision.previous_answer_refs == ("ans_1",)
    assert decision.retained_points == ("失败补偿",)
    assert decision.newly_added_points == ("上线验证",)
    assert decision.regressed_points == ("幂等设计",)
    assert decision.repeated_loss_points == ("loss_metric",)
    assert decision.fixed_loss_points == ("loss_trace",)
    assert decision.score_delta == 1.5
    assert decision.trend == AnswerChangeTrend.MIXED


def test_llm_effect_is_merged_when_history_has_partial_metadata() -> None:
    decision = AnswerChangePolicy.evaluate(
        AnswerChangeInput(
            current_covered_points=("幂等设计",),
            current_loss_point_ids=("loss_trace",),
            previous_answers=(PreviousAnswerSnapshot(answer_id="ans_1", covered_points=("幂等设计",)),),
            llm_regressed_points=("上线验证",),
            llm_repeated_loss_point_ids=("loss_trace",),
            llm_score_delta=-0.5,
        )
    )

    assert decision.retained_points == ("幂等设计",)
    assert decision.regressed_points == ("上线验证",)
    assert decision.repeated_loss_points == ("loss_trace",)
    assert decision.score_delta == -0.5
    assert decision.trend == AnswerChangeTrend.REGRESSED
