"""Polish queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ListPolishTopicsQuery:
    owner_id: str
    resume_job_binding_id: str | None = None


@dataclass(frozen=True)
class ListPolishSessionsQuery:
    owner_id: str


@dataclass(frozen=True)
class GetPolishSessionQuery:
    owner_id: str
    session_id: str
