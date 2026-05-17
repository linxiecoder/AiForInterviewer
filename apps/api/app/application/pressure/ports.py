"""Pressure ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class PressureRepository(Protocol):
    def get_ref(self, session_id: str) -> ResourceRef | None: ...

