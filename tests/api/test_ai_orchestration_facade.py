from __future__ import annotations

import pytest

from app.application.agents.contracts import P8_REQUIRED_RUNTIME_STOP_CONDITIONS
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
    OwnerScopeError,
    RuntimeConflictError,
    RuntimeValidationError,
)
from app.application.ai_runtime.facade import AiOrchestrationFacade
from app.application.ai_runtime.registry import AgentGraphRegistry, GraphDescriptor
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


def test_facade_direct_start_injects_shared_runtime_loop_policy() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    facade.start_polish_question_generation(
        owner_id="owner_1",
        actor_id="actor_1",
        session_ref="session_1",
        progress_node_refs=(),
        completed_focus_refs=(),
        idempotency_key="idem_policy",
    )

    loop_policy = runner.started[0].command.metadata["runtime_loop_policy"]
    assert loop_policy == {
        "max_steps": 7,
        "max_retries": 2,
        "timeout_seconds": 20,
        "stop_conditions": (
            "max_steps_exceeded",
            "timeout",
            "validation_failed",
            "tool_not_allowed",
            "formal_write_requested",
            "interrupt_required",
            "provider_failed",
        ),
        "allowed_tools": (
            "context_retrieval",
            "evidence_selection",
            "question_drafting",
            "grounding_validation",
            "candidate_persistence",
        ),
        "allowed_callers": ("polish_question_agent",),
        "side_effect_policy": "candidate_write",
        "repair_strategy": "retry_within_bounds_then_fail_closed",
        "fallback_semantics": "candidate_only_blocked_or_failed_never_generated_success",
    }


def test_facade_direct_start_routes_through_agent_executor_plan_metadata() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    facade.start_polish_question_generation(
        owner_id="owner_1",
        actor_id="actor_1",
        session_ref="session_1",
        progress_node_refs=(),
        completed_focus_refs=(),
        idempotency_key="idem_executor_boundary",
    )

    metadata = runner.started[0].command.metadata
    assert metadata["plan_id"].startswith("plan_")
    assert metadata["agent_id"] == "polish_question_graph"
    assert metadata["objective"] == "start polish_question_generation"
    assert metadata["steps"] == ("start",)
    assert metadata["task_type"] == "polish_question_generation"


