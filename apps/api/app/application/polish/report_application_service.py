"""Focused application service for Polish report operations."""

from __future__ import annotations

from typing import Protocol

from app.application.common.result import ApplicationResult
from app.application.polish.commands import GeneratePolishSessionReportCommand
from app.application.polish.entities import PolishSessionDetail


class _ReportOperations(Protocol):
    def generate_session_report(
        self,
        command: GeneratePolishSessionReportCommand,
    ) -> ApplicationResult[PolishSessionDetail]: ...


class PolishReportApplicationService:
    def __init__(self, operations: _ReportOperations) -> None:
        self._operations = operations

    def bind(self, operations: _ReportOperations) -> None:
        self._operations = operations

    def generate_session_report(
        self,
        command: GeneratePolishSessionReportCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        return self._operations.generate_session_report(command)
