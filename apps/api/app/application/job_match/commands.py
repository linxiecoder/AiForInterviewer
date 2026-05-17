"""Job match commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateJobMatchAnalysisCommand:
    binding_id: str