@pytest.mark.parametrize(
    (
        "surface",
        "task_type",
        "start_kwargs",
        "expected_input_refs",
        "expected_requested_outputs",
    ),
    (
        (
            "start_polish_question_generation",
            "polish_question_generation",
            {
                "session_ref": "session_1",
                "progress_node_refs": ("progress_node_1",),
                "completed_focus_refs": ("focus_1",),
            },
            ("session_1", "progress_node_1", "focus_1"),
            ("candidate_refs",),
        ),
        (
            "start_polish_feedback_generation",
            "polish_feedback_generation",
            {
                "session_ref": "session_1",
                "question_ref": "question_1",
                "answer_ref": "answer_1",
                "requested_outputs": ("candidate_refs", "suggestion_refs"),
            },
            ("session_1", "question_1", "answer_1"),
            ("candidate_refs", "suggestion_refs"),
        ),
        (
            "start_job_match_analysis",
            "job_match_analysis",
            {
                "binding_ref": "binding_1",
                "resume_ref": "resume_1",
                "job_ref": "job_1",
                "score_rule_ref": "score_rule_1",
            },
            ("binding_1", "resume_1", "job_1", "score_rule_1"),
            ("result_refs", "candidate_refs", "suggestion_refs"),
        ),
        (
            "start_report_generation",
            "report_generation",
            {
                "session_ref": "session_1",
                "report_type_ref": "report_type_1",
                "score_refs": ("score_1",),
            },
            ("session_1", "report_type_1", "score_1"),
            ("result_refs", "candidate_refs"),
        ),
        (
            "start_review_generation",
            "review_generation",
            {
                "source_refs": ("source_1",),
                "review_scope": "mock_interview",
                "privacy_flags": ("owner_only",),
            },
            ("source_1", "mock_interview", "owner_only"),
            ("candidate_refs", "suggestion_refs"),
        ),
    ),
)
def test_facade_start_surfaces_route_through_agent_executor_with_descriptor_runtime_policy(
    surface: str,
    task_type: str,
    start_kwargs: dict[str, object],
    expected_input_refs: tuple[str, ...],
    expected_requested_outputs: tuple[str, ...],
) -> None:
    runner = _RecordingRunner()
    registry = AgentGraphRegistry.default()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=registry,
        flag_resolver=RuntimeFlagResolver(
            test_overrides={
                "AIFI_AI_RUNTIME_ENABLED": True,
                "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True,
                "AIFI_GRAPH_POLISH_FEEDBACK_ENABLED": True,
                "AIFI_GRAPH_JOB_MATCH_ENABLED": True,
                "AIFI_GRAPH_REPORT_GENERATION_ENABLED": True,
                "AIFI_GRAPH_REVIEW_GENERATION_ENABLED": True,
            }
        ),
    )

    getattr(facade, surface)(
        owner_id="owner_1",
        actor_id="actor_1",
        idempotency_key=f"idem_{task_type}",
        **start_kwargs,
    )

    descriptor = registry.get_graph_descriptor(task_type)
    assert len(runner.started) == 1
    context = runner.started[0]
    metadata = context.command.metadata
    assert context.graph_name == descriptor.graph_name
    assert context.graph_version == descriptor.graph_version
    assert context.command.input_refs == expected_input_refs
    assert context.command.requested_outputs == expected_requested_outputs
    assert metadata["task_type"] == task_type
    assert metadata["graph_name"] == descriptor.graph_name
    assert metadata["graph_version"] == descriptor.graph_version
    assert metadata["plan_id"].startswith("plan_")
    assert metadata["objective"] == f"start {task_type}"
    assert metadata["runtime_loop_policy"] == {
        "max_steps": descriptor.runtime_max_steps,
        "max_retries": descriptor.runtime_max_retries,
        "timeout_seconds": descriptor.runtime_timeout_seconds,
        "stop_conditions": descriptor.runtime_stop_conditions,
        "allowed_tools": descriptor.runtime_allowed_tools,
        "allowed_callers": descriptor.runtime_allowed_callers,
        "side_effect_policy": descriptor.runtime_side_effect_policy,
        "repair_strategy": "retry_within_bounds_then_fail_closed",
        "fallback_semantics": "candidate_only_blocked_or_failed_never_generated_success",
    }


def test_facade_direct_start_fails_closed_when_descriptor_runtime_policy_is_missing() -> None:
    runner = _RecordingRunner()
    registry = AgentGraphRegistry(
        descriptors={
            "bad_question_graph": GraphDescriptor(
                graph_name="bad_question_graph",
                graph_version="test",
                capability="polish_question",
                lifecycle_status="active",
                runtime_flag_key="AIFI_GRAPH_POLISH_QUESTION_ENABLED",
                default_enabled=False,
                supported_entrypoints=("start",),
                supported_outputs=("candidate_refs",),
                prompt_contract_ids=("P-POLISH-QUESTION-001",),
                eval_suite_ids=("EVAL-POLISH-QUESTION-001",),
                required_permissions=("owner",),
                runtime_max_steps=7,
                runtime_max_retries=2,
                runtime_timeout_seconds=20,
                runtime_stop_conditions=P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
                runtime_allowed_tools=(),
                runtime_allowed_callers=("polish_question_agent",),
                runtime_side_effect_policy="candidate_write",
            )
        },
        task_map={"polish_question_generation": "bad_question_graph"},
    )
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=registry,
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    with pytest.raises(RuntimeValidationError, match="allowed_tools"):
        facade.start_polish_question_generation(
            owner_id="owner_1",
            actor_id="actor_1",
            session_ref="session_1",
            progress_node_refs=(),
            completed_focus_refs=(),
            idempotency_key="idem_missing_policy",
        )

    assert runner.started == []


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


