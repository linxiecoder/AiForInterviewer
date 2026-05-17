"""Job domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class JobVersionCreated:
    job_id: str
    version_id: str

