"""Auth queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentSessionQuery:
    session_token: str