def test_facade_created_status_timeline_and_cancel_route_through_agent_executor_adapter() -> None:
    runner = _RecordingRunner()
    runner.status_output_refs = ("candidate_ref_status",)
    runner.status_trace_refs = ("trace_status",)
    runner.status_metadata = {"handoff_refs": ("handoff_ref_status",)}
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    started = facade.start_polish_question_generation(
        owner_id="owner_1",
        actor_id="actor_1",
        session_ref="session_1",
        progress_node_refs=(),
        completed_focus_refs=(),
        idempotency_key="idem_adapter_read_cancel",
    )
    runner.timeline = AgentRunTimelinePage(
        run_id=started.agent_run_id,
        events=(
            AgentTimelineEvent(
                event_id="evt_adapter_1",
                event_type="node_finished",
                summary="node finished",
                refs=("candidate_ref_status", "validation_ref_status"),
                metadata={"validation_refs": ("validation_ref_status",)},
            ),
        ),
        next_cursor=None,
    )

    status = facade.get_agent_run_status(run_id=started.agent_run_id, owner_id="owner_1")
    timeline = facade.get_agent_run_timeline(run_id=started.agent_run_id, owner_id="owner_1")
    cancelled = facade.cancel_agent_run(
        run_id=started.agent_run_id,
        owner_id="owner_1",
        reason="user cancelled",
        actor_id="actor_1",
    )

    assert status.metadata["source_boundary"] == "AgentGraphRunner"
    assert status.output_refs == runner.status_output_refs
    assert status.metadata["handoff_refs"] == ("handoff_ref_status",)
    assert timeline.events[0].metadata["source_boundary"] == "AgentGraphRunner"
    assert timeline.events[0].metadata["agent_id"] == "polish_question_graph"
    assert timeline.events[0].metadata["ai_task_id"] == started.ai_task_id
    assert timeline.events[0].metadata["validation_refs"] == ("validation_ref_status",)
    assert cancelled.metadata["source_boundary"] == "AgentGraphRunner"
    assert cancelled.output_refs == runner.status_output_refs


def test_facade_created_adapter_route_preserves_owner_scope() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    started = facade.start_polish_question_generation(
        owner_id="owner_1",
        actor_id="actor_1",
        session_ref="session_1",
        progress_node_refs=(),
        completed_focus_refs=(),
        idempotency_key="idem_adapter_owner_scope",
    )

    with pytest.raises(OwnerScopeError, match="agent run not found for owner"):
        facade.get_agent_run_status(run_id=started.agent_run_id, owner_id="owner_2")


def test_facade_timeline_fails_closed_when_descriptor_does_not_support_timeline_before_runner_call() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=_start_only_registry(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_START_ONLY_ENABLED": True}
        ),
    )

    started = facade._start_run(
        task_type="start_only_task",
        owner_id="owner_1",
        actor_id="actor_1",
        input_refs=("input_ref_1",),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_start_only_timeline",
    )

    with pytest.raises(RuntimeValidationError, match="unsupported graph entrypoint"):
        facade.get_agent_run_timeline(run_id=started.agent_run_id, owner_id="owner_1")

    assert runner.timeline_requests == []


def test_facade_cancel_fails_closed_when_descriptor_does_not_support_cancel_before_runner_call() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=_start_only_registry(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_START_ONLY_ENABLED": True}
        ),
    )

    started = facade._start_run(
        task_type="start_only_task",
        owner_id="owner_1",
        actor_id="actor_1",
        input_refs=("input_ref_1",),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_start_only_cancel",
    )

    with pytest.raises(RuntimeValidationError, match="unsupported graph entrypoint"):
        facade.cancel_agent_run(
            run_id=started.agent_run_id,
            owner_id="owner_1",
            reason="user cancelled",
            actor_id="actor_1",
        )

    assert runner.cancelled == []


def test_facade_replay_agent_run_is_read_only_and_formal_write_blocked() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    replay = facade.replay_agent_run(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_1",
        ai_task_id="aitask_1",
        graph_name="polish_question_graph",
        graph_version="v0",
        checkpoint_ref="ackpt_1",
    )

    assert replay.run_id == "arun_1"
    assert replay.status == "replayed_debug"
    assert replay.read_only is True
    assert replay.formal_write_blocked is True


def test_facade_replay_agent_run_rejects_provider_tool_or_repository_side_effects() -> None:
    runner = _ReplaySideEffectRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    with pytest.raises(RuntimeValidationError, match="replay cannot call"):
        facade.replay_agent_run(
            owner_id="owner_1",
            actor_id="actor_1",
            run_id="arun_1",
            ai_task_id="aitask_1",
            graph_name="polish_question_graph",
            graph_version="v0",
            checkpoint_ref="ackpt_1",
        )


