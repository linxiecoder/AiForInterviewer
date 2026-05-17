"""Resume domain ports."""

from typing import Protocol

from app.domain.resumes.entities import Resume


class ResumeReader(Protocol):
    def get(self, resume_id: str) -> Resume | None: ...

