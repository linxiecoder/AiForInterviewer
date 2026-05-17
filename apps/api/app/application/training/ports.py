"""Training ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class TrainingRepository(Protocol):
    def get_ref(self, training_recommendation_id: str) -> ResourceRef | None: ...