def test_facade_replay_fails_closed_when_descriptor_does_not_support_replay_before_runner_call() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_JOB_MATCH_ENABLED": True}
        ),
    )

    with pytest.raises(RuntimeValidationError, match="unsupported graph entrypoint"):
        facade.replay_agent_run(
            owner_id="owner_1",
            actor_id="actor_1",
            run_id="arun_job_match",
            ai_task_id="aitask_job_match",
            graph_name="job_match_graph",
            graph_version="pr3-contract",
            checkpoint_ref="ackpt_job_match",
        )

    assert runner.replayed == []


def test_facade_resume_injects_checkpoint_control_fields_and_shared_loop_policy() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    status = facade.resume_interrupted_run(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_1",
        ai_task_id="aitask_1",
        graph_name="polish_question_graph",
        graph_version="v0",
        interrupt_ref="aint_1",
        checkpoint_ref="ackpt_1",
        resume_payload={"action": "approve", RAW_KEY: "hidden"},
        base_version=3,
        idempotency_key="idem_resume_1",
    )

    assert status.agent_run_id == "arun_1"
    assert len(runner.resumed) == 1
    context, interrupt_ref, resume_payload = runner.resumed[0]
    assert interrupt_ref == "aint_1"
    assert context.command.input_refs == ("aint_1", "ackpt_1")
    assert context.command.metadata["checkpoint_ref"] == "ackpt_1"
    assert context.command.metadata["base_version"] == 3
    assert "runtime_loop_policy" in context.command.metadata
    assert resume_payload == {
        "action": "approve",
        "checkpoint_ref": "ackpt_1",
        "base_version": 3,
        "idempotency_key": "idem_resume_1",
    }


def test_facade_resume_fails_closed_for_unsupported_action_before_runner_call() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    with pytest.raises(RuntimeValidationError, match="unsupported resume action"):
        facade.resume_interrupted_run(
            owner_id="owner_1",
            actor_id="actor_1",
            run_id="arun_1",
            ai_task_id="aitask_1",
            graph_name="polish_question_graph",
            graph_version="v0",
            interrupt_ref="aint_1",
            checkpoint_ref="ackpt_1",
            resume_payload={"action": "overwrite_formal_fact"},
            base_version=3,
            idempotency_key="idem_resume_1",
        )

    assert runner.resumed == []


def test_facade_resume_fails_closed_when_descriptor_does_not_support_resume_before_runner_call() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_JOB_MATCH_ENABLED": True}
        ),
    )

    with pytest.raises(RuntimeValidationError, match="unsupported graph entrypoint"):
        facade.resume_interrupted_run(
            owner_id="owner_1",
            actor_id="actor_1",
            run_id="arun_job_match",
            ai_task_id="aitask_job_match",
            graph_name="job_match_graph",
            graph_version="pr3-contract",
            interrupt_ref="aint_job_match",
            checkpoint_ref="ackpt_job_match",
            resume_payload={"action": "approve"},
            base_version=1,
            idempotency_key="idem_job_match_resume",
        )

    assert runner.resumed == []


def test_facade_resume_blocks_runtime_formal_refs_through_agent_executor_boundary() -> None:
    runner = _FormalResumeRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    with pytest.raises(ValueError, match="formal refs"):
        facade.resume_interrupted_run(
            owner_id="owner_1",
            actor_id="actor_1",
            run_id="arun_1",
            ai_task_id="aitask_1",
            graph_name="polish_question_graph",
            graph_version="v0",
            interrupt_ref="aint_1",
            checkpoint_ref="ackpt_1",
            resume_payload={"action": "approve"},
            base_version=3,
            idempotency_key="idem_resume_1",
        )


def test_facade_resume_requires_strict_base_version_before_runner_call() -> None:
    runner = _RecordingRunner()
    facade = AiOrchestrationFacade(
        runner=runner,
        registry=AgentGraphRegistry.default(),
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
        ),
    )

    with pytest.raises(RuntimeValidationError, match="base version must be a non-negative integer"):
        facade.resume_interrupted_run(
            owner_id="owner_1",
            actor_id="actor_1",
            run_id="arun_1",
            ai_task_id="aitask_1",
            graph_name="polish_question_graph",
            graph_version="v0",
            interrupt_ref="aint_1",
            checkpoint_ref="ackpt_1",
            resume_payload={"action": "approve"},
            base_version=True,
            idempotency_key="idem_resume_1",
        )

    assert runner.resumed == []


