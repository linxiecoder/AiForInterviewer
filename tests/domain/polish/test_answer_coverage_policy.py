from __future__ import annotations

from app.domain.polish.policies.answer_coverage_policy import (
    AnswerCoverageInput,
    AnswerCoveragePolicy,
    CoverageLevel,
)


def test_answer_covers_all_expected_points() -> None:
    decision = AnswerCoveragePolicy.evaluate(
        AnswerCoverageInput(
            answer_text="我会说明幂等设计，并覆盖失败补偿和上线验证。",
            expected_points=("幂等设计", "失败补偿", "上线验证"),
        )
    )

    assert decision.coverage_level == CoverageLevel.COMPLETE
    assert decision.covered_points == ("幂等设计", "失败补偿", "上线验证")
    assert decision.to_legacy_dict()["missing_points"] == []


def test_answer_weakly_covers_point_when_only_keywords_overlap() -> None:
    decision = AnswerCoveragePolicy.evaluate(
        AnswerCoverageInput(
            answer_text="容量方面还需要补齐细节。",
            expected_points=("容量规划", "上线验证"),
        )
    )

    assert decision.coverage_level == CoverageLevel.PARTIAL
    assert "容量规划" in decision.weak_points
    assert "容量规划" in decision.missing_points
    assert "上线验证" in decision.missing_points


def test_loss_point_reason_is_preserved_as_weak_point() -> None:
    decision = AnswerCoveragePolicy.evaluate(
        AnswerCoverageInput(
            answer_text="我覆盖了幂等设计。",
            expected_points=("幂等设计",),
            loss_point_reasons=("缺少量化指标",),
        )
    )

    assert decision.covered_points == ("幂等设计",)
    assert "缺少量化指标" in decision.weak_points
    assert "loss_point_reason_marked_weak" in decision.reason_codes


def test_asset_conflict_claims_become_contradicted_points() -> None:
    decision = AnswerCoveragePolicy.evaluate(
        AnswerCoverageInput(
            answer_text="我使用 Redis 做缓存。",
            expected_points=("缓存策略",),
            contradicted_asset_claims=("Canonical asset only supports PostgreSQL persistence.",),
        )
    )

    assert decision.contradicted_points == ("Canonical asset only supports PostgreSQL persistence.",)
    assert "asset_claim_contradicted" in decision.reason_codes
