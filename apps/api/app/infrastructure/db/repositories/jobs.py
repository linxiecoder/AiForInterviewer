"""In-memory repository implementations for Job aggregates."""

from __future__ import annotations

from copy import deepcopy

from app.domain.jobs.entities import Job, JobVersion
from app.domain.jobs.ports import JobRepository
from app.infrastructure.db.models.job import Job as JobModel
from app.infrastructure.db.models.job import JobVersion as JobVersionModel


class SqlAlchemyJobRepository(JobRepository):
    _jobs: dict[str, Job] = {}
    _versions: dict[str, JobVersion] = {}
    _job_versions: dict[str, set[str]] = {}

    def list_by_owner(self, owner_id: str) -> list[Job]:
        return [deepcopy(job) for job in self._jobs.values() if job.owner_id == owner_id]

    def get(self, job_id: str) -> Job | None:
        found = self._jobs.get(job_id)
        return deepcopy(found) if found is not None else None

    def create_job(self, job: Job) -> None:
        self._jobs[job.job_id] = deepcopy(job)
        self._job_versions.setdefault(job.job_id, set())

    def update_job(self, job: Job) -> None:
        self._jobs[job.job_id] = deepcopy(job)

    def create_job_version(self, version: JobVersion) -> None:
        self._versions[version.job_version_id] = deepcopy(version)
        self._job_versions.setdefault(version.job_id, set()).add(version.job_version_id)

    def update_job_version(self, version: JobVersion) -> None:
        self._versions[version.job_version_id] = deepcopy(version)

    def get_job_version(self, job_version_id: str) -> JobVersion | None:
        found = self._versions.get(job_version_id)
        return deepcopy(found) if found is not None else None

    @classmethod
    def clear_state(cls) -> None:
        cls._jobs.clear()
        cls._versions.clear()
        cls._job_versions.clear()
