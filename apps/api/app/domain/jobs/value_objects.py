"""Job value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class JobDescription:
    jd_text: str

