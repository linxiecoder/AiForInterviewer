"""Job commands."""

from dataclasses import dataclass
from app.domain.shared.refs import VersionRef


@dataclass(frozen=True)
class CreateJobCommand:
    title: str
    owner_id: str
    company: str | None
    department: str | None
    responsibilities: list[str]
    requirements: list[str]
    other_notes: str | None
    application_status: str | None


@dataclass(frozen=True)
class UpdateJobCommand:
    owner_id: str
    title: str | None
    company: str | None
    department: str | None
    responsibilities: list[str] | None
    requirements: list[str] | None
    other_notes: str | None
    application_status: str | None
    status: str | None
    base_version_ref: VersionRef | None
    record_version: int | None
