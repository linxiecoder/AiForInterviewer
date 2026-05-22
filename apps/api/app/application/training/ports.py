"""Training ports."""

from typing import Any, Protocol

from app.domain.shared.refs import ResourceRef


class TrainingActionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class TrainingRepository(Protocol):
    def get_ref(self, training_recommendation_id: str) -> ResourceRef | None: ...

    def list_recommendations(self, *, owner_id: str) -> tuple[dict[str, Any], ...]: ...

    def dismiss_recommendation(self, *, owner_id: str, actor_id: str, recommendation_id: str) -> dict[str, Any]: ...

    def start_task(self, *, owner_id: str, actor_id: str, recommendation_id: str) -> dict[str, Any]: ...

    def complete_task(
        self,
        *,
        owner_id: str,
        recommendation_id: str,
        task_id: str,
    ) -> dict[str, Any]: ...
