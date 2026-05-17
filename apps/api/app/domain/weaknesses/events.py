"""Weakness domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WeaknessConfirmed:
    weakness_id: str

