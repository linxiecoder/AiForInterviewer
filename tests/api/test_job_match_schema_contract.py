import pytest
from pydantic import ValidationError

from app.domain.shared.enums import ConfidenceLevel
from app.schemas.job_match import (
    DimensionScore,
    JOB_MATCH_V1_DIMENSION_KEYS,
    JobMatchResultPayload,
    JobMatchSourceBundle,
    JobRequirementChunk,
    MatchedRequirement,
    MissingRequirement,
    ResumeChunk,
    ResumeEvidence,
    SourceEvidenceRef,
    compute_source_digest,
    make_source_chunk_id,
    validate_job_match_result_payload,
)


def test_make_source_chunk_id_supports_non_latin_labels() -> None:
    chunk_id = make_source_chunk_id("resume", "项目经历", 1)

    assert chunk_id == make_source_chunk_id("resume", "项目经历", 1)
    assert chunk_id.startswith("resume:section_")
    assert chunk_id.endswith(":001")
    ResumeChunk(
        chunk_id=chunk_id,
        resume_version_id="resume_version_1",
        section_label="项目经历",
        text="负责 AI 面试工作流建设。",
    )


def _source_bundle() -> JobMatchSourceBundle:
    resume_chunks = [
        ResumeChunk(
            chunk_id="resume:summary:001",
            resume_version_id="resume_version_1",
            section_label="summary",
            text="Built interview workflow automation for SaaS hiring teams.",
        ),
        ResumeChunk(
            chunk_id="resume:skill:001",
            resume_version_id="resume_version_1",
            section_label="skills",
            text="Python, FastAPI, React, PostgreSQL.",
        ),
    ]
    job_chunks = [
        JobRequirementChunk(
            chunk_id="job:requirement:001",
            job_version_id="job_version_1",
            requirement_type="requirement",
            text="Requires Python and FastAPI experience.",
        ),
        JobRequirementChunk(
            chunk_id="job:responsibility:001",
            job_version_id="job_version_1",
            requirement_type="responsibility",
            text="Own backend APIs for candidate assessment workflows.",
        ),
    ]
    return JobMatchSourceBundle(
        resume_chunks=resume_chunks,
        job_requirement_chunks=job_chunks,
        source_digest=compute_source_digest(resume_chunks, job_chunks),
    )


def _valid_result() -> JobMatchResultPayload:
    evidence = [SourceEvidenceRef(chunk_id="resume:skill:001")]
    return JobMatchResultPayload(
        overall_score=82,
        overall_level="strong_match",
        confidence=ConfidenceLevel.HIGH,
        summary="Strong match with direct backend and workflow evidence.",
        dimension_scores=[
            DimensionScore(
                key="requirement_alignment",
                score=25,
                max_score=30,
                rationale="Core backend requirement is supported.",
                supporting_evidence=evidence,
                gaps=[],
                confidence=ConfidenceLevel.HIGH,
            ),
            DimensionScore(
                key="experience_evidence",
                score=20,
                max_score=25,
                rationale="Relevant workflow experience is supported.",
                supporting_evidence=evidence,
                gaps=[],
                confidence=ConfidenceLevel.HIGH,
            ),
            DimensionScore(
                key="skill_coverage",
                score=17,
                max_score=20,
                rationale="Core skills are supported.",
                supporting_evidence=evidence,
                gaps=[],
                confidence=ConfidenceLevel.HIGH,
            ),
            DimensionScore(
                key="gap_risk",
                score=12,
                max_score=15,
                rationale="Higher gap_risk score means lower uncovered-gap risk.",
                supporting_evidence=evidence,
                gaps=["No explicit enterprise-scale evidence."],
                confidence=ConfidenceLevel.MEDIUM,
            ),
            DimensionScore(
                key="readiness_actions",
                score=8,
                max_score=10,
                rationale="Follow-up actions are clear.",
                supporting_evidence=evidence,
                gaps=[],
                confidence=ConfidenceLevel.MEDIUM,
            ),
        ],
        matched_requirements=[
            MatchedRequirement(
                requirement_chunk_id="job:requirement:001",
                resume_evidence_chunk_ids=["resume:skill:001"],
                rationale="The resume names Python and FastAPI.",
                confidence=ConfidenceLevel.HIGH,
            )
        ],
        missing_requirements=[],
        resume_evidence=[
            ResumeEvidence(
                chunk_id="resume:skill:001",
                summary="Resume lists Python and FastAPI.",
                confidence=ConfidenceLevel.HIGH,
            )
        ],
        risk_flags=[],
        interview_focus=["Probe backend API ownership depth."],
        suggested_questions=["Which FastAPI services did you own end to end?"],
        markdown_report="# Job Match\n\nStrong match.",
    )


