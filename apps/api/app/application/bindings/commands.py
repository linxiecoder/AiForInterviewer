"""Binding command objects."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.shared.refs import VersionRef


@dataclass(frozen=True)
class CreateBindingCommand:
    owner_id: str
    resume_id: str
    job_id: str
    resume_version_id: str | None
    job_version_id: str | None


@dataclass(frozen=True)
class DeleteBindingCommand:
    owner_id: str
    base_version_ref: VersionRef | None
    record_version: int | None
    reason: str | None = None


@dataclass(frozen=True)
class RegisterResumeVersionCommand:
    owner_id: str
    resume_id: str
    resume_version_id: str
