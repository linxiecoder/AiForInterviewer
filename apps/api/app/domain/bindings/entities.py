"""Resume-job binding domain entities for F5-M2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ResumeJobBinding:
    binding_id: str
    owner_id: str
    resume_id: str
    job_id: str
    resume_version_id: str
    job_version_id: str
    status: str
    record_version: int
    created_at: datetime
    updated_at: datetime
    unbound_at: datetime | None = None
    unbound_by: str | None = None
