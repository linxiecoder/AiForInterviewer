from __future__ import annotations

from app.application.polish.context.source_support import SourceSupportSummaryService


def test_source_support_summary_service_classifies_direct_confirmed_assets() -> None:
    result = SourceSupportSummaryService().build(
        canonical_project_assets={
            "available": True,
            "items": [
                {
                    "asset_id": "asset_backend_workflow",
                    "status": "asset_confirmed",
                    "asset_type": "project_story",
                    "title": "Backend workflow automation",
                }
            ],
        }
    )

    assert result.summary.to_dict()["level"] == "direct_project_evidence"
    assert result.summary.to_dict()["primary_evidence_refs"] == [
        {"resource_type": "asset", "resource_id": "asset_backend_workflow"}
    ]
    assert result.summary.to_dict()["reason_codes"] == ["canonical_asset_confirmed"]
    assert result.summary.to_dict()["confidence"] == "high"
    assert result.blocking_issues == ()


def test_source_support_summary_service_classifies_adjacent_project_evidence() -> None:
    result = SourceSupportSummaryService().build(
        evidence_chunks=(
            {
                "chunk_id": "resume_project_001",
                "source_type": "resume_project",
                "title": "Backend automation",
            },
        )
    )

    assert result.summary.to_dict()["level"] == "adjacent_project_evidence"
    assert result.summary.to_dict()["adjacent_evidence_refs"] == [
        {"resource_type": "resume_project", "resource_id": "resume_project_001"}
    ]
    assert result.summary.to_dict()["reason_codes"] == ["project_evidence_without_confirmed_canonical_asset"]
    assert result.summary.to_dict()["confidence"] == "medium"


def test_source_support_summary_service_classifies_matching_project_evidence_as_direct() -> None:
    result = SourceSupportSummaryService().build(
        evidence_chunks=(
            {
                "chunk_id": "resume_project_payment",
                "source_type": "resume_project",
                "text": "支付链路需要覆盖幂等、失败补偿和上线验证指标。",
            },
        ),
        focus_target={
            "title": "支付可靠性追问",
            "expected_capability": "验证候选人能否围绕支付链路说明设计、取舍和复盘。",
            "missing_points": ["需要补充验证指标。"],
        },
    )

    assert result.summary.to_dict()["level"] == "direct_project_evidence"
    assert result.summary.to_dict()["primary_evidence_refs"] == [
        {"resource_type": "resume_project", "resource_id": "resume_project_payment"}
    ]
    assert result.summary.to_dict()["reason_codes"] == ["matching_project_evidence"]
    assert result.summary.to_dict()["confidence"] == "high"


def test_source_support_summary_service_classifies_job_gap_only() -> None:
    result = SourceSupportSummaryService().build(
        evidence_chunks=(
            {
                "chunk_id": "match_gap_001",
                "source_type": "match_gap",
                "title": "Distributed consistency gap",
            },
        )
    )

    assert result.summary.to_dict()["level"] == "job_gap_only"
    assert result.summary.to_dict()["job_gap_refs"] == [
        {"resource_type": "match_gap", "resource_id": "match_gap_001"}
    ]
    assert result.summary.to_dict()["reason_codes"] == ["job_gap_without_project_evidence"]
    assert result.summary.to_dict()["confidence"] == "medium"


def test_source_support_summary_service_excludes_archived_assets_by_default() -> None:
    result = SourceSupportSummaryService().build(
        canonical_project_assets={
            "available": True,
            "items": [
                {
                    "asset_id": "asset_archived_workflow",
                    "status": "asset_archived",
                    "asset_type": "project_story",
                    "title": "Archived backend workflow",
                }
            ],
        }
    )

    assert result.summary.to_dict()["level"] == "insufficient_context"
    assert result.summary.to_dict()["missing_context"] == ["confirmed_project_evidence"]
    assert result.summary.to_dict()["reason_codes"] == ["no_confirmed_canonical_asset"]


def test_source_support_summary_service_marks_asset_conflicts_as_blocking_hitl() -> None:
    result = SourceSupportSummaryService().build(
        canonical_project_assets={
            "available": True,
            "items": [
                {
                    "asset_id": "asset_backend_workflow_a",
                    "status": "asset_confirmed",
                    "asset_type": "project_story",
                    "title": "Backend workflow version A",
                },
                {
                    "asset_id": "asset_backend_workflow_b",
                    "status": "asset_confirmed",
                    "asset_type": "project_story",
                    "title": "Backend workflow version B",
                    "conflict_refs": [{"resource_type": "asset", "resource_id": "asset_backend_workflow_a"}],
                },
            ],
        }
    )

    assert result.summary.to_dict()["level"] == "insufficient_context"
    assert result.summary.to_dict()["missing_context"] == ["asset_conflict_human_review"]
    assert result.summary.to_dict()["reason_codes"] == ["asset_conflict_requires_human_review"]
    assert result.blocking_issues == (
        {
            "issue_type": "asset_conflict_requires_human_review",
            "severity": "blocking",
            "hitl_required": "true",
        },
    )


def test_source_support_summary_service_does_not_treat_current_answer_as_canonical_evidence() -> None:
    result = SourceSupportSummaryService().build(
        current_answer_refs=({"resource_type": "answer", "resource_id": "answer_current"},)
    )

    assert result.summary.to_dict()["level"] == "insufficient_context"
    assert result.summary.to_dict()["missing_context"] == ["confirmed_project_evidence"]
    assert result.summary.to_dict()["reason_codes"] == ["no_confirmed_canonical_asset"]
    assert result.warnings == ("current_answer_not_canonical_evidence",)
