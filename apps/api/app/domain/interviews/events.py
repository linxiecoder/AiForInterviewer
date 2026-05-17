"""Interview domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InterviewSessionCreated:
    session_id: str

