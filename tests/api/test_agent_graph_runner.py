from __future__ import annotations

from dataclasses import is_dataclass

from app.application.ai_runtime.contracts import (
    AgentCommandEnvelope,
    AgentGraphRunner,
    AgentReplayResult,
    AgentRunContext,
    AgentRunResult,
    AgentRunStatus,
    AgentRunTimelinePage,
)


def test_agent_graph_runner_port_declares_required_methods() -> None:
    for method_name in ("start", "resume", "replay", "get_status", "get_timeline", "cancel"):
        assert hasattr(AgentGraphRunner, method_name)


def test_stub_runner_returns_project_owned_results_only() -> None:
    runner = _StubRunner()
    context = AgentRunContext(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_1",
        ai_task_id="aitask_1",
        graph_name="polish_question_graph",
        graph_version="v0",
        command=AgentCommandEnvelope(
            entrypoint="start",
            input_refs=("session_1",),
            requested_outputs=("candidate_refs",),
            idempotency_key="idem_1",
        ),
    )

    result = runner.start(context, context.command)
    replay = runner.replay(context, checkpoint_ref="ackpt_1")
    cancelled = runner.cancel("arun_1", "owner_1", reason="user_cancelled", actor_id="actor_1")

    assert is_dataclass(result)
    assert result.formal_refs == ()
    assert replay.read_only is True
    assert replay.formal_write_blocked is True
    assert cancelled.formal_write_blocked is True


class _StubRunner:
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(run_id=context.run_id, status="queued", output_refs=("candidate_ref_1",))

    def resume(
        self, context: AgentRunContext, interrupt_ref: str, resume_payload: dict[str, object]
    ) -> AgentRunResult:
        return AgentRunResult(run_id=context.run_id, status="running", output_refs=("candidate_ref_1",))

    def replay(self, context: AgentRunContext, checkpoint_ref: str) -> AgentReplayResult:
        return AgentReplayResult(run_id=context.run_id, status="replayed_debug", read_only=True)

    def get_status(self, run_id: str, owner_id: str) -> AgentRunStatus:
        return AgentRunStatus(run_id=run_id, status="running", owner_id=owner_id)

    def get_timeline(self, run_id: str, owner_id: str, cursor: str | None = None, limit: int = 50) -> AgentRunTimelinePage:
        return AgentRunTimelinePage(run_id=run_id, events=(), next_cursor=None)

    def cancel(self, run_id: str, owner_id: str, reason: str, actor_id: str) -> AgentRunStatus:
        return AgentRunStatus(run_id=run_id, status="cancelled", owner_id=owner_id, formal_write_blocked=True)

