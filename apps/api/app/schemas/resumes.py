"""Resume API DTO skeletons."""

from pydantic import BaseModel, Field

from app.schemas.refs import VersionRef


class CreateResumeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    markdown_text: str = Field(min_length=1)


class UpdateResumeRequest(BaseModel):
    markdown_text: str = Field(min_length=1)
    base_version_ref: VersionRef
    edit_reason: str | None = Field(default=None, max_length=240)


class ResumeSummary(BaseModel):
    resume_id: str
    title: str
    status: str
    current_version_ref: VersionRef


class ResumeDetail(ResumeSummary):
    markdown_text: str
    derived_outline: dict[str, object] | None = None