class _RecordingRunner:
    def __init__(self) -> None:
        self.started: list[AgentRunContext] = []
        self.resumed: list[tuple[AgentRunContext, str, dict[str, object]]] = []
        self.replayed: list[tuple[AgentRunContext, str]] = []
        self.timeline_requests: list[tuple[str, str]] = []
        self.cancelled: list[tuple[str, str, str, str]] = []
        self.timeline = AgentRunTimelinePage(run_id="arun_1", events=(), next_cursor=None)
        self.candidate_payloads: tuple[AgentCandidatePayload, ...] = ()
        self.status_output_refs: tuple[str, ...] = ()
        self.status_trace_refs: tuple[str, ...] = ()
        self.status_metadata: dict[str, object] = {}

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
        self.resumed.append((context, interrupt_ref, resume_payload))
        return AgentRunResult(run_id=context.run_id, status="running", trace_refs=("trace_resume",))

    def replay(self, context: AgentRunContext, checkpoint_ref: str) -> AgentReplayResult:
        self.replayed.append((context, checkpoint_ref))
        return AgentReplayResult(run_id=context.run_id, status="replayed_debug", read_only=True)

    def get_status(self, run_id: str, owner_id: str) -> AgentRunStatus:
        return AgentRunStatus(
            run_id=run_id,
            status="running",
            owner_id=owner_id,
            output_refs=self.status_output_refs,
            trace_refs=self.status_trace_refs,
            metadata=self.status_metadata,
            formal_write_blocked=True,
        )

    def get_timeline(self, run_id: str, owner_id: str, cursor: str | None = None, limit: int = 50) -> AgentRunTimelinePage:
        self.timeline_requests.append((run_id, owner_id))
        return self.timeline

    def cancel(self, run_id: str, owner_id: str, reason: str, actor_id: str) -> AgentRunStatus:
        self.cancelled.append((run_id, owner_id, reason, actor_id))
        return AgentRunStatus(
            run_id=run_id,
            status="cancelled",
            owner_id=owner_id,
            output_refs=self.status_output_refs,
            trace_refs=self.status_trace_refs,
            metadata={**self.status_metadata, "reason": reason},
            formal_write_blocked=True,
        )


class _FormalResumeRunner(_RecordingRunner):
    def resume(
        self, context: AgentRunContext, interrupt_ref: str, resume_payload: dict[str, object]
    ) -> AgentRunResult:
        self.resumed.append((context, interrupt_ref, resume_payload))
        return AgentRunResult(run_id=context.run_id, status="running", formal_refs=("formal_question_1",))


class _ReplaySideEffectRunner(_RecordingRunner):
    def replay(self, context: AgentRunContext, checkpoint_ref: str) -> AgentReplayResult:
        return AgentReplayResult(
            run_id=context.run_id,
            status="replayed",
            read_only=True,
            formal_write_blocked=True,
            trace_refs=(checkpoint_ref,),
            metadata={
                "provider_calls": 1,
                "tool_calls": 1,
                "repository_writes": 1,
            },
        )


def _start_only_registry() -> AgentGraphRegistry:
    return AgentGraphRegistry(
        descriptors={
            "start_only_graph": GraphDescriptor(
                graph_name="start_only_graph",
                graph_version="test-start-only",
                capability="start_only",
                lifecycle_status="active",
                runtime_flag_key="AIFI_GRAPH_START_ONLY_ENABLED",
                default_enabled=False,
                supported_entrypoints=("start",),
                supported_outputs=("candidate_refs",),
                prompt_contract_ids=("P-START-ONLY-001",),
                eval_suite_ids=("EVAL-START-ONLY-001",),
                runtime_max_steps=1,
                runtime_max_retries=0,
                runtime_timeout_seconds=5,
                runtime_stop_conditions=P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
                runtime_allowed_tools=("start_only_runtime_entry",),
                runtime_allowed_callers=("facade",),
                runtime_side_effect_policy="candidate_write",
                required_permissions=("owner",),
            )
        },
        task_map={"start_only_task": "start_only_graph"},
    )
