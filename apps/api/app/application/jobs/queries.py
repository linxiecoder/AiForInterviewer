"""Job queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetJobQuery:
    job_id: str

