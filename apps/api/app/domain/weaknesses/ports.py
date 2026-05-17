"""Weakness domain ports."""

from typing import Protocol

from app.domain.weaknesses.entities import Weakness


class WeaknessReader(Protocol):
    def get(self, weakness_id: str) -> Weakness | None: ...

