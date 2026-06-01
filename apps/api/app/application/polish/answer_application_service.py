"""Focused application service for Polish answer operations."""

from __future__ import annotations

from typing import Protocol

from app.application.common.result import ApplicationResult
from app.application.polish.commands import CreatePolishAnswerCommand
from app.application.polish.entities import PolishAnswer


class _AnswerOperations(Protocol):
    def create_answer(self, command: CreatePolishAnswerCommand) -> ApplicationResult[PolishAnswer]: ...


class PolishAnswerApplicationService:
    def __init__(self, operations: _AnswerOperations) -> None:
        self._operations = operations

    def bind(self, operations: _AnswerOperations) -> None:
        self._operations = operations

    def create_answer(self, command: CreatePolishAnswerCommand) -> ApplicationResult[PolishAnswer]:
        return self._operations.create_answer(command)
