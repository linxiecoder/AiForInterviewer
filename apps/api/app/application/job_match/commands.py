"""Job match commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateJobMatchAnalysisCommand:
    owner_id: str
    actor_id: str
    binding_id: str
