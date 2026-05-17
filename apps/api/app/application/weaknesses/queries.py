"""Weakness queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetWeaknessQuery:
    weakness_id: str

