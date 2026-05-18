"""Job domain entities for F5-M2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Job:
    job_id: str
    owner_id: str
    title: str
    company: str | None
    department: str | None
    application_status: str
    status: str
    current_version_id: str
    record_version: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None


@dataclass(frozen=True)
class JobVersion:
    job_version_id: str
    owner_id: str
    job_id: str
    version_number: int
    responsibilities: list[str]
    requirements: list[str]
    other_notes: str | None = None
    status: str = "current"
    created_at: datetime | None = None
