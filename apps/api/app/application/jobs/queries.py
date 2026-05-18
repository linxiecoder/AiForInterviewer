"""Job query objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetJobQuery:
    owner_id: str
    job_id: str


@dataclass(frozen=True)
class ListJobsQuery:
    owner_id: str
