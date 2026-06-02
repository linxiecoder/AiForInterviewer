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
from app.domain.shared.errors import DomainError


POLISH_TOPICS: tuple[PolishTopic, ...] = (
    PolishTopic(
        topic_id="topic_authenticity_contribution",
        title="经历真实性与贡献拷问",
        description="围绕简历经历真实性、个人贡献边界、关键证据和追问抗压能力进行模拟面试。",
        requires_job_binding=True,
    ),
    PolishTopic(
        topic_id="topic_technical_depth",
        title="能力深度与技术碾压",
        description="围绕核心技术栈、架构设计、性能瓶颈和底层原理进行深度追问。",
        requires_job_binding=True,
    ),
    PolishTopic(
        topic_id="topic_scenario_roleplay",
        title="情景模拟与角色扮演",
        description="围绕真实业务场景、团队协作、跨角色沟通和临场决策进行角色化模拟。",
        requires_job_binding=True,
    ),
    PolishTopic(
        topic_id="topic_risk_defense",
        title="风险点排查与防御性打磨",
        description="围绕简历和岗位匹配中的风险点、薄弱项、反问陷阱和防御性表达进行打磨。",
        requires_job_binding=True,
    ),
)


class _BindingRecord(Protocol):
    owner_id: str


class _BindingLookup(Protocol):
    def get(self, binding_id: str) -> _BindingRecord | None: ...


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
    def __init__(
        self,
        operations: _SessionOperations,
        *,
        binding_repository: _BindingLookup | None = None,
    ) -> None:
        self._operations = operations
        self._binding_repository = binding_repository

    def bind(self, operations: _SessionOperations) -> None:
        self._operations = operations

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="polish_skeleton")

    def list_topics(self, query: ListPolishTopicsQuery) -> ApplicationResult[tuple[PolishTopic, ...]]:
        if self._binding_repository is None:
            return self._operations.list_topics(query)
        if query.resume_job_binding_id:
            binding = self._binding_repository.get(query.resume_job_binding_id)
            if binding is None or binding.owner_id != query.owner_id:
                return ApplicationResult(
                    error=DomainError(code="not_found_or_inaccessible", message="Binding not found")
                )
        return ApplicationResult(value=POLISH_TOPICS)

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
