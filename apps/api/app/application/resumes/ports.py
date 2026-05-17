"""Resume repository ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class ResumeRepository(Protocol):
    def get_ref(self, resume_id: str) -> ResourceRef | None: ...

