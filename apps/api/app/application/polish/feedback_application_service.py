"""Focused application service for Polish feedback operations."""

from __future__ import annotations

from typing import Protocol

from app.application.common.result import ApplicationResult
from app.application.polish.commands import CreatePolishFeedbackTaskCommand
from app.application.polish.entities import PolishTaskStatus


class _FeedbackOperations(Protocol):
    def create_feedback_task(
        self,
        command: CreatePolishFeedbackTaskCommand,
    ) -> ApplicationResult[PolishTaskStatus]: ...


class PolishFeedbackApplicationService:
    def __init__(self, operations: _FeedbackOperations) -> None:
        self._operations = operations

    def bind(self, operations: _FeedbackOperations) -> None:
        self._operations = operations

    def create_feedback_task(
        self,
        command: CreatePolishFeedbackTaskCommand,
    ) -> ApplicationResult[PolishTaskStatus]:
        return self._operations.create_feedback_task(command)
