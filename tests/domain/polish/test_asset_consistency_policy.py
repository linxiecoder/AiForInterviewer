from __future__ import annotations

from app.domain.polish.policies.asset_consistency_policy import (
    AssetConsistencyInput,
    AssetConsistencyPolicy,
    AssetConsistencyStatus,
    CanonicalAssetItem,
)


def test_missing_canonical_assets_returns_insufficient_context() -> None:
    decision = AssetConsistencyPolicy.evaluate(
        AssetConsistencyInput(answer_text="我主导了 FastAPI 和 PostgreSQL 后端。")
    )

    assert decision.status == AssetConsistencyStatus.INSUFFICIENT_ASSET_CONTEXT
    assert decision.to_legacy_dict()["status"] == "insufficient_asset_context"
    assert decision.reason_codes == ("canonical_asset_context_missing",)


def test_confirmed_asset_supports_matching_project_fact() -> None:
    decision = AssetConsistencyPolicy.evaluate(
        AssetConsistencyInput(
            answer_text="我参与了 FastAPI API 和 PostgreSQL 持久化建设。",
            asset_items=(
                CanonicalAssetItem(
                    asset_id="asset_backend",
                    title="Backend workflow",
                    summary="Candidate contributed FastAPI APIs with PostgreSQL persistence.",
                ),
            ),
            canonical_assets_available=True,
        )
    )

    assert decision.status == AssetConsistencyStatus.CONSISTENT
    assert decision.checked_asset_refs == ("asset_backend",)
    assert decision.conflicts == ()


def test_stack_conflict_requires_user_clarification() -> None:
    decision = AssetConsistencyPolicy.evaluate(
        AssetConsistencyInput(
            answer_text="我主导了 Django 和 MongoDB 的工作流平台。",
            asset_items=(
                CanonicalAssetItem(
                    asset_id="asset_backend",
                    summary="Candidate contributed FastAPI APIs with PostgreSQL persistence.",
                ),
            ),
            canonical_assets_available=True,
        )
    )

    assert decision.status == AssetConsistencyStatus.CONFLICT
    assert decision.user_clarification_required
    assert decision.conflicts[0].conflict_type == "technology_stack_conflict"
    assert decision.conflicts[0].asset_ref == {"resource_type": "asset", "resource_id": "asset_backend"}


def test_unsupported_new_project_claim_is_reported_as_claim_and_conflict() -> None:
    decision = AssetConsistencyPolicy.evaluate(
        AssetConsistencyInput(
            answer_text="我们使用 Redis 做分布式锁，并通过缓存加速。",
            asset_items=(
                CanonicalAssetItem(
                    asset_id="asset_backend",
                    summary="Candidate contributed FastAPI APIs with PostgreSQL persistence.",
                ),
            ),
            canonical_assets_available=True,
        )
    )

    assert decision.status == AssetConsistencyStatus.CONFLICT
    assert decision.unsupported_claims[0].current_answer_claim == "redis"
    assert decision.unsupported_claims[0].reason == "not_supported_by_canonical_project_assets"
    assert any(conflict.conflict_type == "unsupported_claim" for conflict in decision.conflicts)


def test_responsibility_upgrade_conflicts_with_supporting_asset_role() -> None:
    decision = AssetConsistencyPolicy.evaluate(
        AssetConsistencyInput(
            answer_text="I owned the workflow automation project end to end.",
            asset_items=(
                CanonicalAssetItem(
                    asset_id="asset_role",
                    summary="Candidate helped and supported workflow API integration.",
                ),
            ),
            canonical_assets_available=True,
        )
    )

    assert decision.status == AssetConsistencyStatus.CONFLICT
    assert any(conflict.conflict_type == "responsibility_conflict" for conflict in decision.conflicts)
