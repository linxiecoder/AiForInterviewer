"""Resume domain entities."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.shared.refs import OwnerRef, VersionRef


@dataclass(frozen=True)
class Resume:
    resume_id: str
    owner_ref: OwnerRef
    current_version_ref: VersionRef
    status: str
    title: str | None = None
    file_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class ResumeVersion:
    resume_version_id: str
    owner_id: str
    resume_id: str
    version_number: int
    markdown_text: str
    status: str
    created_at: datetime | None = None
