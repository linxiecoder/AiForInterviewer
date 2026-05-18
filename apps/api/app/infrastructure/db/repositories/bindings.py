"""In-memory repository implementations for resume-job bindings."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy

from app.domain.bindings.entities import ResumeJobBinding
from app.domain.bindings.ports import BindingRepository
from app.infrastructure.db.models.binding import ResumeJobBinding as BindingModel


class SqlAlchemyBindingRepository(BindingRepository):
    _bindings: dict[str, ResumeJobBinding] = {}
    _by_owner_job: dict[tuple[str, str], set[str]] = defaultdict(set)
    _resume_current_version: dict[tuple[str, str], str] = {}

    def get(self, binding_id: str) -> ResumeJobBinding | None:
        binding = self._bindings.get(binding_id)
        return deepcopy(binding) if binding is not None else None

    def add(self, binding: ResumeJobBinding) -> None:
        self._bindings[binding.binding_id] = deepcopy(binding)
        self._by_owner_job[(binding.owner_id, binding.job_id)].add(binding.binding_id)

    def update(self, binding: ResumeJobBinding) -> None:
        self._bindings[binding.binding_id] = deepcopy(binding)
        self._by_owner_job[(binding.owner_id, binding.job_id)].add(binding.binding_id)

    def list_by_owner(self, owner_id: str) -> list[ResumeJobBinding]:
        return [deepcopy(binding) for binding in self._bindings.values() if binding.owner_id == owner_id]

    def list_by_job(self, owner_id: str, job_id: str) -> list[ResumeJobBinding]:
        ids = self._by_owner_job.get((owner_id, job_id), set())
        return [deepcopy(self._bindings[binding_id]) for binding_id in ids if binding_id in self._bindings]

    def find_active_binding(self, owner_id: str, resume_id: str, job_id: str) -> ResumeJobBinding | None:
        ids = self._by_owner_job.get((owner_id, job_id), set())
        for binding_id in ids:
            binding = self._bindings.get(binding_id)
            if (
                binding is not None
                and binding.resume_id == resume_id
                and binding.owner_id == owner_id
                and binding.job_id == job_id
                and binding.status == "active"
            ):
                return deepcopy(binding)
        return None

    def register_resume(self, owner_id: str, resume_id: str, resume_version_id: str) -> None:
        self._resume_current_version[(owner_id, resume_id)] = resume_version_id

    def get_resume_current_version(self, owner_id: str, resume_id: str) -> str | None:
        return self._resume_current_version.get((owner_id, resume_id))

    @classmethod
    def clear_state(cls) -> None:
        cls._bindings.clear()
        cls._by_owner_job.clear()
        cls._resume_current_version.clear()
