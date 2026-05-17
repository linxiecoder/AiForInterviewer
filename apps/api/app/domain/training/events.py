"""Training domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingSuggestionConfirmed:
    training_recommendation_id: str

