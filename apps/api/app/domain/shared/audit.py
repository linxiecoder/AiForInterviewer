"""Audit concepts shared by domain modules."""

from dataclasses import dataclass

from app.domain.shared.refs import OwnerRef, ResourceRef, TraceRef


@dataclass(frozen=True)
class AuditConcept:
    actor_ref: OwnerRef
    target_ref: ResourceRef
    action: str
    trace_ref: TraceRef