def test_valid_source_bundle_passes_validation() -> None:
    bundle = _source_bundle()

    assert bundle.resume_chunks[0].source_type == "resume"
    assert bundle.job_requirement_chunks[0].source_type == "job"
    assert bundle.source_digest == compute_source_digest(
        bundle.resume_chunks, bundle.job_requirement_chunks
    )


def test_valid_job_match_result_payload_passes_validation() -> None:
    result = validate_job_match_result_payload(_valid_result(), _source_bundle())

    assert result.overall_score == 82
    assert result.overall_level == "strong_match"
    assert tuple(score.key for score in result.dimension_scores) == JOB_MATCH_V1_DIMENSION_KEYS


@pytest.mark.parametrize("score", [-1, 101])
def test_overall_score_out_of_range_fails(score: int) -> None:
    with pytest.raises(ValidationError):
        JobMatchResultPayload(
            **(_valid_result().model_dump() | {"overall_score": score})
        )


def test_unknown_chunk_id_fails_source_ref_validation() -> None:
    result = _valid_result()
    result.dimension_scores[0].supporting_evidence = [
        SourceEvidenceRef(chunk_id="resume:missing:001")
    ]

    with pytest.raises(ValueError, match="unknown chunk_id"):
        validate_job_match_result_payload(result, _source_bundle())


def test_resume_evidence_cannot_reference_job_chunk() -> None:
    result = _valid_result()
    result.resume_evidence = [
        ResumeEvidence(
            chunk_id="job:requirement:001",
            summary="Wrong source type.",
            confidence=ConfidenceLevel.MEDIUM,
        )
    ]

    with pytest.raises(ValueError, match="resume evidence"):
        validate_job_match_result_payload(result, _source_bundle())


def test_matched_requirements_cannot_reference_resume_chunk_as_requirement() -> None:
    result = _valid_result()
    result.matched_requirements = [
        MatchedRequirement(
            requirement_chunk_id="resume:summary:001",
            resume_evidence_chunk_ids=["resume:skill:001"],
            rationale="Wrong source type.",
            confidence=ConfidenceLevel.MEDIUM,
        )
    ]

    with pytest.raises(ValueError, match="matched requirement"):
        validate_job_match_result_payload(result, _source_bundle())


def test_matched_requirement_unknown_job_chunk_fails() -> None:
    result = _valid_result()
    result.matched_requirements = [
        MatchedRequirement(
            requirement_chunk_id="job:missing:001",
            resume_evidence_chunk_ids=["resume:skill:001"],
            rationale="Unknown job chunk.",
            confidence=ConfidenceLevel.HIGH,
        )
    ]

    with pytest.raises(ValueError, match="unknown chunk_id"):
        validate_job_match_result_payload(result, _source_bundle())


def test_missing_required_dimension_fails_scoring_validation() -> None:
    result = _valid_result()
    result.dimension_scores = [
        score for score in result.dimension_scores if score.key != "readiness_actions"
    ]

    with pytest.raises(ValueError, match="missing required dimension"):
        validate_job_match_result_payload(result, _source_bundle())


def test_unknown_dimension_fails_scoring_validation() -> None:
    result = _valid_result()
    result.dimension_scores[-1] = result.dimension_scores[-1].model_copy(
        update={"key": "unknown_dimension"}
    )

    with pytest.raises(ValueError, match="unknown dimension"):
        validate_job_match_result_payload(result, _source_bundle())


def test_duplicate_dimension_fails_scoring_validation() -> None:
    result = _valid_result()
    result.dimension_scores[-1] = result.dimension_scores[-1].model_copy(
        update={"key": "gap_risk"}
    )

    with pytest.raises(ValueError, match="duplicate dimension"):
        validate_job_match_result_payload(result, _source_bundle())


