"""Focused application service for Polish question operations."""

from __future__ import annotations

from typing import Protocol

from app.application.common.result import ApplicationResult
from app.application.polish.commands import CompletePolishQuestionCommand, CreatePolishQuestionTaskCommand
from app.application.polish.entities import PolishSessionDetail, PolishTaskStatus


class _QuestionOperations(Protocol):
    def create_question_task(
        self,
        command: CreatePolishQuestionTaskCommand,
    ) -> ApplicationResult[PolishTaskStatus]: ...

    def complete_question(
        self,
        command: CompletePolishQuestionCommand,
    ) -> ApplicationResult[PolishSessionDetail]: ...


class PolishQuestionApplicationService:
    def __init__(self, operations: _QuestionOperations) -> None:
        self._operations = operations

    def bind(self, operations: _QuestionOperations) -> None:
        self._operations = operations

    def create_question_task(
        self,
        command: CreatePolishQuestionTaskCommand,
    ) -> ApplicationResult[PolishTaskStatus]:
        return self._operations.create_question_task(command)

    def complete_question(
        self,
        command: CompletePolishQuestionCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        return self._operations.complete_question(command)
