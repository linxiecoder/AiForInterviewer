"""Training commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateTrainingSuggestionTaskCommand:
    target_ref_id: str

