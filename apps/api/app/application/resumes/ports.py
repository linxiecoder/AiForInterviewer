"""Resume repository ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef
from app.domain.resumes.entities import Resume, ResumeVersion


class ResumeRepository(Protocol):
    def get_ref(self, resume_id: str) -> ResourceRef | None: ...

    def get(self, resume_id: str) -> Resume | None: ...

    def list_by_owner(self, owner_id: str) -> list[Resume]: ...

    def add(self, resume: Resume) -> None: ...

    def add_version(self, version: ResumeVersion) -> None: ...

    def create_with_version(self, resume: Resume, version: ResumeVersion) -> None: ...
