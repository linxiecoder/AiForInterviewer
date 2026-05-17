"""Job commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateJobCommand:
    title: str
    jd_text: str

