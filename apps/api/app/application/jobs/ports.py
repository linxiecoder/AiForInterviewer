"""Job repository ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class JobRepository(Protocol):
    def get_ref(self, job_id: str) -> ResourceRef | None: ...

