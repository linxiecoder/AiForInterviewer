"""Training use cases."""

from typing import Any

from app.application.common.result import ApplicationResult
from app.application.training.ports import TrainingActionError, TrainingRepository
from app.domain.shared.errors import DomainError


class TrainingUseCases:
    def __init__(self, repository: TrainingRepository) -> None:
        self._repository = repository

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="training_skeleton")

    def list_training_suggestions(self, *, owner_id: str) -> ApplicationResult[tuple[dict[str, Any], ...]]:
        return ApplicationResult(value=self._repository.list_recommendations(owner_id=owner_id))

    def dismiss_training_suggestion(
        self,
        *,
        owner_id: str,
        actor_id: str,
        recommendation_id: str,
    ) -> ApplicationResult[dict[str, Any]]:
        return self._run_repository_action(
            self._repository.dismiss_recommendation,
            owner_id=owner_id,
            actor_id=actor_id,
            recommendation_id=recommendation_id,
        )

    def start_training_task(
        self,
        *,
        owner_id: str,
        actor_id: str,
        recommendation_id: str,
    ) -> ApplicationResult[dict[str, Any]]:
        return self._run_repository_action(
            self._repository.start_task,
            owner_id=owner_id,
            actor_id=actor_id,
            recommendation_id=recommendation_id,
        )

    def complete_training_task(
        self,
        *,
        owner_id: str,
        recommendation_id: str,
        task_id: str,
    ) -> ApplicationResult[dict[str, Any]]:
        return self._run_repository_action(
            self._repository.complete_task,
            owner_id=owner_id,
            recommendation_id=recommendation_id,
            task_id=task_id,
        )

    def _run_repository_action(self, action: Any, **kwargs: Any) -> ApplicationResult[dict[str, Any]]:
        try:
            return ApplicationResult(value=action(**kwargs))
        except TrainingActionError as exc:
            return ApplicationResult(error=DomainError(code=exc.code, message=exc.message))
