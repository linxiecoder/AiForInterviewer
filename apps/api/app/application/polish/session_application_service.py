"""Focused application service for Polish session operations."""

from __future__ import annotations

from typing import Protocol

from app.application.common.result import ApplicationResult
from app.application.polish.commands import (
    CreatePolishSessionCommand,
    EndPolishSessionCommand,
    SoftDeletePolishSessionCommand,
)
from app.application.polish.entities import PolishSession, PolishSessionDetail, PolishTopic
from app.application.polish.queries import (
    GetPolishSessionQuery,
    ListPolishSessionsQuery,
    ListPolishTopicsQuery,
)


class _SessionOperations(Protocol):
    def bootstrap(self) -> ApplicationResult[str]: ...

    def list_topics(self, query: ListPolishTopicsQuery) -> ApplicationResult[tuple[PolishTopic, ...]]: ...

    def list_sessions(
        self,
        query: ListPolishSessionsQuery,
    ) -> ApplicationResult[tuple[PolishSessionDetail, ...]]: ...

    def create_session(self, command: CreatePolishSessionCommand) -> ApplicationResult[PolishSession]: ...

    def get_session(self, query: GetPolishSessionQuery) -> ApplicationResult[PolishSessionDetail]: ...

    def end_session(self, command: EndPolishSessionCommand) -> ApplicationResult[PolishSessionDetail]: ...

    def soft_delete_session(
        self,
        command: SoftDeletePolishSessionCommand,
    ) -> ApplicationResult[PolishSessionDetail]: ...


class PolishSessionApplicationService:
    def __init__(self, operations: _SessionOperations) -> None:
        self._operations = operations

    def bind(self, operations: _SessionOperations) -> None:
        self._operations = operations

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="polish_skeleton")

    def list_topics(self, query: ListPolishTopicsQuery) -> ApplicationResult[tuple[PolishTopic, ...]]:
        return self._operations.list_topics(query)

    def list_sessions(self, query: ListPolishSessionsQuery) -> ApplicationResult[tuple[PolishSessionDetail, ...]]:
        return self._operations.list_sessions(query)

    def create_session(self, command: CreatePolishSessionCommand) -> ApplicationResult[PolishSession]:
        return self._operations.create_session(command)

    def get_session(self, query: GetPolishSessionQuery) -> ApplicationResult[PolishSessionDetail]:
        return self._operations.get_session(query)

    def end_session(self, command: EndPolishSessionCommand) -> ApplicationResult[PolishSessionDetail]:
        return self._operations.end_session(command)

    def soft_delete_session(
        self,
        command: SoftDeletePolishSessionCommand,
    ) -> ApplicationResult[PolishSessionDetail]:
        return self._operations.soft_delete_session(command)
