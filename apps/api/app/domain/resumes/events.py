"""Resume domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResumeVersionCreated:
    resume_id: str
    version_id: str

