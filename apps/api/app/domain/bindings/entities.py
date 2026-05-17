"""Binding domain entities."""

from dataclasses import dataclass

from app.domain.shared.refs import OwnerRef, VersionRef


@dataclass(frozen=True)
class ResumeJobBinding:
    binding_id: str
    owner_ref: OwnerRef
    resume_version_ref: VersionRef
    job_version_ref: VersionRef
    status: str

