"""Binding API DTO skeletons."""

from pydantic import BaseModel

from app.schemas.refs import VersionRef


class CreateBindingRequest(BaseModel):
    resume_version_ref: VersionRef
    job_version_ref: VersionRef


class BindingSummary(BaseModel):
    binding_id: str
    resume_version_ref: VersionRef
    job_version_ref: VersionRef
    status: str

