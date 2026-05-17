"""Polish queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetPolishSessionQuery:
    session_id: str

