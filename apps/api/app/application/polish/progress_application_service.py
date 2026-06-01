"""Focused application service for Polish progress operations."""

from __future__ import annotations

from typing import Protocol

from app.application.common.result import ApplicationResult
from app.application.polish.commands import (
    GenerateInitialPolishProgressTreeCommand,
    RefreshPolishProgressTreeStateCommand,
)
from app.application.polish.entities import PolishSessionDetail


class _ProgressOperations(Protocol):
    def generate_initial_progress_tree(
        self,
        command: GenerateInitialPolishProgressTreeCommand,
    ) -> ApplicationResult[PolishSessionDetail]: ...

    def refresh_progress_tree_state(
        self,
        command: RefreshPolishProgressTreeStateCommand,
    ) -> ApplicationResult[PolishSessionDetail]: ...


class PolishProgressApplicationService:
    def __init__(self, operations: _ProgressOperations) -> None:
        self._operations = operations

    def bind(self, operations: _ProgressOperations) -> None:
        self._operations = operations

    def generate_initial_progress_tree(
        self,
        command: GenerateInitialPolishProgressTreeCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        return self._operations.generate_initial_progress_tree(command)

    def refresh_progress_tree_state(
        self,
        command: RefreshPolishProgressTreeStateCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        return self._operations.refresh_progress_tree_state(command)
