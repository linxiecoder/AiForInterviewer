"""API response envelope schemas."""

from typing import Any

from pydantic import BaseModel, Field

from app.domain.shared.enums import (
    ApiStatus,
    ConfidenceLevel,
    PassTendencyLevel,
    RiskLevel,
    SourceAvailability,
)
from app.schemas.refs import EvidenceRefSchema, LowConfidenceFlagSchema, ResourceRef, TraceRefSchema


class ApiSuccessEnvelope(BaseModel):
    request_id: str
    trace_id: str
    status: ApiStatus
    resource_type: str
    resource_ref: ResourceRef | None = None
    data: Any | None = None
    meta: dict[str, Any] | None = None
    candidate_refs: list[ResourceRef] = Field(default_factory=list)
    suggestion_refs: list[ResourceRef] = Field(default_factory=list)
    confirmation_required: bool | None = None
    ai_task_id: str | None = None
    validation_result_ref: ResourceRef | None = None
    low_confidence_flags: list[LowConfidenceFlagSchema] = Field(default_factory=list)
    source_availability: SourceAvailability | None = None
    evidence_refs: list[EvidenceRefSchema] = Field(default_factory=list)
    trace_refs: list[TraceRefSchema] = Field(default_factory=list)
    score_version: str | None = None
    rubric_version: str | None = None
    confidence_level: ConfidenceLevel | None = None
    pass_tendency_level: PassTendencyLevel | None = None
    risk_level: RiskLevel | None = None
    next_actions: list[str] = Field(default_factory=list)


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    retryable: bool
    user_action: str | None = None
    audit_event_ref: ResourceRef | None = None


class ApiErrorEnvelope(BaseModel):
    request_id: str
    trace_id: str
    error: ApiError

