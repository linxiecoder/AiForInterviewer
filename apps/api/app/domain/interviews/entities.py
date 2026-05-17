"""Interview domain entities."""

from dataclasses import dataclass

from app.domain.shared.refs import OwnerRef, ResourceRef


@dataclass(frozen=True)
class InterviewSession:
    session_id: str
    owner_ref: OwnerRef
    binding_ref: ResourceRef
    mode: str
    status: str

