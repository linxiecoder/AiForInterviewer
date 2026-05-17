"""Interview commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateInterviewSessionCommand:
    binding_id: str
    mode: str

