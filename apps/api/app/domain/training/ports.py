"""Training domain ports."""

from typing import Protocol

from app.domain.training.entities import TrainingRecommendation


class TrainingRecommendationReader(Protocol):
    def get(self, training_recommendation_id: str) -> TrainingRecommendation | None: ...

