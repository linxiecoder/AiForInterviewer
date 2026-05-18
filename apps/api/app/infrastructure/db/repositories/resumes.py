"""Resume repository placeholder."""

from copy import deepcopy

from app.application.resumes.ports import ResumeRepository
from app.domain.resumes.entities import Resume
from app.domain.shared.refs import ResourceRef


class SqlAlchemyResumeRepository(ResumeRepository):
    _resumes: dict[str, Resume] = {}

    def get(self, resume_id: str) -> Resume | None:
        found = self._resumes.get(resume_id)
        return deepcopy(found) if found is not None else None

    def get_ref(self, resume_id: str) -> ResourceRef | None:
        found = self._resumes.get(resume_id)
        if found is None:
            return None
        return ResourceRef(resource_type="resume", resource_id=resume_id)

    def list_by_owner(self, owner_id: str) -> list[Resume]:
        return [
            deepcopy(resume)
            for resume in self._resumes.values()
            if resume.owner_ref.owner_id == owner_id
        ]

    def add(self, resume: Resume) -> None:
        self._resumes[resume.resume_id] = deepcopy(resume)

    @classmethod
    def clear_state(cls) -> None:
        cls._resumes.clear()
