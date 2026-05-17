"""Polish ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class PolishRepository(Protocol):
    def get_ref(self, session_id: str) -> ResourceRef | None: ...

