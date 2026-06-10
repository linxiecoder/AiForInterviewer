"""Persist Polish feedback results through the repository boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.application.common.result import ApplicationResult
from app.application.polish.entities import PolishFeedback, PolishTaskStatus


class _PolishResultWriter(Protocol):
    def add_feedback(self, feedback: PolishFeedback) -> None: ...

    def add_task(self, task: PolishTaskStatus, *, owner_id: str, actor_id: str, target_ref_id: str) -> None: ...


@dataclass(frozen=True)
class PersistPolishResultCommand:
    feedback: PolishFeedback
    task: PolishTaskStatus
    owner_id: str
    actor_id: str
    target_ref_id: str


class PolishPersistResultUseCase:
    def __init__(self, repository: _PolishResultWriter) -> None:
        self._repository = repository

    def execute(self, command: PersistPolishResultCommand) -> ApplicationResult[PolishTaskStatus]:
        self._repository.add_feedback(command.feedback)
        self._repository.add_task(
            command.task,
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            target_ref_id=command.target_ref_id,
        )
        return ApplicationResult(value=command.task)

