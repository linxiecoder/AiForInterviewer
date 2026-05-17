"""Job API DTO skeletons."""

from pydantic import BaseModel, Field

from app.schemas.refs import VersionRef


class CreateJobRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    jd_text: str = Field(min_length=1)


class UpdateJobRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    jd_text: str | None = Field(default=None, min_length=1)
    base_version_ref: VersionRef


class JobBindingSummary(BaseModel):
    active_binding_count: int = 0
    latest_binding_id: str | None = None


class JobMatchSummary(BaseModel):
    display_score: int | None = Field(default=None, ge=0, le=100)
    score_scale: str = "0_100_product_scale"
    score_version: str | None = None
    rubric_version: str | None = None


class JobSummary(BaseModel):
    job_id: str
    title: str
    status: str
    current_version_ref: VersionRef
    binding_summary: JobBindingSummary | None = None
    latest_match_summary: JobMatchSummary | None = None


class JobDetail(JobSummary):
    jd_text: str

