from __future__ import annotations

import pytest

from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentCommandEnvelope,
    AgentReplayResult,
    AgentRunContext,
    AgentRunResult,
    AgentRunStatus,
    AgentRunTimelinePage,
    AgentTimelineEvent,
    GraphDisabledError,
    RuntimeConflictError,
)
from app.application.ai_runtime.facade import AiOrchestrationFacade
from app.application.ai_runtime.registry import AgentGraphRegistry
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver


RAW_KEY = "raw" + "_prompt"
PROVIDER_KEY = "provider_" + "payload"


def test_facade_starts_polish_question_generation_with_refs_only_and_idempotency() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    first = facade.start_polish_question_generation(
        owner_id="owner_1",
        actor_id="actor_1",
        session_ref="session_1",
        progress_node_refs=("progress_node_1",),
        completed_focus_refs=("focus_1",),
        idempotency_key="idem_1",
    )
    repeated = facade.start_polish_question_generation(
        owner_id="owner_1",
        actor_id="actor_1",
        session_ref="session_1",
        progress_node_refs=("progress_node_1",),
        completed_focus_refs=("focus_1",),
        idempotency_key="idem_1",
    )

    assert first == repeated
    assert first.ai_task_id.startswith("aitask_")
    assert first.agent_run_id.startswith("arun_")
    assert first.formal_refs == ()
    assert len(runner.started) == 1
    assert runner.started[0].command.input_refs == ("session_1", "progress_node_1", "focus_1")
    assert "request_digest" in runner.started[0].command.metadata
    assert "idempotency_key_hash" in runner.started[0].command.metadata


def test_facade_same_idempotency_key_with_different_input_refs_conflicts_without_runner_call() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    first = facade.start_polish_question_generation(
        owner_id="owner_1",
        actor_id="actor_1",
        session_ref="session_1",
        progress_node_refs=("progress_node_1",),
        completed_focus_refs=("focus_1",),
        idempotency_key="idem_1",
    )

    with pytest.raises(RuntimeConflictError):
        facade.start_polish_question_generation(
            owner_id="owner_1",
            actor_id="actor_1",
            session_ref="session_2",
            progress_node_refs=("progress_node_1",),
            completed_focus_refs=("focus_1",),
            idempotency_key="idem_1",
        )

    assert len(runner.started) == 1
    assert runner.started[0].run_id == first.agent_run_id


def test_facade_same_idempotency_key_with_different_requested_outputs_conflicts_without_new_run() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_FEEDBACK_ENABLED": True}
        ),
    )

    first = facade.start_polish_feedback_generation(
        owner_id="owner_1",
        actor_id="actor_1",
        session_ref="session_1",
        question_ref="question_1",
        answer_ref="answer_1",
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_1",
    )

    with pytest.raises(RuntimeConflictError):
        facade.start_polish_feedback_generation(
            owner_id="owner_1",
            actor_id="actor_1",
            session_ref="session_1",
            question_ref="question_1",
            answer_ref="answer_1",
            requested_outputs=("candidate_refs", "suggestion_refs"),
            idempotency_key="idem_1",
        )

    assert len(runner.started) == 1
    assert runner.started[0].run_id == first.agent_run_id


def test_facade_different_idempotency_key_creates_separate_request() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    first = facade.start_polish_question_generation(
        owner_id="owner_1",
        actor_id="actor_1",
        session_ref="session_1",
        progress_node_refs=(),
        completed_focus_refs=(),
        idempotency_key="idem_1",
    )
    second = facade.start_polish_question_generation(
        owner_id="owner_1",
        actor_id="actor_1",
        session_ref="session_1",
        progress_node_refs=(),
        completed_focus_refs=(),
        idempotency_key="idem_2",
    )

    assert first != second
    assert first.agent_run_id != second.agent_run_id
    assert len(runner.started) == 2


def test_facade_propagates_candidate_payloads_from_runner_to_status_ref() -> None:
    payload = AgentCandidatePayload(
        candidate_ref="question_candidate_ref_1",
        candidate_type="polish_question_candidate",
        payload_schema_id="polish_question_candidate.v1",
        payload={"question_text": "请介绍支付链路一致性经验"},
        trace_refs=("trace_1",),
    )
    runner = _RecordingRunner()
    runner.candidate_payloads = (payload,)
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    status_ref = facade.start_polish_question_generation(
        owner_id="owner_1",
        actor_id="actor_1",
        session_ref="session_1",
        progress_node_refs=(),
        completed_focus_refs=(),
        idempotency_key="idem_payload",
    )

    assert status_ref.candidate_refs == ("candidate_ref_1",)
    assert status_ref.candidate_payloads == (payload,)
    assert status_ref.formal_refs == ()


def test_facade_fails_closed_when_graph_is_disabled() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(),
    )

    with pytest.raises(GraphDisabledError):
        facade.start_polish_question_generation(
            owner_id="owner_1",
            actor_id="actor_1",
            session_ref="session_1",
            progress_node_refs=(),
            completed_focus_refs=(),
            idempotency_key="idem_disabled",
        )

    assert runner.started == []


def test_facade_status_and_timeline_are_sanitized() -> None:
    runner = _RecordingRunner()
    runner.timeline = AgentRunTimelinePage(
        run_id="arun_1",
        events=(
            AgentTimelineEvent(
                event_id="evt_1",
                event_type="node_finished",
                summary="node finished",
                refs=("trace_1",),
                metadata={RAW_KEY: "hidden", PROVIDER_KEY: {"token": "secret"}, "safe": "ok"},
            ),
        ),
        next_cursor=None,
    )
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(test_overrides={"AIFI_AI_RUNTIME_ENABLED": True}),
    )

    status = facade.get_agent_run_status(run_id="arun_1", owner_id="owner_1")
    timeline = facade.get_agent_run_timeline(run_id="arun_1", owner_id="owner_1")

    assert status.run_id == "arun_1"
    assert status.formal_write_blocked is True
    assert timeline.events[0].metadata == {"safe": "ok"}


class _RecordingRunner:
    def __init__(self) -> None:
        self.started: list[AgentRunContext] = []
        self.timeline = AgentRunTimelinePage(run_id="arun_1", events=(), next_cursor=None)
        self.candidate_payloads: tuple[AgentCandidatePayload, ...] = ()

    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        self.started.append(context)
        return AgentRunResult(
            run_id=context.run_id,
            status="queued",
            output_refs=("candidate_ref_1",),
            trace_refs=("trace_1",),
            formal_refs=(),
            candidate_payloads=self.candidate_payloads,
        )

    def resume(
        self, context: AgentRunContext, interrupt_ref: str, resume_payload: dict[str, object]
    ) -> AgentRunResult:
        return AgentRunResult(run_id=context.run_id, status="running", trace_refs=("trace_resume",))

    def replay(self, context: AgentRunContext, checkpoint_ref: str) -> AgentReplayResult:
        return AgentReplayResult(run_id=context.run_id, status="replayed_debug", read_only=True)

    def get_status(self, run_id: str, owner_id: str) -> AgentRunStatus:
        return AgentRunStatus(run_id=run_id, status="running", owner_id=owner_id, formal_write_blocked=True)

    def get_timeline(self, run_id: str, owner_id: str, cursor: str | None = None, limit: int = 50) -> AgentRunTimelinePage:
        return self.timeline

    def cancel(self, run_id: str, owner_id: str, reason: str, actor_id: str) -> AgentRunStatus:
        return AgentRunStatus(run_id=run_id, status="cancelled", owner_id=owner_id, formal_write_blocked=True)
