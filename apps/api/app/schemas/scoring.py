"""Scoring API DTOs."""

from typing import Any

from pydantic import BaseModel, Field

from app.domain.shared.enums import ConfidenceLevel, PassTendencyLevel, RiskLevel, ScoreType, ValidationStatus
from app.schemas.refs import EvidenceRefSchema, LowConfidenceFlagSchema, ResourceRef, TraceRefSchema


class ScoreDimensionRequest(BaseModel):
    name: str = Field(max_length=80)
    score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence_links: list[dict[str, Any]] = Field(default_factory=list)


class CreateScoreResultRequest(BaseModel):
    score_type: ScoreType
    target_type: str = Field(min_length=1, max_length=80)
    target_id: str = Field(min_length=1, max_length=80)
    target_parent_type: str | None = Field(default=None, max_length=80)
    target_parent_id: str | None = Field(default=None, max_length=80)
    source_module: str | None = Field(default=None, max_length=80)
    source_event: str | None = Field(default=None, max_length=120)
    rubric_version: str = Field(min_length=1, max_length=120)
    overall_score: int | None = Field(default=None, ge=0, le=100)
    dimensions: list[ScoreDimensionRequest] = Field(min_length=1)
    evidence_links: list[dict[str, Any]] = Field(default_factory=list)
    next_action_type: str | None = Field(default=None, max_length=120)


class ScoreDimensionResponse(BaseModel):
    dimension_key: str
    dimension_score: int = Field(ge=0, le=100)
    score: int = Field(ge=0, le=100)
    weight: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence_links: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[EvidenceRefSchema] = Field(default_factory=list)


class ScoreResultResponse(BaseModel):
    score_result_id: str
    score_type: ScoreType
    target_ref: ResourceRef
    target_type: str
    target_id: str
    target_parent_ref: ResourceRef | None = None
    target_parent_type: str | None = None
    target_parent_id: str | None = None
    source_module: str | None = None
    source_event: str | None = None
    score_value: int = Field(ge=0, le=100)
    overall_score: int = Field(ge=0, le=100)
    score_scale: str = "0_100_product_scale"
    score_version: str
    rubric_version: str
    validation_status: ValidationStatus
    confidence: float = Field(ge=0, le=1)
    confidence_level: ConfidenceLevel
    pass_tendency_level: PassTendencyLevel | None = None
    risk_level: RiskLevel | None = None
    dimension_scores: list[ScoreDimensionResponse] = Field(default_factory=list)
    evidence_links: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[EvidenceRefSchema] = Field(default_factory=list)
    trace_refs: list[TraceRefSchema] = Field(default_factory=list)
    low_confidence_flags: list[LowConfidenceFlagSchema] = Field(default_factory=list)
    primary_bottleneck: str
    next_action_type: str
    generated_by_task_id: str | None = None
    allowed_as_formal_score: bool
