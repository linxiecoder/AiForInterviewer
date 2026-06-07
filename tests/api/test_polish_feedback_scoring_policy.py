from __future__ import annotations

from app.domain.polish.policies.scoring_policy import (
    ScoringInput,
    ScoringLossPoint,
    ScoringPolicy,
)


def test_scoring_policy_maps_known_severity_to_expected_deductions_and_score() -> None:
    decision = ScoringPolicy.evaluate(
        ScoringInput(
            loss_points=(
                ScoringLossPoint(loss_point_id="lp_critical", severity="critical", reason="安全边界缺失"),
                ScoringLossPoint(loss_point_id="lp_major", severity="major", reason="未解释失败回退路径"),
                ScoringLossPoint(loss_point_id="lp_minor", severity="minor", reason="观测口径不完整"),
            )
        )
    )

    assert decision.score_type == "polish_answer"
    assert decision.score_value == 62.0
    assert [item.deduction for item in decision.scored_loss_points] == [20.0, 12.0, 6.0]
    assert decision.scoring_basis == "score_result is computed server-side from loss_point severity."
    assert decision.warnings == ()


def test_scoring_policy_unknown_severity_gives_zero_deduction_and_warning() -> None:
    decision = ScoringPolicy.evaluate(
        ScoringInput(
            loss_points=(
                ScoringLossPoint(
                    loss_point_id="lp_unknown",
                    severity="weird",
                    reason="未知 severity 标签",
                ),
            )
        )
    )

    assert decision.scored_loss_points[0].deduction == 0.0
    assert decision.scored_loss_points[0].is_unknown_severity is True
    assert decision.score_value == 100.0
    assert decision.warnings == ("score_point_unknown_severity:lp_unknown",)
    assert "server-side" in decision.scoring_basis
