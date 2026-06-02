from __future__ import annotations

import pytest

from app.application.polish.canonical_evidence import (
    SOURCE_SUPPORT_LEVELS,
    SourceSupportSummary,
    source_support_level_from_summary,
)


def test_source_support_summary_serializes_required_fields() -> None:
    summary = SourceSupportSummary(
        level="direct_project_evidence",
        primary_evidence_refs=({"resource_type": "asset", "resource_id": "asset_001"},),
        reason_codes=("canonical_asset_confirmed",),
        confidence="high",
        computed_at="deterministic_fixture",
    )

    assert summary.to_dict() == {
        "level": "direct_project_evidence",
        "primary_evidence_refs": [{"resource_type": "asset", "resource_id": "asset_001"}],
        "adjacent_evidence_refs": [],
        "job_gap_refs": [],
        "missing_context": [],
        "reason_codes": ["canonical_asset_confirmed"],
        "confidence": "high",
        "policy_version": "source_support_summary.v1",
        "computed_at": "deterministic_fixture",
    }
    assert source_support_level_from_summary(summary.to_dict()) == "direct_project_evidence"


def test_source_support_summary_rejects_unknown_level() -> None:
    with pytest.raises(ValueError, match="source_support_level_invalid"):
        SourceSupportSummary(
            level="unsupported",
            primary_evidence_refs=({"resource_type": "asset", "resource_id": "asset_001"},),
            reason_codes=("canonical_asset_confirmed",),
            confidence="high",
        )


@pytest.mark.parametrize("level", SOURCE_SUPPORT_LEVELS)
def test_source_support_summary_requires_reason_codes(level: str) -> None:
    kwargs = _required_kwargs_for_level(level)
    kwargs["reason_codes"] = ()

    with pytest.raises(ValueError, match="source_support_reason_codes_required"):
        SourceSupportSummary(level=level, **kwargs)


def test_source_support_summary_requires_level_specific_refs_and_missing_context() -> None:
    with pytest.raises(ValueError, match="source_support_primary_refs_required"):
        SourceSupportSummary(
            level="direct_project_evidence",
            reason_codes=("canonical_asset_confirmed",),
            confidence="high",
        )
    with pytest.raises(ValueError, match="source_support_adjacent_refs_required"):
        SourceSupportSummary(
            level="adjacent_project_evidence",
            reason_codes=("adjacent_project_signal",),
            confidence="medium",
        )
    with pytest.raises(ValueError, match="source_support_job_gap_refs_required"):
        SourceSupportSummary(
            level="job_gap_only",
            reason_codes=("job_requirement_without_project_evidence",),
            confidence="medium",
        )
    with pytest.raises(ValueError, match="source_support_missing_context_required"):
        SourceSupportSummary(
            level="insufficient_context",
            reason_codes=("no_confirmed_canonical_asset",),
            confidence="low",
        )


def _required_kwargs_for_level(level: str) -> dict[str, object]:
    if level == "direct_project_evidence":
        return {
            "primary_evidence_refs": ({"resource_type": "asset", "resource_id": "asset_001"},),
            "confidence": "high",
        }
    if level == "adjacent_project_evidence":
        return {
            "adjacent_evidence_refs": ({"resource_type": "asset", "resource_id": "asset_001"},),
            "confidence": "medium",
        }
    if level == "job_gap_only":
        return {
            "job_gap_refs": ({"resource_type": "job_requirement", "resource_id": "job_gap_001"},),
            "confidence": "medium",
        }
    return {
        "missing_context": ("confirmed_project_evidence",),
        "confidence": "low",
    }
