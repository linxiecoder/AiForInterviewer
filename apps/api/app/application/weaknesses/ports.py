"""Weakness ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class WeaknessRepository(Protocol):
    def get_ref(self, weakness_id: str) -> ResourceRef | None: ...

