"""Job API DTOs."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from app.domain.shared.enums import ApiStatus
from app.schemas.refs import VersionRef


class CreateJobRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    company: str | None = Field(default=None, max_length=160)
    department: str | None = Field(default=None, max_length=160)
    responsibilities: list[str] = Field(min_length=1)
    requirements: list[str] = Field(min_length=1)
    other_notes: str | None = None
    application_status: str | None = Field(default="draft", min_length=1, max_length=32)


class UpdateJobRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    company: str | None = Field(default=None, max_length=160)
    department: str | None = Field(default=None, max_length=160)
    responsibilities: list[str] | None = None
    requirements: list[str] | None = None
    other_notes: str | None = None
    application_status: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, max_length=64)
    base_version_ref: VersionRef | None = None
    record_version: int | None = None


class JobBindingSummary(BaseModel):
    status: str
    resume_job_binding_id: str | None = None
    resume_id: str | None = None
    resume_title: str | None = None
    resume_version_ref: VersionRef | None = None
    bound_at: datetime | None = None


class JobMatchSummary(BaseModel):
    status: str = "match_not_generated"
    analysis_id: str | None = None
    display_score: int | None = Field(default=None, ge=0, le=100)
    score_scale: str = "0_100_product_scale"
    score_version: str | None = None
    rubric_version: str | None = None
    confidence_level: str | None = None
    summary_text: str | None = None
    generated_at: datetime | None = None
    stale_reason: str | None = None


class JobSummary(BaseModel):
    job_id: str
    title: str
    company: str | None
    department: str | None = None
    application_status: str
    current_version_ref: VersionRef
    archived_at: datetime | None = None
    binding_summary: JobBindingSummary
    latest_match_summary: JobMatchSummary
    status: str
    record_version: int
    created_at: datetime
    updated_at: datetime


class JobDetail(JobSummary):
    department: str | None = None
    responsibilities: list[str]
    requirements: list[str]
    other_notes: str | None = None
