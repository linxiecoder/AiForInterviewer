"""Binding API DTOs."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.refs import VersionRef, OwnerRef


class CreateBindingRequest(BaseModel):
    resume_id: str
    job_id: str
    resume_version_id: str | None = None
    job_version_id: str | None = None


class DeleteBindingRequest(BaseModel):
    base_version_ref: VersionRef | None = None
    record_version: int | None = None
    reason: str | None = None


class JobResumeBindingResponse(BaseModel):
    binding_id: str
    resume_ref: VersionRef
    job_ref: VersionRef
    binding_status: str
    created_at: datetime
    unbound_at: datetime | None = None
    unbound_by: OwnerRef | None = None
    record_version: int
    resume_job_binding_id: str | None = None
    preserved_history_refs: list[str] = Field(default_factory=list)
    affected_default_entry_summary: str | None = None


# Backward compatible alias used by older placeholders and tests.
class BindingSummary(JobResumeBindingResponse):
    pass
