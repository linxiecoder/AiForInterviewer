from __future__ import annotations

from typing import Protocol

from app.application.agents.contracts import (
    AgentExecutionPlan,
    AgentExecutionResult,
    AgentExecutionStatus,
    AgentExecutionTimeline,
)


class AgentExecutor(Protocol):
    def start(self, plan: AgentExecutionPlan) -> AgentExecutionResult: ...

    def resume(self, run_id: str, resume_payload: dict[str, object]) -> AgentExecutionResult: ...

    def replay(self, run_id: str, trace_ref: str) -> AgentExecutionResult: ...

    def get_status(self, run_id: str) -> AgentExecutionStatus: ...

    def get_timeline(self, run_id: str, cursor: str | None = None, limit: int = 50) -> AgentExecutionTimeline: ...

    def cancel(self, run_id: str, reason: str, actor_id: str) -> AgentExecutionStatus: ...


__all__ = ["AgentExecutor"]
