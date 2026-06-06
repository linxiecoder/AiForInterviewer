from __future__ import annotations

from app.application.agents.contracts import (
    AgentExecutionPlan,
    AgentRuntimeLoopPolicy,
    P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
)
from app.application.agents.runtime import AgentExecutor, AgentGraphRunnerExecutorAdapter
from app.application.ai_runtime.contracts import (
    AgentCommandEnvelope,
    AgentRunContext,
    AgentRunResult,
    AgentRunStatus,
    AgentRunTimelinePage,
    AgentTimelineEvent,
)


def test_phase8_agent_executor_adapter_surfaces_runtime_without_formal_writes() -> None:
    runner = _ApplicationRunner()
    executor = AgentGraphRunnerExecutorAdapter(runner)
    plan = AgentExecutionPlan(
        plan_id="plan_application_phase8",
        run_id="arun_application_phase8",
        ai_task_id="aitask_application_phase8",
        agent_id="polish_question_graph",
        owner_id="owner_1",
        actor_id="actor_1",
        graph_name="polish_question_graph",
        graph_version="v0",
        objective="application layer P8 adapter gate",
        input_refs=("session_ref_1",),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_application_phase8",
        runtime_loop_policy=_runtime_loop_policy(),
    )

    started = executor.start(plan)
    status = executor.get_status(started.run_id)
    timeline = executor.get_timeline(started.run_id)
    cancelled = executor.cancel(started.run_id, reason="user_cancelled", actor_id="actor_1")

    assert isinstance(executor, AgentExecutor)
    assert started.output_refs == ("candidate_ref_application",)
    assert started.trace.trace_id == "trace_ref_application"
    assert started.metadata["source_boundary"] == "AgentGraphRunner"
    assert status.candidate_refs == started.output_refs
    assert status.trace_refs == ("trace_ref_application",)
    assert status.metadata["source_boundary"] == "AgentGraphRunner"
    assert timeline.events[0].candidate_refs == ("candidate_ref_application",)
    assert timeline.events[0].validation_refs == ("validation_ref_application",)
    assert cancelled.candidate_refs == started.output_refs
    assert cancelled.metadata["formal_write_blocked"] is True


class _ApplicationRunner:
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="running",
            output_refs=("candidate_ref_application",),
            trace_refs=("trace_ref_application",),
            formal_refs=(),
            metadata={"validation_refs": ("validation_ref_application",)},
        )

    def resume(
        self,
        context: AgentRunContext,
        interrupt_ref: str,
        resume_payload: dict[str, object],
    ) -> AgentRunResult:
        return self.start(context, context.command)

    def replay(self, context: AgentRunContext, checkpoint_ref: str):
        raise NotImplementedError

    def get_status(self, run_id: str, owner_id: str) -> AgentRunStatus:
        return AgentRunStatus(
            run_id=run_id,
            status="running",
            owner_id=owner_id,
            output_refs=("candidate_ref_application",),
            trace_refs=("trace_ref_application",),
            formal_write_blocked=True,
        )

    def get_timeline(
        self,
        run_id: str,
        owner_id: str,
        cursor: str | None = None,
        limit: int = 50,
    ) -> AgentRunTimelinePage:
        return AgentRunTimelinePage(
            run_id=run_id,
            events=(
                AgentTimelineEvent(
                    event_id="trace_event_application",
                    event_type="candidate_ready",
                    summary="application layer runtime event",
                    refs=("candidate_ref_application", "validation_ref_application"),
                    metadata={
                        "candidate_refs": ("candidate_ref_application",),
                        "validation_refs": ("validation_ref_application",),
                    },
                ),
            ),
            next_cursor=None,
        )

    def cancel(self, run_id: str, owner_id: str, reason: str, actor_id: str) -> AgentRunStatus:
        return AgentRunStatus(
            run_id=run_id,
            status="cancelled",
            owner_id=owner_id,
            output_refs=("candidate_ref_application",),
            trace_refs=("trace_ref_application",),
            formal_write_blocked=True,
        )


def _runtime_loop_policy() -> AgentRuntimeLoopPolicy:
    return AgentRuntimeLoopPolicy(
        max_steps=3,
        max_retries=1,
        timeout_seconds=5,
        stop_conditions=P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
        allowed_tools=("question_drafting",),
        allowed_callers=("polish_question_agent",),
        side_effect_policy="candidate_write",
    )
