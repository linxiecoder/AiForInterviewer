"""Job domain ports."""

from typing import Protocol

from app.domain.jobs.entities import Job


class JobReader(Protocol):
    def get(self, job_id: str) -> Job | None: ...

