"""Binding commands."""

from dataclasses import dataclass

from app.domain.shared.refs import VersionRef


@dataclass(frozen=True)
class CreateBindingCommand:
    resume_version_ref: VersionRef
    job_version_ref: VersionRef