def test_dimension_max_score_total_must_equal_100() -> None:
    result = _valid_result()
    result.dimension_scores[-1] = result.dimension_scores[-1].model_copy(
        update={"max_score": 9}
    )

    with pytest.raises(ValueError, match="max_score total"):
        validate_job_match_result_payload(result, _source_bundle())


def test_dimension_score_total_must_match_overall_score() -> None:
    result = _valid_result()
    result.dimension_scores[-1] = result.dimension_scores[-1].model_copy(
        update={"score": 7}
    )

    with pytest.raises(ValueError, match="score total"):
        validate_job_match_result_payload(result, _source_bundle())


def test_dimension_score_above_max_score_fails() -> None:
    with pytest.raises(ValidationError, match="dimension score"):
        DimensionScore(
            key="skill_coverage",
            score=21,
            max_score=20,
            rationale="Score exceeds dimension max.",
            supporting_evidence=[SourceEvidenceRef(chunk_id="resume:skill:001")],
            gaps=[],
            confidence=ConfidenceLevel.HIGH,
        )


def test_overall_level_mismatch_fails_scoring_validation() -> None:
    with pytest.raises(ValidationError, match="overall_level"):
        JobMatchResultPayload(
            **(_valid_result().model_dump() | {"overall_level": "medium_match"})
        )


def test_high_confidence_payload_without_any_evidence_fails() -> None:
    payload = _valid_result().model_dump()
    payload["dimension_scores"] = [
        {
            "key": "experience_evidence",
            "score": 18,
            "max_score": 25,
            "rationale": "Evidence is intentionally omitted.",
            "supporting_evidence": [],
            "gaps": [],
            "confidence": ConfidenceLevel.MEDIUM,
        }
    ]
    payload["matched_requirements"] = []
    payload["resume_evidence"] = []

    with pytest.raises(ValidationError, match="requires evidence"):
        JobMatchResultPayload(**payload)


def test_medium_confidence_dimension_requires_evidence_or_gap() -> None:
    with pytest.raises(ValidationError, match="medium confidence"):
        DimensionScore(
            key="gap_risk",
            score=10,
            max_score=15,
            rationale="Medium confidence cannot be unsupported.",
            supporting_evidence=[],
            gaps=[],
            confidence=ConfidenceLevel.MEDIUM,
        )


def test_insufficient_confidence_requires_insufficient_evidence_level() -> None:
    with pytest.raises(ValidationError):
        JobMatchResultPayload(
            **(
                _valid_result().model_dump()
                | {"confidence": ConfidenceLevel.INSUFFICIENT}
            )
        )

    result = JobMatchResultPayload(
        **(
            _valid_result().model_dump()
            | {
                "confidence": ConfidenceLevel.INSUFFICIENT,
                "overall_level": "insufficient_evidence",
            }
        )
    )

    assert result.overall_level == "insufficient_evidence"


def test_gap_risk_score_higher_means_lower_gap_risk() -> None:
    gap_risk = next(score for score in _valid_result().dimension_scores if score.key == "gap_risk")

    assert gap_risk.score == 12
    assert "lower" in gap_risk.rationale


def test_missing_requirement_cannot_reference_resume_chunk_as_primary_source() -> None:
    result = _valid_result()
    result.missing_requirements = [
        MissingRequirement(
            requirement_chunk_id="resume:summary:001",
            reason="Wrong source type.",
            confidence=ConfidenceLevel.MEDIUM,
        )
    ]

    with pytest.raises(ValueError, match="missing requirement"):
        validate_job_match_result_payload(result, _source_bundle())


def test_source_digest_is_stable_for_same_input() -> None:
    bundle = _source_bundle()

    assert compute_source_digest(bundle.resume_chunks, bundle.job_requirement_chunks) == compute_source_digest(
        bundle.resume_chunks, bundle.job_requirement_chunks
    )


def test_source_digest_changes_when_source_content_changes() -> None:
    bundle = _source_bundle()
    changed_resume_chunks = [
        chunk.model_copy(update={"text": "Different source content."})
        if chunk.chunk_id == "resume:summary:001"
        else chunk
        for chunk in bundle.resume_chunks
    ]

    assert compute_source_digest(changed_resume_chunks, bundle.job_requirement_chunks) != bundle.source_digest
