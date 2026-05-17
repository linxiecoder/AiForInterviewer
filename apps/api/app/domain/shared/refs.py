"""Typed reference value objects shared across modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.shared.clock import utc_now
from app.domain.shared.enums import ConfidenceLevel, SourceAvailability


@dataclass(frozen=True)
class ResourceRef:
    resource_type: str
    resource_id: str


@dataclass(frozen=True)
class VersionRef:
    resource_type: str
    resource_id: str
    version_id: str


@dataclass(frozen=True)
class OwnerRef:
    owner_id: str


@dataclass(frozen=True)
class EvidenceRef:
    evidence_ref_id: str
    source_ref: ResourceRef
    version_ref: VersionRef | None = None
    summary: str | None = None
    confidence_level: ConfidenceLevel | None = None


@dataclass(frozen=True)
class TraceRef:
    trace_ref_id: str
    trace_type: str
    created_at: datetime = field(default_factory=utc_now)
    redaction_boundary: str = "no raw payload"


@dataclass(frozen=True)
class UserConfirmationRef:
    confirmation_id: str
    actor_ref: OwnerRef
    target_ref: ResourceRef | TraceRef
    action_type: str
    action_result: str
    audit_event_ref: TraceRef


@dataclass(frozen=True)
class SourceAvailabilityRef:
    source_ref: ResourceRef
    status: SourceAvailability
    can_read_for_generation: bool
    display_summary: str | None = None

