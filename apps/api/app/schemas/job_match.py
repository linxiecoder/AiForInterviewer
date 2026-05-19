"""Job match source bundle and result contract schemas."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.shared.enums import ConfidenceLevel, StrEnum


JOB_MATCH_V1_DIMENSION_KEYS = (
    "requirement_alignment",
    "experience_evidence",
    "skill_coverage",
    "gap_risk",
    "readiness_actions",
)


class JobMatchOverallLevel(StrEnum):
    STRONG_MATCH = "strong_match"
    MEDIUM_MATCH = "medium_match"
    WEAK_MATCH = "weak_match"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class JobMatchContractValidationError(ValueError):
    """Raised when a payload references sources outside the current bundle."""


class ResumeChunk(BaseModel):
    chunk_id: str = Field(pattern=r"^resume:[a-z0-9_]+:\d{3}$")
    source_type: Literal["resume"] = "resume"
    resume_version_id: str = Field(min_length=1)
    section_label: str = Field(min_length=1)
    text: str = Field(min_length=1)
    locator: str | None = None

    @field_validator("text", "section_label", "resume_version_id")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class JobRequirementChunk(BaseModel):
    chunk_id: str = Field(pattern=r"^job:[a-z0-9_]+:\d{3}$")
    source_type: Literal["job"] = "job"
    job_version_id: str = Field(min_length=1)
    requirement_type: str = Field(min_length=1)
    text: str = Field(min_length=1)
    locator: str | None = None

    @field_validator("text", "requirement_type", "job_version_id")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class JobMatchSourceBundle(BaseModel):
    resume_chunks: list[ResumeChunk] = Field(min_length=1)
    job_requirement_chunks: list[JobRequirementChunk] = Field(min_length=1)
    source_digest: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_digest_and_unique_chunks(self) -> "JobMatchSourceBundle":
        chunk_ids = [
            chunk.chunk_id
            for chunk in [*self.resume_chunks, *self.job_requirement_chunks]
        ]
        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("source bundle chunk_id values must be unique")
        expected_digest = compute_source_digest(
            self.resume_chunks, self.job_requirement_chunks
        )
        if self.source_digest != expected_digest:
            raise ValueError("source_digest does not match source bundle content")
        return self


class SourceEvidenceRef(BaseModel):
    chunk_id: str = Field(min_length=1)
    quote: str | None = None


class DimensionScore(BaseModel):
    key: str = Field(min_length=1)
    score: int = Field(ge=0)
    max_score: int = Field(gt=0, le=100)
    rationale: str = Field(min_length=1)
    supporting_evidence: list[SourceEvidenceRef] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel

    @model_validator(mode="after")
    def _validate_score_and_evidence(self) -> "DimensionScore":
        if self.score > self.max_score:
            raise ValueError("dimension score must not exceed max_score")
        if self.confidence is ConfidenceLevel.HIGH and not self.supporting_evidence:
            raise ValueError("high confidence dimension requires supporting evidence")
        if (
            self.confidence is ConfidenceLevel.MEDIUM
            and not self.supporting_evidence
            and not self.gaps
        ):
            raise ValueError("medium confidence dimension requires evidence or gaps")
        return self


class MatchedRequirement(BaseModel):
    requirement_chunk_id: str = Field(min_length=1)
    resume_evidence_chunk_ids: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)
    confidence: ConfidenceLevel

    @model_validator(mode="after")
    def _validate_high_confidence_evidence(self) -> "MatchedRequirement":
        if self.confidence is ConfidenceLevel.HIGH and not self.resume_evidence_chunk_ids:
            raise ValueError("high confidence match requires resume evidence")
        return self


class MissingRequirement(BaseModel):
    requirement_chunk_id: str | None = None
    reason: str = Field(min_length=1)
    confidence: ConfidenceLevel
    evidence_insufficient: bool = False

    @model_validator(mode="after")
    def _validate_missing_source(self) -> "MissingRequirement":
        if self.requirement_chunk_id is None and not self.evidence_insufficient:
            raise ValueError(
                "missing requirement without a requirement_chunk_id must be evidence_insufficient"
            )
        return self


class ResumeEvidence(BaseModel):
    chunk_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    confidence: ConfidenceLevel


class RiskFlag(BaseModel):
    risk_type: str = Field(min_length=1)
    description: str = Field(min_length=1)
    severity: Literal["low", "medium", "high"]
    supporting_evidence: list[SourceEvidenceRef] = Field(default_factory=list)


class JobMatchResultPayload(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    overall_level: JobMatchOverallLevel
    confidence: ConfidenceLevel
    summary: str = Field(min_length=1)
    dimension_scores: list[DimensionScore] = Field(min_length=1)
    matched_requirements: list[MatchedRequirement] = Field(default_factory=list)
    missing_requirements: list[MissingRequirement] = Field(default_factory=list)
    resume_evidence: list[ResumeEvidence] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    interview_focus: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    markdown_report: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_overall_level(self) -> "JobMatchResultPayload":
        if self.confidence is ConfidenceLevel.INSUFFICIENT:
            if self.overall_level is not JobMatchOverallLevel.INSUFFICIENT_EVIDENCE:
                raise ValueError(
                    "insufficient confidence requires insufficient_evidence level"
                )
            return self

        if self.overall_level is JobMatchOverallLevel.INSUFFICIENT_EVIDENCE:
            return self

        if self.overall_score >= 80:
            expected = JobMatchOverallLevel.STRONG_MATCH
        elif self.overall_score >= 60:
            expected = JobMatchOverallLevel.MEDIUM_MATCH
        else:
            expected = JobMatchOverallLevel.WEAK_MATCH

        if self.overall_level is not expected:
            raise ValueError("overall_level does not match overall_score threshold")
        return self

    @model_validator(mode="after")
    def _validate_high_confidence_has_evidence(self) -> "JobMatchResultPayload":
        if self.confidence is not ConfidenceLevel.HIGH:
            return self
        has_evidence = any(score.supporting_evidence for score in self.dimension_scores)
        has_evidence = has_evidence or bool(self.resume_evidence)
        has_evidence = has_evidence or any(
            match.resume_evidence_chunk_ids for match in self.matched_requirements
        )
        if not has_evidence:
            raise ValueError("high confidence payload requires evidence")
        return self

    @model_validator(mode="after")
    def _validate_insufficient_evidence_signal(self) -> "JobMatchResultPayload":
        has_insufficient_evidence = any(
            missing.evidence_insufficient for missing in self.missing_requirements
        )
        if not has_insufficient_evidence:
            return self
        if (
            self.confidence is not ConfidenceLevel.INSUFFICIENT
            and self.overall_level is not JobMatchOverallLevel.INSUFFICIENT_EVIDENCE
        ):
            raise ValueError(
                "evidence_insufficient requires insufficient confidence or overall level"
            )
        return self


class CreateJobMatchAnalysisRequest(BaseModel):
    resume_job_binding_id: str = Field(min_length=1)


class JobMatchAnalysisResponse(BaseModel):
    analysis_id: str
    resume_job_binding_id: str
    resume_id: str
    resume_version_id: str
    job_id: str
    job_version_id: str
    status: Literal["completed", "failed"]
    overall_score: int | None = Field(default=None, ge=0, le=100)
    overall_level: JobMatchOverallLevel | None = None
    confidence: ConfidenceLevel | None = None
    result_payload: JobMatchResultPayload
    markdown_report_text: str | None = None
    score_rule_version: str
    prompt_version: str
    model_name: str
    source_digest: str
    created_at: datetime
    updated_at: datetime


def compute_source_digest(
    resume_chunks: list[ResumeChunk], job_requirement_chunks: list[JobRequirementChunk]
) -> str:
    """Return a stable digest for the normalized source bundle content."""

    payload = {
        "resume_chunks": sorted(
            [_dump_model(chunk) for chunk in resume_chunks],
            key=lambda item: item["chunk_id"],
        ),
        "job_requirement_chunks": sorted(
            [_dump_model(chunk) for chunk in job_requirement_chunks],
            key=lambda item: item["chunk_id"],
        ),
    }
    normalized = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(normalized.encode('utf-8')).hexdigest()}"


def make_source_chunk_id(source_type: Literal["resume", "job"], label: str, index: int) -> str:
    """Build a predictable source chunk id such as resume:summary:001."""

    if index < 1:
        raise ValueError("chunk index must be >= 1")
    stripped_label = label.strip()
    if not stripped_label:
        raise ValueError("chunk label must not be blank")
    normalized_label = re.sub(r"[^a-z0-9_]+", "_", stripped_label.lower()).strip("_")
    if not normalized_label:
        label_digest = hashlib.sha256(stripped_label.encode("utf-8")).hexdigest()[:12]
        normalized_label = f"section_{label_digest}"
    return f"{source_type}:{normalized_label}:{index:03d}"


def validate_job_match_result_payload(
    payload: JobMatchResultPayload | dict,
    source_bundle: JobMatchSourceBundle,
) -> JobMatchResultPayload:
    """Validate result payload schema and all evidence refs against a source bundle."""

    result = (
        payload
        if isinstance(payload, JobMatchResultPayload)
        else JobMatchResultPayload.model_validate(payload)
    )
    chunk_source_types = _chunk_source_types(source_bundle)
    _validate_dimension_scores(result)
    _validate_payload_confidence_consistency(result)

    for score in result.dimension_scores:
        if score.score < 0 or score.score > score.max_score:
            raise JobMatchContractValidationError(
                f"dimension score out of range: {score.key}"
            )
        if score.max_score <= 0:
            raise JobMatchContractValidationError(
                f"dimension max_score must be positive: {score.key}"
            )
        if score.confidence is ConfidenceLevel.HIGH and not score.supporting_evidence:
            raise JobMatchContractValidationError(
                f"high confidence dimension requires supporting evidence: {score.key}"
            )
        if (
            score.confidence is ConfidenceLevel.MEDIUM
            and not score.supporting_evidence
            and not score.gaps
        ):
            raise JobMatchContractValidationError(
                f"medium confidence dimension requires evidence or gaps: {score.key}"
            )
        for ref in score.supporting_evidence:
            _require_known_chunk(
                ref.chunk_id,
                chunk_source_types,
                context="supporting evidence",
            )

    for match in result.matched_requirements:
        if match.confidence is ConfidenceLevel.HIGH and not match.resume_evidence_chunk_ids:
            raise JobMatchContractValidationError(
                "high confidence matched requirement requires resume evidence"
            )
        _require_known_chunk(
            match.requirement_chunk_id,
            chunk_source_types,
            expected_source_type="job",
            context="matched requirement",
        )
        for chunk_id in match.resume_evidence_chunk_ids:
            _require_known_chunk(
                chunk_id,
                chunk_source_types,
                expected_source_type="resume",
                context="matched requirement resume evidence",
            )

    for missing in result.missing_requirements:
        if missing.requirement_chunk_id is not None:
            _require_known_chunk(
                missing.requirement_chunk_id,
                chunk_source_types,
                expected_source_type="job",
                context="missing requirement",
            )

    for evidence in result.resume_evidence:
        _require_known_chunk(
            evidence.chunk_id,
            chunk_source_types,
            expected_source_type="resume",
            context="resume evidence",
        )

    for risk in result.risk_flags:
        for ref in risk.supporting_evidence:
            _require_known_chunk(
                ref.chunk_id,
                chunk_source_types,
                context="risk flag evidence",
            )

    return result


def _dump_model(model: BaseModel) -> dict:
    return model.model_dump(mode="json", exclude_none=True)


def _chunk_source_types(source_bundle: JobMatchSourceBundle) -> dict[str, str]:
    return {
        **{chunk.chunk_id: chunk.source_type for chunk in source_bundle.resume_chunks},
        **{
            chunk.chunk_id: chunk.source_type
            for chunk in source_bundle.job_requirement_chunks
        },
    }


def _validate_dimension_scores(result: JobMatchResultPayload) -> None:
    required_keys = set(JOB_MATCH_V1_DIMENSION_KEYS)
    keys = [score.key for score in result.dimension_scores]
    duplicate_keys = sorted({key for key in keys if keys.count(key) > 1})
    if duplicate_keys:
        raise JobMatchContractValidationError(
            f"duplicate dimension key: {', '.join(duplicate_keys)}"
        )

    actual_keys = set(keys)
    unknown_keys = sorted(actual_keys - required_keys)
    if unknown_keys:
        raise JobMatchContractValidationError(
            f"unknown dimension key: {', '.join(unknown_keys)}"
        )

    missing_keys = sorted(required_keys - actual_keys)
    if missing_keys:
        raise JobMatchContractValidationError(
            f"missing required dimension: {', '.join(missing_keys)}"
        )

    max_score_total = sum(score.max_score for score in result.dimension_scores)
    if max_score_total != 100:
        raise JobMatchContractValidationError(
            f"dimension max_score total must equal 100, got {max_score_total}"
        )

    score_total = sum(score.score for score in result.dimension_scores)
    if score_total != result.overall_score:
        raise JobMatchContractValidationError(
            f"dimension score total must match overall_score, got {score_total} != {result.overall_score}"
        )


def _validate_payload_confidence_consistency(result: JobMatchResultPayload) -> None:
    if result.confidence is ConfidenceLevel.HIGH and not _has_any_evidence(result):
        raise JobMatchContractValidationError("high confidence payload requires evidence")
    if (
        result.confidence is ConfidenceLevel.MEDIUM
        and not _has_any_evidence(result)
        and not _has_any_gap(result)
    ):
        raise JobMatchContractValidationError(
            "medium confidence payload requires evidence or gaps"
        )


def _has_any_evidence(result: JobMatchResultPayload) -> bool:
    return (
        any(score.supporting_evidence for score in result.dimension_scores)
        or bool(result.resume_evidence)
        or any(match.resume_evidence_chunk_ids for match in result.matched_requirements)
        or any(risk.supporting_evidence for risk in result.risk_flags)
    )


def _has_any_gap(result: JobMatchResultPayload) -> bool:
    return (
        any(score.gaps for score in result.dimension_scores)
        or bool(result.missing_requirements)
        or bool(result.risk_flags)
    )


def _require_known_chunk(
    chunk_id: str,
    chunk_source_types: dict[str, str],
    *,
    context: str,
    expected_source_type: Literal["resume", "job"] | None = None,
) -> None:
    actual_source_type = chunk_source_types.get(chunk_id)
    if actual_source_type is None:
        raise JobMatchContractValidationError(f"{context} references unknown chunk_id: {chunk_id}")
    if expected_source_type is not None and actual_source_type != expected_source_type:
        raise JobMatchContractValidationError(
            f"{context} references {actual_source_type} chunk, expected {expected_source_type}: {chunk_id}"
        )


__all__ = [
    "DimensionScore",
    "CreateJobMatchAnalysisRequest",
    "JOB_MATCH_V1_DIMENSION_KEYS",
    "JobMatchAnalysisResponse",
    "JobMatchContractValidationError",
    "JobMatchOverallLevel",
    "JobMatchResultPayload",
    "JobMatchSourceBundle",
    "JobRequirementChunk",
    "MatchedRequirement",
    "MissingRequirement",
    "ResumeChunk",
    "ResumeEvidence",
    "RiskFlag",
    "SourceEvidenceRef",
    "compute_source_digest",
    "make_source_chunk_id",
    "validate_job_match_result_payload",
]
