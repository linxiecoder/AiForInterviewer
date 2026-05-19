"""Resume commands."""

from dataclasses import dataclass

from app.domain.shared.refs import VersionRef


@dataclass(frozen=True)
class CreateResumeCommand:
    owner_id: str
    title: str
    markdown_text: str


@dataclass(frozen=True)
class UpdateResumeCommand:
    owner_id: str
    resume_id: str
    title: str
    markdown_text: str
    base_version_ref: VersionRef
