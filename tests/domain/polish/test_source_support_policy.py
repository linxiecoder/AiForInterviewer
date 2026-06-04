from __future__ import annotations

from app.domain.polish.policies.source_support_policy import (
    SourceSupportDecision,
    SourceSupportEvidence,
    SourceSupportLevel,
    SourceSupportPolicy,
    SourceSupportTarget,
)


def test_source_support_decision_converts_direct_project_evidence_to_summary() -> None:
    decision = SourceSupportDecision(
        level=SourceSupportLevel.DIRECT_PROJECT_EVIDENCE,
        reason_codes=("direct_project_term_overlap",),
        evidence_refs=("resume_project_001",),
    )

    summary = decision.to_summary()

    assert summary.to_dict() == {
        "level": "direct_project_evidence",
        "primary_evidence_refs": ["resume_project_001"],
        "adjacent_evidence_refs": [],
        "job_gap_refs": [],
        "missing_context": [],
        "reason_codes": ["direct_project_term_overlap"],
        "confidence": "high",
        "policy_version": "source_support_policy.v1",
        "computed_at": "deterministic:source_support_policy.v1",
    }


def test_source_support_summary_maps_adjacent_and_job_gap_refs() -> None:
    adjacent = SourceSupportDecision(
        level=SourceSupportLevel.ADJACENT_PROJECT_EVIDENCE,
        reason_codes=("project_evidence_without_direct_overlap",),
        evidence_refs=("resume_project_004",),
    ).to_summary()
    job_gap = SourceSupportDecision(
        level=SourceSupportLevel.JOB_GAP_ONLY,
        reason_codes=("job_gap_evidence_only",),
        evidence_refs=("job_gap_001",),
    ).to_summary()

    assert adjacent.primary_evidence_refs == ()
    assert adjacent.adjacent_evidence_refs == ("resume_project_004",)
    assert adjacent.missing_context == ("direct_project_overlap",)
    assert adjacent.confidence == "medium"
    assert job_gap.job_gap_refs == ("job_gap_001",)
    assert job_gap.missing_context == ("direct_project_evidence",)
    assert job_gap.confidence == "medium"


def test_source_support_summary_records_insufficient_context() -> None:
    summary = SourceSupportPolicy.classify_question_context(
        target=SourceSupportTarget(title="分布式一致性设计"),
        evidence=(),
    ).to_summary()

    assert summary.level == SourceSupportLevel.INSUFFICIENT_CONTEXT
    assert summary.missing_context == ("project_evidence", "job_requirement_evidence")
    assert summary.confidence == "low"


def test_existing_level_summary_keeps_safe_project_refs() -> None:
    decision = SourceSupportPolicy.classify_question_context(
        existing_level="direct_project_evidence",
        target=SourceSupportTarget(title="FastAPI PostgreSQL workflow reliability"),
        evidence=(
            SourceSupportEvidence(
                source_type="resume_project",
                text="Candidate built FastAPI APIs with PostgreSQL persistence.",
                ref="resume_project_backend",
            ),
            SourceSupportEvidence(
                source_type="job_requirement",
                text="岗位要求 Redis 分布式锁。",
                ref="job_gap_redis",
            ),
        ),
    )

    assert decision.to_summary().to_dict()["primary_evidence_refs"] == ["resume_project_backend"]
