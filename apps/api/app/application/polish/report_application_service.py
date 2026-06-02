"""Focused application service for Polish report operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from app.application.common.result import ApplicationResult
from app.application.polish.commands import GeneratePolishSessionReportCommand
from app.application.polish.entities import PolishSessionDetail
from app.application.polish.ports import PolishRepository
from app.domain.shared.errors import DomainError
from app.domain.shared.ids import ResourceIdPrefix, generate_resource_id


SESSION_STATUS_DELETED = "deleted"
BuildSessionDetail = Callable[..., PolishSessionDetail]


class _ReportOperations(Protocol):
    def generate_session_report(
        self,
        command: GeneratePolishSessionReportCommand,
    ) -> ApplicationResult[PolishSessionDetail]: ...


class PolishReportApplicationService:
    def __init__(
        self,
        operations: _ReportOperations,
        *,
        polish_repository: PolishRepository | None = None,
        build_session_detail: BuildSessionDetail | None = None,
    ) -> None:
        self._operations = operations
        self._polish_repository = polish_repository
        self._build_session_detail = build_session_detail

    def bind(self, operations: _ReportOperations) -> None:
        self._operations = operations

    def generate_session_report(
        self,
        command: GeneratePolishSessionReportCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        if self._polish_repository is None or self._build_session_detail is None:
            return self._operations.generate_session_report(command)
        session = self._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None or session.status == SESSION_STATUS_DELETED:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )
        session_with_report = self._polish_repository.create_session_report(
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            session_id=command.session_id,
            report_id=generate_resource_id(ResourceIdPrefix.REPORT),
        )
        return ApplicationResult(
            value=self._build_session_detail(owner_id=command.owner_id, session=session_with_report)
        )
