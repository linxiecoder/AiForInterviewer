"""Apply feedback generation to a saved Polish answer."""

from __future__ import annotations

from typing import Any, Protocol

from app.application.common.result import ApplicationResult
from app.application.polish.commands import CreatePolishFeedbackTaskCommand
from app.application.polish.entities import PolishAnswer, PolishTaskStatus
from app.domain.shared.errors import DomainError


class _AnswerReader(Protocol):
    def get_answer(self, owner_id: str, answer_id: str) -> PolishAnswer | None: ...


class _FeedbackTaskCreator(Protocol):
    def create_feedback_task(
        self,
        command: CreatePolishFeedbackTaskCommand,
    ) -> ApplicationResult[PolishTaskStatus]: ...


class PolishApplyFeedbackUseCase:
    def __init__(self, repository: _AnswerReader, feedback_service: _FeedbackTaskCreator) -> None:
        self._repository = repository
        self._feedback_service = feedback_service

    def execute(self, command: CreatePolishFeedbackTaskCommand) -> ApplicationResult[PolishTaskStatus]:
        answer = self._repository.get_answer(command.owner_id, command.answer_id)
        if answer is None or answer.session_id != command.session_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Answer not found")
            )

        scoring_context = _normalize_internal_scoring_context(
            getattr(command, "internal_scoring_context", None)
        )
        if scoring_context is not None:
            object.__setattr__(command, "internal_scoring_context", scoring_context)
        return self._feedback_service.create_feedback_task(command)


def _normalize_internal_scoring_context(value: object) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        return None
    return {str(key): item for key, item in value.items()}

