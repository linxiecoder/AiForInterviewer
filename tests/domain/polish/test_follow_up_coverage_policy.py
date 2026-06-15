from __future__ import annotations

from hashlib import sha256

from app.domain.polish.policies.follow_up_coverage_policy import (
    FollowUpAssetConflict,
    FollowUpCoverageAction,
    FollowUpCoverageInput,
    FollowUpCoveragePolicy,
)


def test_missing_point_focus_skips_completed_focus_refs() -> None:
    completed = _focus_key("missing_point", "失败补偿")

    decision = FollowUpCoveragePolicy.decide(
        FollowUpCoverageInput(
            expected_points=("幂等设计", "失败补偿", "上线验证"),
            covered_points=("幂等设计",),
            missing_points=("失败补偿", "上线验证"),
            completed_focus_refs=(completed,),
            coverage_available=True,
        )
    )

    assert decision.action == FollowUpCoverageAction.ALLOW_FOLLOW_UP
    assert decision.focus.focus_source == "missing_point"
    assert decision.focus.target_dimension == "上线验证"
    assert decision.focus.focus_key == _focus_key("missing_point", "上线验证")
    assert completed in decision.matrix["completed_focus_refs"]
    assert "completed_focus_ref_skipped" in decision.reason_codes


def test_covered_points_filter_weak_points_and_mark_completed_refs() -> None:
    decision = FollowUpCoveragePolicy.decide(
        FollowUpCoverageInput(
            expected_points=("幂等设计", "失败补偿"),
            covered_points=("幂等设计",),
            weak_points=("幂等设计", "失败补偿"),
            coverage_available=True,
        )
    )

    assert decision.focus.focus_source == "weak_point"
    assert decision.focus.target_dimension == "失败补偿"
    assert decision.matrix["weak_points"] == ["失败补偿"]
    assert _focus_key("weak_point", "幂等设计") in decision.matrix["completed_focus_refs"]


def test_asset_conflict_has_highest_priority() -> None:
    decision = FollowUpCoveragePolicy.decide(
        FollowUpCoverageInput(
            expected_points=("幂等设计",),
            covered_points=("幂等设计",),
            contradicted_points=("RocketMQ",),
            asset_conflicts=(
                FollowUpAssetConflict(
                    conflict_type="technology_stack_conflict",
                    current_answer_claim="RocketMQ",
                    asset_claim="PostgreSQL",
                    severity="major",
                ),
            ),
            coverage_available=True,
        )
    )

    assert decision.focus.focus_source == "asset_conflict"
    assert decision.focus.follow_up_reason == "asset_conflict"
    assert decision.focus.recommended_action == "clarify_asset_conflict"
    assert decision.matrix["asset_conflicts"][0]["current_answer_claim"] == "RocketMQ"


def test_all_candidate_focus_completed_returns_complete_decision() -> None:
    decision = FollowUpCoveragePolicy.decide(
        FollowUpCoverageInput(
            expected_points=("失败补偿",),
            missing_points=("失败补偿",),
            completed_focus_refs=(_focus_key("missing_point", "失败补偿"),),
            coverage_available=True,
        )
    )

    assert decision.action == FollowUpCoverageAction.COMPLETE
    assert decision.focus.completion_status == "all_focus_completed"
    assert decision.focus.recommended_action == "focus_complete"
    assert "all_candidate_focus_completed" in decision.reason_codes


def test_used_focus_refs_prevent_repeating_same_follow_up_intent() -> None:
    decision = FollowUpCoveragePolicy.decide(
        FollowUpCoverageInput(
            expected_points=("失败补偿",),
            missing_points=("失败补偿",),
            used_focus_refs=(_focus_key("missing_point", "失败补偿"),),
            coverage_available=True,
        )
    )

    assert decision.action == FollowUpCoverageAction.COMPLETE
    assert decision.focus.completion_status == "all_focus_completed"
    assert "used_focus_ref_skipped" in decision.reason_codes


def _focus_key(source_type: str, value: str) -> str:
    seed = f"{source_type}:{value}"
    return f"focus_{source_type}_{sha256(seed.encode('utf-8')).hexdigest()[:12]}"
