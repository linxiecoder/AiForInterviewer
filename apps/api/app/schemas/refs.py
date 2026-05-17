"""Shared API reference schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.shared.enums import ConfidenceLevel, SourceAvailability


class ResourceRef(BaseModel):
    resource_type: str
    resource_id: str


class VersionRef(BaseModel):
    resource_type: str
    resource_id: str
    version_id: str


class OwnerRef(BaseModel):
    owner_id: str


class EvidenceRefSchema(BaseModel):
    evidence_ref_id: str
    source_ref: ResourceRef
    version_ref: VersionRef | None = None
    summary: str | None = None
    confidence_level: ConfidenceLevel | None = None


class TraceRefSchema(BaseModel):
    trace_ref_id: str
    trace_type: str
    created_at: datetime
    redaction_boundary: str = "no raw payload"


class SourceAvailabilitySchema(BaseModel):
    source_ref: ResourceRef
    status: SourceAvailability
    can_read_for_generation: bool
    display_summary: str | None = None


class LowConfidenceFlagSchema(BaseModel):
    flag_id: str
    reason: str
    impact_scope: str = Field(max_length=240)
    recommended_action: str | None = None


class UserConfirmationRef(BaseModel):
    confirmation_id: str
    actor_ref: OwnerRef
    target_ref: ResourceRef | TraceRefSchema
    action_type: str
    action_result: str
    audit_event_ref: TraceRefSchema

