"""Interview queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetInterviewSessionQuery:
    session_id: str

