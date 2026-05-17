"""Pressure queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetPressureSessionQuery:
    session_id: str

