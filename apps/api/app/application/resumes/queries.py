"""Resume queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetResumeQuery:
    resume_id: str

