"""Scoring API DTO skeletons."""

from pydantic import BaseModel, Field

from app.domain.shared.enums import ConfidenceLevel, PassTendencyLevel, RiskLevel, ScoreType, ValidationStatus
from app.schemas.refs import EvidenceRefSchema, LowConfidenceFlagSchema, ResourceRef, TraceRefSchema


class ScoreDimensionResponse(BaseModel):
    dimension_key: str
    dimension_score: int = Field(ge=0, le=100)
    weight: int = Field(ge=0, le=100)
    evidence_refs: list[EvidenceRefSchema] = Field(default_factory=list)


class ScoreResultResponse(BaseModel):
    score_result_id: str
    score_type: ScoreType
    target_ref: ResourceRef
    score_value: int = Field(ge=0, le=100)
    score_scale: str = "0_100_product_scale"
    score_version: str
    rubric_version: str
    validation_status: ValidationStatus
    confidence_level: ConfidenceLevel
    pass_tendency_level: PassTendencyLevel | None = None
    risk_level: RiskLevel | None = None
    dimension_scores: list[ScoreDimensionResponse] = Field(default_factory=list)
    evidence_refs: list[EvidenceRefSchema] = Field(default_factory=list)
    trace_refs: list[TraceRefSchema] = Field(default_factory=list)
    low_confidence_flags: list[LowConfidenceFlagSchema] = Field(default_factory=list)
    generated_by_task_id: str
    allowed_as_formal_score: bool

