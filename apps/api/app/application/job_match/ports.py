"""Job match ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class JobMatchRepository(Protocol):
    def get_ref(self, analysis_id: str) -> ResourceRef | None: ...

