"""Resume domain entities."""

from dataclasses import dataclass

from app.domain.shared.refs import OwnerRef, VersionRef


@dataclass(frozen=True)
class Resume:
    resume_id: str
    owner_ref: OwnerRef
    current_version_ref: VersionRef
    status: str

