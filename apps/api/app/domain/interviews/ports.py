"""Interview domain ports."""

from typing import Protocol

from app.domain.interviews.entities import InterviewSession


class InterviewReader(Protocol):
    def get(self, session_id: str) -> InterviewSession | None: ...

