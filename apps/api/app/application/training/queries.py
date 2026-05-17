"""Training queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetTrainingSuggestionQuery:
    training_recommendation_id: str

