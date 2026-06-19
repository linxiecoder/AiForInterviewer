from __future__ import annotations

from dataclasses import is_dataclass

import pytest

import app.application.agents.handoff as agent_handoff
import app.application.agents.runtime as agent_runtime
from app.application.agents.contracts import (
    AgentExecutionPlan,
    AgentRuntimeLoopPolicy,
    HandoffContract,
    P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
)
from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentCommandEnvelope,
    AgentGraphRunner,
    AgentReplayResult,
    AgentRunContext,
    AgentRunResult,
    AgentRunStatus,
    AgentTimelineEvent,
    AgentTaskStatusRef,
    AgentRunTimelinePage,
    RuntimeValidationError,
    classify_agent_runtime_status,
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


def test_graph_runner_adapter_exposes_agent_executor_boundary() -> None:
    runner = _StubRunner()
    adapter_cls = getattr(agent_runtime, "AgentGraphRunnerExecutorAdapter", None)
    assert adapter_cls is not None
    executor = adapter_cls(runner)
    plan = AgentExecutionPlan(
        plan_id="plan_1",
        run_id="arun_1",
        ai_task_id="aitask_1",
        agent_id="polish_question_graph",
        owner_id="owner_1",
        actor_id="actor_1",
        graph_name="polish_question_graph",
        graph_version="v0",
        objective="produce a question candidate",
        input_refs=("session_1",),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_1",
        runtime_loop_policy=_runtime_loop_policy(),
    )

    result = executor.start(plan)
    replay = executor.replay("arun_1", trace_ref="ackpt_1")
    status = executor.get_status("arun_1")
    timeline = executor.get_timeline("arun_1")
    cancelled = executor.cancel("arun_1", reason="user_cancelled", actor_id="actor_1")

    assert isinstance(executor, agent_runtime.AgentExecutor)
    assert result.candidate_refs == ("candidate_ref_1",)
    assert result.trace.run_id == "arun_1"
    assert result.trace.agent_id == "polish_question_graph"
    assert result.trace.agent_version == "v0"
    assert result.trace.ai_task_id == "aitask_1"
    assert result.trace.input_refs == ("session_1",)
    assert result.metadata["formal_write_blocked"] is True
    assert result.metadata["source_boundary"] == "AgentGraphRunner"
    assert replay.status == "replayed_debug"
    assert replay.metadata["read_only"] is True
    assert replay.metadata["formal_write_blocked"] is True
    assert status.run_id == "arun_1"
    assert timeline.run_id == "arun_1"
    assert cancelled.metadata["formal_write_blocked"] is True


def test_graph_runner_adapter_preserves_replay_failure_status_and_trace_comparison() -> None:
    runner = _ReplayFailureRunner()
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(runner)
    executor.start(
        AgentExecutionPlan(
            plan_id="plan_1",
            run_id="arun_1",
            ai_task_id="aitask_1",
            agent_id="polish_question_graph",
            owner_id="owner_1",
            actor_id="actor_1",
            graph_name="polish_question_graph",
            graph_version="v0",
            objective="register context before replay",
            input_refs=("session_1",),
            requested_outputs=("candidate_refs",),
            idempotency_key="idem_1",
            runtime_loop_policy=_runtime_loop_policy(),
        )
    )

    replay = executor.replay("arun_1", trace_ref="ackpt_1")

    assert replay.status == "replayed_failed"
    assert replay.trace.failure_reason == "validation_failed"
    assert replay.trace.fallback_reason == "provider_disabled"
    assert replay.trace.validation_refs == ("validation_ref_replay",)
    assert replay.metadata["original_status"] == "validation_failed"
    assert replay.metadata["replay_trace_match"] is True
    assert replay.metadata["replay_compared_trace_refs"] == ("ackpt_1", "validation_ref_replay")


def test_graph_runner_adapter_rejects_replay_with_provider_or_repository_side_effects() -> None:
    runner = _ReplaySideEffectRunner()
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(runner)
    executor.start(
        AgentExecutionPlan(
            plan_id="plan_1",
            run_id="arun_1",
            ai_task_id="aitask_1",
            agent_id="polish_question_graph",
            owner_id="owner_1",
            actor_id="actor_1",
            graph_name="polish_question_graph",
            graph_version="v0",
            objective="register context before side-effect replay",
            input_refs=("session_1",),
            requested_outputs=("candidate_refs",),
            idempotency_key="idem_1",
            runtime_loop_policy=_runtime_loop_policy(),
        )
    )

    with pytest.raises(RuntimeValidationError, match="replay cannot call"):
        executor.replay("arun_1", trace_ref="ackpt_1")


def test_graph_runner_adapter_preserves_facade_status_payload_refs() -> None:
    runner = _StatusPayloadRunner()
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(runner)

    result = executor.start(
        AgentExecutionPlan(
            plan_id="plan_1",
            run_id="arun_1",
            ai_task_id="aitask_1",
            agent_id="polish_question_graph",
            owner_id="owner_1",
            actor_id="actor_1",
            graph_name="polish_question_graph",
            graph_version="v0",
            objective="preserve facade status refs",
            input_refs=("session_1",),
            requested_outputs=("candidate_refs", "interrupt_refs"),
            idempotency_key="idem_1",
            runtime_loop_policy=_runtime_loop_policy(),
        )
    )

    assert result.interrupt_refs == ("interrupt_ref_1",)
    assert result.output_refs == ("question_candidate_ref_1",)
    assert result.candidate_payloads[0].candidate_ref == "question_candidate_ref_1"
    assert result.candidate_refs == ("question_candidate_ref_1",)


def test_graph_runner_adapter_blocks_formal_refs_from_runtime_result() -> None:
    runner = _FormalWritingRunner()
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(runner)

    with pytest.raises(ValueError, match="formal refs"):
        executor.start(
            AgentExecutionPlan(
                plan_id="plan_1",
                run_id="arun_1",
                ai_task_id="aitask_1",
                agent_id="polish_question_graph",
                owner_id="owner_1",
                actor_id="actor_1",
                graph_name="polish_question_graph",
                graph_version="v0",
                objective="produce a question candidate",
                input_refs=("session_1",),
                requested_outputs=("candidate_refs",),
                idempotency_key="idem_1",
                runtime_loop_policy=_runtime_loop_policy(),
            )
        )


def test_graph_runner_adapter_blocks_formal_refs_from_runtime_metadata_surfaces() -> None:
    plan = AgentExecutionPlan(
        plan_id="plan_formal_metadata",
        run_id="arun_formal_metadata",
        ai_task_id="aitask_formal_metadata",
        agent_id="polish_question_graph",
        owner_id="owner_1",
        actor_id="actor_1",
        graph_name="polish_question_graph",
        graph_version="v0",
        objective="block formal refs hidden in runtime metadata",
        input_refs=("session_1",),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_formal_metadata",
        runtime_loop_policy=_runtime_loop_policy(),
    )

    result_executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_FormalMetadataResultRunner())
    with pytest.raises(ValueError, match="formal refs"):
        result_executor.start(plan)

    status_executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_FormalMetadataStatusRunner())
    status_executor.start(plan)
    with pytest.raises(ValueError, match="formal refs"):
        status_executor.get_status("arun_formal_metadata")

    timeline_executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_FormalMetadataTimelineRunner())
    timeline_executor.start(plan)
    with pytest.raises(ValueError, match="formal refs"):
        timeline_executor.get_timeline("arun_formal_metadata")


def test_graph_runner_adapter_blocks_formal_write_counter_variants_from_runtime_metadata() -> None:
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_FormalCounterMetadataResultRunner())

    with pytest.raises(ValueError, match="formal refs"):
        executor.start(
            AgentExecutionPlan(
                plan_id="plan_formal_counter_metadata",
                run_id="arun_formal_counter_metadata",
                ai_task_id="aitask_formal_counter_metadata",
                agent_id="polish_question_graph",
                owner_id="owner_1",
                actor_id="actor_1",
                graph_name="polish_question_graph",
                graph_version="v0",
                objective="block formal write counters hidden in runtime metadata",
                input_refs=("session_1",),
                requested_outputs=("candidate_refs",),
                idempotency_key="idem_formal_counter_metadata",
                runtime_loop_policy=_runtime_loop_policy(),
            )
        )


def test_graph_runner_adapter_blocks_repository_and_db_write_counters_from_runtime_metadata() -> None:
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_RepositoryWriteMetadataResultRunner())

    with pytest.raises(ValueError, match="business writes"):
        executor.start(
            AgentExecutionPlan(
                plan_id="plan_repository_write_metadata",
                run_id="arun_repository_write_metadata",
                ai_task_id="aitask_repository_write_metadata",
                agent_id="polish_question_graph",
                owner_id="owner_1",
                actor_id="actor_1",
                graph_name="polish_question_graph",
                graph_version="v0",
                objective="block repository or db writes hidden in runtime metadata",
                input_refs=("session_1",),
                requested_outputs=("candidate_refs",),
                idempotency_key="idem_repository_write_metadata",
                runtime_loop_policy=_runtime_loop_policy(),
            )
        )


def test_graph_runner_adapter_blocks_fake_provider_metadata_from_runtime_result() -> None:
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_FakeProviderMetadataRunner())

    with pytest.raises(ValueError, match="fake provider"):
        executor.start(
            AgentExecutionPlan(
                plan_id="plan_fake_provider_metadata",
                run_id="arun_fake_provider_metadata",
                ai_task_id="aitask_fake_provider_metadata",
                agent_id="polish_question_graph",
                owner_id="owner_1",
                actor_id="actor_1",
                graph_name="polish_question_graph",
                graph_version="v0",
                objective="block fake provider metadata from runtime result",
                input_refs=("session_1",),
                requested_outputs=("candidate_refs",),
                idempotency_key="idem_fake_provider_metadata",
                runtime_loop_policy=_runtime_loop_policy(),
            )
        )


def test_graph_runner_adapter_blocks_fail_open_fallback_success_metadata() -> None:
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_FailOpenFallbackMetadataRunner())

    with pytest.raises(ValueError, match="fail-open"):
        executor.start(
            AgentExecutionPlan(
                plan_id="plan_failopen_metadata",
                run_id="arun_failopen_metadata",
                ai_task_id="aitask_failopen_metadata",
                agent_id="polish_question_graph",
                owner_id="owner_1",
                actor_id="actor_1",
                graph_name="polish_question_graph",
                graph_version="v0",
                objective="block fail-open fallback metadata from runtime result",
                input_refs=("session_1",),
                requested_outputs=("candidate_refs",),
                idempotency_key="idem_failopen_metadata",
                runtime_loop_policy=_runtime_loop_policy(),
            )
        )


def test_graph_runner_adapter_rejects_success_status_with_failure_reason() -> None:
    runner = _FailureReportedAsSuccessRunner()
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(runner)

    with pytest.raises(RuntimeValidationError, match="failure"):
        executor.start(
            AgentExecutionPlan(
                plan_id="plan_1",
                run_id="arun_1",
                ai_task_id="aitask_1",
                agent_id="polish_question_graph",
                owner_id="owner_1",
                actor_id="actor_1",
                graph_name="polish_question_graph",
                graph_version="v0",
                objective="produce a question candidate",
                input_refs=("session_1",),
                requested_outputs=("candidate_refs",),
                idempotency_key="idem_1",
                runtime_loop_policy=_runtime_loop_policy(),
            )
        )


def test_graph_runner_adapter_rejects_unknown_metadata_event_status() -> None:
    runner = _UnknownMetadataEventStatusRunner()
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(runner)

    with pytest.raises(RuntimeValidationError, match="unknown runtime status"):
        executor.start(
            AgentExecutionPlan(
                plan_id="plan_1",
                run_id="arun_1",
                ai_task_id="aitask_1",
                agent_id="polish_question_graph",
                owner_id="owner_1",
                actor_id="actor_1",
                graph_name="polish_question_graph",
                graph_version="v0",
                objective="reject unknown runtime metadata event status",
                input_refs=("session_1",),
                requested_outputs=("candidate_refs",),
                idempotency_key="idem_1",
                runtime_loop_policy=_runtime_loop_policy(),
            )
        )


def test_runtime_status_taxonomy_is_enforced_by_runtime_dtos() -> None:
    assert classify_agent_runtime_status("queued") == "pending"
    assert classify_agent_runtime_status("agent_orchestration_blocked") == "blocked"
    assert classify_agent_runtime_status("replayed_debug") == "replayed"
    assert classify_agent_runtime_status("requires_user_confirmation") == "interrupted"

    with pytest.raises(RuntimeValidationError, match="unknown runtime status"):
        AgentRunResult(run_id="arun_unknown", status="made_up_status")

    with pytest.raises(RuntimeValidationError, match="failure"):
        AgentRunResult(
            run_id="arun_false_success",
            status="agent_orchestration_succeeded",
            metadata={"failure_reason": "validation_failed"},
        )

    with pytest.raises(RuntimeValidationError, match="failure"):
        AgentRunStatus(
            run_id="arun_false_status",
            owner_id="owner_1",
            status="generated",
            metadata={"failure_reason": "provider_failed"},
        )

    with pytest.raises(RuntimeValidationError, match="unknown runtime status"):
        AgentReplayResult(run_id="arun_replay", status="write_enabled_replay")

    with pytest.raises(RuntimeValidationError, match="unknown runtime status"):
        AgentTaskStatusRef(ai_task_id="aitask_1", agent_run_id="arun_1", status="doneish")


def test_graph_runner_adapter_fails_closed_without_runtime_loop_policy() -> None:
    runner = _StubRunner()
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(runner)

    with pytest.raises(ValueError, match="runtime loop policy"):
        executor.start(
            AgentExecutionPlan(
                plan_id="plan_1",
                run_id="arun_1",
                ai_task_id="aitask_1",
                agent_id="polish_question_graph",
                owner_id="owner_1",
                actor_id="actor_1",
                graph_name="polish_question_graph",
                graph_version="v0",
                objective="produce a question candidate",
                input_refs=("session_1",),
                requested_outputs=("candidate_refs",),
                idempotency_key="idem_1",
            )
        )


def test_graph_runner_adapter_enforces_loop_bound_exhaustion_without_success() -> None:
    blocked_executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_MaxStepsBlockedRunner())
    blocked = blocked_executor.start(_execution_plan(plan_id="plan_steps_blocked", run_id="arun_steps_blocked"))

    assert blocked.status == "agent_orchestration_blocked"
    assert blocked.trace.failure_reason == "max_steps_exceeded"

    retry_failed_executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_RetryBoundFailureReasonRunner())
    retry_failed = retry_failed_executor.start(
        _execution_plan(plan_id="plan_retry_failure_reason", run_id="arun_retry_failure_reason")
    )
    assert retry_failed.status == "provider_failed"
    assert retry_failed.trace.failure_reason == "provider_failed"

    with pytest.raises(RuntimeValidationError, match="max_steps_exceeded"):
        agent_runtime.AgentGraphRunnerExecutorAdapter(_MaxStepsSuccessRunner()).start(
            _execution_plan(plan_id="plan_steps_success", run_id="arun_steps_success")
        )
    with pytest.raises(RuntimeValidationError, match="max_retries_exceeded"):
        agent_runtime.AgentGraphRunnerExecutorAdapter(_RetryBoundSuccessRunner()).start(
            _execution_plan(plan_id="plan_retry_success", run_id="arun_retry_success")
        )
    with pytest.raises(RuntimeValidationError, match="timeout"):
        agent_runtime.AgentGraphRunnerExecutorAdapter(_TimeoutSuccessRunner()).start(
            _execution_plan(plan_id="plan_timeout_success", run_id="arun_timeout_success")
        )


def test_graph_runner_adapter_validates_hitl_interrupt_and_resume_payload() -> None:
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_HitlInterruptRunner())
    result = executor.start(_execution_plan(plan_id="plan_hitl", run_id="arun_hitl"))

    assert result.status == "requires_user_confirmation"
    assert result.interrupt_refs == ("interrupt_ref_asset_conflict",)
    assert result.trace.low_confidence_flags == ("source_gap",)

    resumed = executor.resume(
        "arun_hitl",
        {
            "cross_agent_resume": True,
            "checkpoint_ref": "checkpoint_ref_hitl",
            "base_version": 1,
            "idempotency_key": "idem_resume_hitl",
            "owner_id": "owner_1",
            "interrupt_ref": "interrupt_ref_asset_conflict",
            "resume_action": "continue",
        },
    )
    assert resumed.status == "running"

    with pytest.raises(ValueError, match="owner scope"):
        executor.resume(
            "arun_hitl",
            {
                "cross_agent_resume": True,
                "checkpoint_ref": "checkpoint_ref_hitl",
                "base_version": 1,
                "idempotency_key": "idem_resume_hitl",
                "owner_id": "owner_2",
                "interrupt_ref": "interrupt_ref_asset_conflict",
                "resume_action": "continue",
            },
        )


def test_graph_runner_adapter_rejects_unscoped_or_repository_tool_calls() -> None:
    with pytest.raises(RuntimeValidationError, match="permission scope"):
        agent_runtime.AgentGraphRunnerExecutorAdapter(_UnscopedToolRunner()).start(
            _execution_plan(plan_id="plan_unscoped_tool", run_id="arun_unscoped_tool")
        )
    with pytest.raises(RuntimeValidationError, match="tool_not_allowed"):
        agent_runtime.AgentGraphRunnerExecutorAdapter(_DisallowedToolRunner()).start(
            _execution_plan(plan_id="plan_disallowed_tool", run_id="arun_disallowed_tool")
        )
    with pytest.raises(RuntimeValidationError, match="repository"):
        agent_runtime.AgentGraphRunnerExecutorAdapter(_RepositoryToolExposureRunner()).start(
            _execution_plan(plan_id="plan_repository_tool", run_id="arun_repository_tool")
        )


def test_graph_runner_adapter_rejects_fallback_reported_as_generated_success() -> None:
    with pytest.raises(ValueError, match="fallback"):
        agent_runtime.AgentGraphRunnerExecutorAdapter(_GeneratedFallbackSuccessRunner()).start(
            _execution_plan(plan_id="plan_fallback_success", run_id="arun_fallback_success")
        )


def test_graph_runner_adapter_passes_repair_strategy_and_fallback_semantics_to_runner() -> None:
    runner = _RecordingPolicyRunner()
    agent_runtime.AgentGraphRunnerExecutorAdapter(runner).start(
        _execution_plan(plan_id="plan_policy_semantics", run_id="arun_policy_semantics")
    )

    assert runner.last_policy["repair_strategy"] == "retry_within_bounds_then_fail_closed"
    assert runner.last_policy["fallback_semantics"] == "candidate_only_blocked_or_failed_never_generated_success"


def test_graph_runner_adapter_populates_phase8_trace_refs_from_runtime_result() -> None:
    runner = _TraceRichRunner()
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(runner)

    result = executor.start(
        AgentExecutionPlan(
            plan_id="plan_trace",
            run_id="arun_trace",
            ai_task_id="aitask_trace",
            agent_id="polish_question_graph",
            owner_id="owner_1",
            actor_id="actor_1",
            graph_name="polish_question_graph",
            graph_version="v1",
            objective="produce a trace-rich question candidate",
            input_refs=("session_1",),
            requested_outputs=("candidate_refs",),
            idempotency_key="idem_trace",
            runtime_loop_policy=_runtime_loop_policy(),
            metadata={
                "plan_refs": ("plan_ref_1",),
                "skill_refs": ("skill_ref_1",),
                "tool_refs": ("command_tool_ref_1",),
                "policy_refs": ("command_policy_ref_1",),
                "provider_refs": ("command_provider_ref_1",),
                "validation_refs": ("validation_ref_command",),
                "handoff_refs": ("handoff_ref_command",),
                "low_confidence_flags": ("command_source_gap",),
            },
        )
    )

    trace = result.trace
    assert result.handoff_refs == ("handoff_ref_command", "handoff_ref_1")
    assert trace.validation_refs == ("validation_ref_command", "validation_ref_1")
    assert trace.handoff_refs == ("handoff_ref_command", "handoff_ref_1")
    assert trace.tool_refs == (
        "command_tool_ref_1",
        "runtime_tool_context_retrieval",
        "runtime_tool_question_drafting",
    )
    assert trace.policy_refs == ("command_policy_ref_1", "policy_ref_grounding")
    assert trace.provider_refs == ("command_provider_ref_1", "provider_ref_llm_1")
    assert trace.plan_refs == ("plan_ref_1",)
    assert trace.skill_refs == ("skill_ref_1",)
    assert trace.low_confidence_flags == ("command_source_gap", "source_gap")
    assert trace.failure_reason == "validation_failed"
    assert trace.fallback_reason == "provider_disabled"
    assert "agent_orchestration_blocked" in trace.events
    assert "context_retrieval:succeeded" in trace.events


def test_graph_runner_adapter_reads_nested_runtime_trace_metadata_refs() -> None:
    runner = _NestedTraceMetadataRunner()
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(runner)

    result = executor.start(
        AgentExecutionPlan(
            plan_id="plan_nested_trace",
            run_id="arun_nested_trace",
            ai_task_id="aitask_nested_trace",
            agent_id="polish_feedback_graph",
            owner_id="owner_1",
            actor_id="actor_1",
            graph_name="polish_feedback_graph",
            graph_version="v1",
            objective="surface nested runtime trace refs",
            input_refs=("feedback_session_1",),
            requested_outputs=("candidate_refs",),
            idempotency_key="idem_nested_trace",
            runtime_loop_policy=_runtime_loop_policy(),
        )
    )
    status = executor.get_status("arun_nested_trace")
    timeline = executor.get_timeline("arun_nested_trace")

    assert result.trace.validation_refs == ("validation_ref_nested_runtime",)
    assert result.trace.handoff_refs == ("handoff_ref_nested_runtime",)
    assert result.trace.tool_refs == ("tool_ref_nested_runtime",)
    assert result.trace.policy_refs == ("policy_ref_nested_runtime",)
    assert result.trace.provider_refs == ("provider_ref_nested_runtime",)
    assert result.trace.low_confidence_flags == ("low_confidence_nested_runtime",)
    assert status.handoff_refs == ("handoff_ref_nested_runtime",)
    event = timeline.events[0]
    assert event.validation_refs == ("validation_ref_nested_runtime",)
    assert event.handoff_refs == ("handoff_ref_nested_runtime",)
    assert event.tool_refs == ("tool_ref_nested_runtime",)
    assert event.policy_refs == ("policy_ref_nested_runtime",)
    assert event.provider_refs == ("provider_ref_nested_runtime",)
    assert event.low_confidence_flags == ("low_confidence_nested_runtime",)


def test_graph_runner_adapter_maps_phase8_trace_refs_from_timeline_event_metadata() -> None:
    runner = _TraceRichTimelineRunner()
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(runner)
    executor.start(
        AgentExecutionPlan(
            plan_id="plan_timeline",
            run_id="arun_timeline",
            ai_task_id="aitask_timeline",
            agent_id="polish_question_graph",
            owner_id="owner_1",
            actor_id="actor_1",
            graph_name="polish_question_graph",
            graph_version="v1",
            objective="surface trace refs in timeline",
            input_refs=("session_1",),
            requested_outputs=("candidate_refs",),
            idempotency_key="idem_timeline",
            runtime_loop_policy=_runtime_loop_policy(),
            metadata={
                "plan_refs": ("plan_ref_command",),
                "skill_refs": ("skill_ref_command",),
                "tool_refs": ("command_tool_ref_timeline",),
                "policy_refs": ("command_policy_ref_timeline",),
                "provider_refs": ("command_provider_ref_timeline",),
                "validation_refs": ("validation_ref_command_timeline",),
                "handoff_refs": ("handoff_ref_command_timeline",),
                "low_confidence_flags": ("command_source_gap_timeline",),
            },
        )
    )

    timeline = executor.get_timeline("arun_timeline")

    assert len(timeline.events) == 1
    event = timeline.events[0]
    assert event.output_refs == ("timeline_output_ref", "timeline_output_ref_meta")
    assert event.candidate_refs == ("timeline_candidate_ref",)
    assert event.plan_refs == ("plan_ref_command", "plan_ref_event")
    assert event.skill_refs == ("skill_ref_command", "skill_ref_event")
    assert event.tool_refs == ("command_tool_ref_timeline", "runtime_tool_timeline")
    assert event.policy_refs == ("command_policy_ref_timeline", "policy_ref_timeline")
    assert event.provider_refs == ("command_provider_ref_timeline", "provider_ref_timeline")
    assert event.validation_refs == (
        "validation_ref_command_timeline",
        "validation_ref_from_metadata",
        "validation_ref_from_refs",
    )
    assert event.handoff_refs == (
        "handoff_ref_command_timeline",
        "handoff_ref_from_metadata",
        "handoff_ref_from_refs",
    )
    assert event.low_confidence_flags == ("command_source_gap_timeline", "timeline_source_gap")
    assert event.failure_reason == "validation_failed"
    assert event.fallback_reason == "provider_disabled"


def test_graph_runner_adapter_exposes_handoff_refs_on_status_snapshot() -> None:
    runner = _HandoffStatusRunner()
    executor = agent_runtime.AgentGraphRunnerExecutorAdapter(runner)
    executor.start(
        AgentExecutionPlan(
            plan_id="plan_status",
            run_id="arun_status",
            ai_task_id="aitask_status",
            agent_id="polish_question_graph",
            owner_id="owner_1",
            actor_id="actor_1",
            graph_name="polish_question_graph",
            graph_version="v1",
            objective="surface handoff refs in status",
            input_refs=("session_1",),
            requested_outputs=("candidate_refs",),
            idempotency_key="idem_status",
            runtime_loop_policy=_runtime_loop_policy(),
        )
    )

    status = executor.get_status("arun_status")

    assert status.handoff_refs == ("handoff_ref_status_meta", "handoff_ref_status_trace")


def test_agent_executor_handoff_plan_routes_candidate_to_target_executor_without_raw_payload() -> None:
    source_executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_HandoffSourceRunner())
    source_result = source_executor.start(
        AgentExecutionPlan(
            plan_id="plan_source",
            run_id="arun_source",
            ai_task_id="aitask_source",
            agent_id="polish_question_agent",
            owner_id="owner_1",
            actor_id="actor_1",
            graph_name="polish_question_graph",
            graph_version="v1",
            objective="produce a typed question candidate",
            input_refs=("session_1",),
            requested_outputs=("question_candidate",),
            idempotency_key="idem_source",
            runtime_loop_policy=_runtime_loop_policy(),
        )
    )
    contract = HandoffContract(
        contract_id="question_to_feedback",
        candidate_ref_types=("question_candidate",),
        payload_schema_id="schema.question_candidate.v1",
        validation_refs=("validation_ref_contract",),
        side_effect_key="side_effect_question_to_feedback",
        idempotency_key="idem_handoff_question_to_feedback",
    )

    target_plan = agent_handoff.build_agent_handoff_plan(
        source_result=source_result,
        handoff_contract=contract,
        target_plan_id="plan_target",
        target_agent_id="polish_feedback_agent",
        owner_id="owner_1",
        actor_id="actor_1",
        objective="review the handed-off question candidate",
        runtime_loop_policy=_runtime_loop_policy(),
    )
    target_runner = _RecordingHandoffTargetRunner()
    target_executor = agent_runtime.AgentGraphRunnerExecutorAdapter(target_runner)

    target_result = target_executor.start(target_plan)

    assert target_plan.input_refs == ("handoff_question_candidate_ref_1",)
    assert target_plan.handoff_contract == contract
    assert target_result.metadata["formal_write_blocked"] is True
    handoff_metadata = target_runner.last_command.metadata["handoff_envelope"]
    assert handoff_metadata == {
        "handoff_ref": "handoff_question_candidate_ref_1",
        "candidate_ref": "question_candidate_ref_1",
        "candidate_type": "question_candidate",
        "payload_schema_id": "schema.question_candidate.v1",
        "trace_refs": ("trace_ref_candidate", "trace_arun_source"),
        "validation_refs": ("validation_ref_contract", "validation_ref_candidate"),
        "side_effect_key": "side_effect_question_to_feedback",
        "idempotency_key": "idem_handoff_question_to_feedback",
    }
    serialized_metadata = str(target_runner.last_command.metadata)
    assert "question_text" not in serialized_metadata
    assert "raw_prompt" not in serialized_metadata
    assert "formal_refs" not in serialized_metadata
    timeline = target_executor.get_timeline("arun_plan_target")
    assert len(timeline.events) == 1
    event_trace = timeline.events[0]
    assert event_trace.input_refs == ("handoff_question_candidate_ref_1",)
    assert event_trace.handoff_refs == ("handoff_question_candidate_ref_1",)
    assert event_trace.candidate_refs == ("question_candidate_ref_1", "feedback_candidate_ref_1")
    assert event_trace.validation_refs == ("validation_ref_contract", "validation_ref_candidate")
    event_metadata = str(event_trace.metadata)
    assert "question_text" not in event_metadata
    assert "raw_prompt" not in event_metadata

    mismatched_contract = HandoffContract(
        contract_id="wrong_type",
        candidate_ref_types=("feedback_candidate",),
        payload_schema_id="schema.question_candidate.v1",
        validation_refs=("validation_ref_contract",),
        side_effect_key="side_effect_wrong",
        idempotency_key="idem_wrong",
    )
    with pytest.raises(ValueError, match="candidate type"):
        agent_handoff.build_agent_handoff_plan(
            source_result=source_result,
            handoff_contract=mismatched_contract,
            target_plan_id="plan_wrong",
            target_agent_id="polish_feedback_agent",
            owner_id="owner_1",
            objective="reject incompatible candidate handoff",
            runtime_loop_policy=_runtime_loop_policy(),
        )


def test_execute_agent_handoff_starts_target_executor_with_typed_refs_only() -> None:
    source_executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_HandoffSourceRunner())
    source_result = source_executor.start(
        AgentExecutionPlan(
            plan_id="plan_source_execute",
            run_id="arun_source_execute",
            ai_task_id="aitask_source_execute",
            agent_id="polish_question_agent",
            owner_id="owner_1",
            actor_id="actor_1",
            graph_name="polish_question_graph",
            graph_version="v1",
            objective="produce a typed question candidate for execution",
            input_refs=("session_1",),
            requested_outputs=("question_candidate",),
            idempotency_key="idem_source_execute",
            runtime_loop_policy=_runtime_loop_policy(),
        )
    )
    contract = HandoffContract(
        contract_id="question_to_feedback_execute",
        candidate_ref_types=("question_candidate",),
        payload_schema_id="schema.question_candidate.v1",
        validation_refs=("validation_ref_contract",),
        side_effect_key="side_effect_question_to_feedback",
        idempotency_key="idem_handoff_question_to_feedback",
    )
    target_runner = _RecordingHandoffTargetRunner()
    target_executor = agent_runtime.AgentGraphRunnerExecutorAdapter(target_runner)

    target_result = agent_handoff.execute_agent_handoff(
        source_result=source_result,
        handoff_contract=contract,
        target_executor=target_executor,
        target_plan_id="plan_target_execute",
        target_agent_id="polish_feedback_agent",
        owner_id="owner_1",
        actor_id="actor_1",
        objective="execute the typed candidate handoff",
        runtime_loop_policy=_runtime_loop_policy(),
    )

    assert target_result.run_id == "arun_plan_target_execute"
    assert target_result.candidate_refs == ("feedback_candidate_ref_1",)
    assert target_result.metadata["formal_write_blocked"] is True
    command_metadata = target_runner.last_command.metadata
    assert command_metadata["handoff_refs"] == ("handoff_question_candidate_ref_1",)
    assert command_metadata["handoff_envelope"]["candidate_ref"] == "question_candidate_ref_1"
    assert command_metadata["handoff_envelope"]["validation_refs"] == (
        "validation_ref_contract",
        "validation_ref_candidate",
    )
    serialized_metadata = str(command_metadata)
    assert "question_text" not in serialized_metadata
    assert "raw_prompt" not in serialized_metadata
    assert "full_asset_body" not in serialized_metadata
    assert "formal_refs" not in serialized_metadata


def test_agent_executor_asset_update_handoff_carries_body_ref_without_raw_asset_body() -> None:
    source_executor = agent_runtime.AgentGraphRunnerExecutorAdapter(_AssetUpdateHandoffSourceRunner())
    source_result = source_executor.start(
        AgentExecutionPlan(
            plan_id="plan_asset_source",
            run_id="arun_asset_source",
            ai_task_id="aitask_asset_source",
            agent_id="polish_feedback_agent",
            owner_id="owner_1",
            actor_id="actor_1",
            graph_name="polish_feedback_graph",
            graph_version="v1",
            objective="produce a typed asset update candidate",
            input_refs=("feedback_candidate_ref_1",),
            requested_outputs=("asset_update_candidate",),
            idempotency_key="idem_asset_source",
            runtime_loop_policy=_runtime_loop_policy(),
        )
    )
    descriptor = source_result.metadata["handoff_candidate_descriptors"][0]
    contract = HandoffContract(
        contract_id="feedback_asset_update_to_formal_handoff",
        candidate_ref_types=("asset_update_candidate",),
        payload_schema_id="polish_asset_update_candidate.v1",
        validation_refs=("validation_ref_asset_contract",),
        side_effect_key="asset_update_candidate_handoff",
        idempotency_key="idem_asset_update_handoff",
    )

    target_plan = agent_handoff.build_agent_handoff_plan(
        source_result=source_result,
        handoff_contract=contract,
        target_plan_id="plan_asset_target",
        target_agent_id="polish_asset_handoff_agent",
        owner_id="owner_1",
        actor_id="actor_1",
        objective="review refs-only asset update candidate before formal write",
        runtime_loop_policy=_runtime_loop_policy(),
        candidate_ref="asset_update_candidate_ref_payment_recovery",
    )

    assert descriptor["asset_update_candidate_ref"] == "asset_update_candidate_ref_payment_recovery"
    assert descriptor["asset_body_ref"] == "asset_body_ref_payment_recovery"
    assert descriptor["asset_schema_id"] == "project_asset.update_candidate.v1"
    assert descriptor["formal_write_blocked_until"] == "user_confirmation"
    assert descriptor["user_confirmation_required"] is True
    assert target_plan.input_refs == ("handoff_asset_update_candidate_ref_payment_recovery",)
    handoff_metadata = target_plan.metadata["handoff_envelope"]
    assert handoff_metadata == {
        "handoff_ref": "handoff_asset_update_candidate_ref_payment_recovery",
        "candidate_ref": "asset_update_candidate_ref_payment_recovery",
        "candidate_type": "asset_update_candidate",
        "payload_schema_id": "polish_asset_update_candidate.v1",
        "trace_refs": ("trace_ref_asset_candidate", "trace_arun_asset_source"),
        "validation_refs": ("validation_ref_asset_contract", "validation_ref_asset_candidate"),
        "side_effect_key": "asset_update_candidate_handoff",
        "idempotency_key": "idem_asset_update_handoff",
        "asset_update_candidate_ref": "asset_update_candidate_ref_payment_recovery",
        "asset_body_ref": "asset_body_ref_payment_recovery",
        "asset_schema_id": "project_asset.update_candidate.v1",
        "formal_write_blocked_until": "user_confirmation",
        "user_confirmation_required": True,
    }
    serialized_metadata = str(target_plan.metadata)
    assert "full_asset_body" not in serialized_metadata
    assert "asset_body_text" not in serialized_metadata
    assert "formal_refs" not in serialized_metadata


def _execution_plan(*, plan_id: str, run_id: str) -> AgentExecutionPlan:
    return AgentExecutionPlan(
        plan_id=plan_id,
        run_id=run_id,
        ai_task_id=f"aitask_{plan_id}",
        agent_id="polish_question_graph",
        owner_id="owner_1",
        actor_id="actor_1",
        graph_name="polish_question_graph",
        graph_version="v1",
        objective="exercise controlled runtime loop policy",
        input_refs=("session_1",),
        requested_outputs=("candidate_refs",),
        idempotency_key=f"idem_{plan_id}",
        runtime_loop_policy=_runtime_loop_policy(),
    )


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


class _ReplayFailureRunner(_StubRunner):
    def replay(self, context: AgentRunContext, checkpoint_ref: str) -> AgentReplayResult:
        return AgentReplayResult(
            run_id=context.run_id,
            status="replayed_failed",
            read_only=True,
            formal_write_blocked=True,
            trace_refs=(checkpoint_ref, "validation_ref_replay"),
            metadata={
                "original_status": "validation_failed",
                "failure_reason": "validation_failed",
                "fallback_reason": "provider_disabled",
                "validation_refs": ("validation_ref_replay",),
                "replay_trace_match": True,
                "replay_compared_trace_refs": (checkpoint_ref, "validation_ref_replay"),
            },
        )


class _ReplaySideEffectRunner(_StubRunner):
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


class _FormalWritingRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(run_id=context.run_id, status="queued", formal_refs=("question_1",))


class _FormalMetadataResultRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="queued",
            metadata={"formal_refs": ("question_1",)},
        )


class _FormalMetadataStatusRunner(_StubRunner):
    def get_status(self, run_id: str, owner_id: str) -> AgentRunStatus:
        return AgentRunStatus(
            run_id=run_id,
            status="queued",
            owner_id=owner_id,
            formal_write_blocked=True,
            metadata={"formal_refs": ("question_1",)},
        )


class _FormalMetadataTimelineRunner(_StubRunner):
    def get_timeline(self, run_id: str, owner_id: str, cursor: str | None = None, limit: int = 50) -> AgentRunTimelinePage:
        return AgentRunTimelinePage(
            run_id=run_id,
            events=(
                AgentTimelineEvent(
                    event_id="evt_formal_ref_leak",
                    event_type="runtime_formal_ref_leak",
                    summary="runtime event leaked formal refs",
                    metadata={"formal_refs": ("question_1",)},
                ),
            ),
            next_cursor=None,
        )


class _FormalCounterMetadataResultRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="queued",
            metadata={
                "formal_write_blocked": True,
                "nested_runtime_counters": {
                    "formal_write_count": 1,
                    "formal_writes": "1",
                },
            },
        )


class _RepositoryWriteMetadataResultRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="queued",
            metadata={
                "side_effect_counters": {
                    "repository_writes": 1,
                    "db_business_writes": "1",
                },
            },
        )


class _FakeProviderMetadataRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="queued",
            metadata={
                "provider_trace": {
                    "provider_mode": "fake",
                    "fake_provider_used": True,
                },
            },
        )


class _FailOpenFallbackMetadataRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="queued",
            metadata={
                "fallback_reported_as_generated_success": True,
            },
        )


class _StatusPayloadRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        payload = AgentCandidatePayload(
            candidate_ref="question_candidate_ref_1",
            candidate_type="question_candidate",
            payload_schema_id="schema.question_candidate.v1",
            payload={"candidate_ref": "question_candidate_ref_1"},
        )
        return AgentRunResult(
            run_id=context.run_id,
            status="requires_user_confirmation",
            output_refs=("question_candidate_ref_1",),
            interrupt_refs=("interrupt_ref_1",),
            candidate_payloads=(payload,),
        )


class _FailureReportedAsSuccessRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="agent_orchestration_succeeded",
            output_refs=("candidate_ref_1",),
            metadata={"failure_reason": "validation_failed"},
        )


class _UnknownMetadataEventStatusRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="agent_orchestration_blocked",
            output_refs=("candidate_ref_1",),
            metadata={
                "phase_results": ({"phase": "validation", "status": "doneish"},),
                "tool_results": ({"tool_name": "context_retrieval", "status": "succeeded"},),
            },
        )


class _MaxStepsBlockedRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="agent_orchestration_blocked",
            metadata={
                "runtime_step_count": 4,
                "stop_condition": "max_steps_exceeded",
                "failure_reason": "max_steps_exceeded",
            },
        )


class _MaxStepsSuccessRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="fake_runtime_succeeded",
            output_refs=("candidate_ref_1",),
            metadata={"runtime_step_count": 4},
        )


class _RetryBoundSuccessRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="fake_runtime_succeeded",
            output_refs=("candidate_ref_1",),
            metadata={"runtime_retry_count": 2},
        )


class _RetryBoundFailureReasonRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="provider_failed",
            metadata={"runtime_retry_count": 2, "failure_reason": "provider_failed"},
        )


class _TimeoutSuccessRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="fake_runtime_succeeded",
            output_refs=("candidate_ref_1",),
            metadata={"runtime_elapsed_seconds": 6},
        )


class _HitlInterruptRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        payload = AgentCandidatePayload(
            candidate_ref="asset_update_candidate_ref_1",
            candidate_type="asset_update_candidate",
            payload_schema_id="polish_asset_update_candidate.v1",
            payload={
                "candidate_ref": "asset_update_candidate_ref_1",
                "formal_write_blocked_until": "user_confirmation",
                "user_confirmation_required": True,
            },
            low_confidence_flags=("source_gap",),
        )
        return AgentRunResult(
            run_id=context.run_id,
            status="requires_user_confirmation",
            output_refs=("asset_update_candidate_ref_1",),
            interrupt_refs=("interrupt_ref_asset_conflict",),
            candidate_payloads=(payload,),
            metadata={
                "hitl_triggers": ("asset_conflict", "low_confidence", "ambiguous_ownership"),
                "asset_conflict_ref": "asset_conflict_ref_1",
                "ownership_ambiguity_ref": "ownership_ambiguity_ref_1",
                "low_confidence_flags": ("source_gap",),
                "interrupt_refs": ("interrupt_ref_asset_conflict",),
            },
        )


class _UnscopedToolRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="queued",
            metadata={"tool_results": ({"status": "succeeded"},)},
        )


class _DisallowedToolRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="queued",
            metadata={"tool_results": ({"tool_name": "unregistered_tool", "status": "succeeded"},)},
        )


class _RepositoryToolExposureRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="queued",
            metadata={
                "tool_results": (
                    {
                        "tool_name": "repository_lookup",
                        "permission_scope": "repository_read",
                        "status": "succeeded",
                    },
                )
            },
        )


class _GeneratedFallbackSuccessRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="fake_runtime_succeeded",
            output_refs=("candidate_ref_1",),
            metadata={"fallback_reason": "provider_disabled", "fallback_reported_as_generated_success": True},
        )


class _RecordingPolicyRunner(_StubRunner):
    last_policy: dict[str, object]

    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        policy = command.metadata.get("runtime_loop_policy")
        assert isinstance(policy, dict)
        self.last_policy = policy
        return AgentRunResult(run_id=context.run_id, status="queued", output_refs=("candidate_ref_1",))


class _TraceRichRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        payload = AgentCandidatePayload(
            candidate_ref="question_candidate_ref_1",
            candidate_type="polish_question_candidate",
            payload_schema_id="polish_question_candidate.v1",
            payload={"candidate_ref": "question_candidate_ref_1", "question_text": "请说明支付链路一致性治理。"},
            trace_refs=("trace_ref_candidate",),
            validation_refs=("validation_ref_1",),
            low_confidence_flags=("source_gap",),
        )
        return AgentRunResult(
            run_id=context.run_id,
            status="agent_orchestration_blocked",
            output_refs=("question_result_ref_1", "question_candidate_ref_1"),
            trace_refs=("trace_ref_1", "validation_ref_1", "handoff_ref_1"),
            candidate_payloads=(payload,),
            metadata={
                "tool_results": (
                    {"tool_id": "runtime_tool_context_retrieval", "tool_name": "context_retrieval", "status": "succeeded"},
                    {"tool_id": "runtime_tool_question_drafting", "tool_name": "question_drafting", "status": "succeeded"},
                ),
                "policy_refs": ("policy_ref_grounding",),
                "provider_refs": ("provider_ref_llm_1",),
                "failure_reason": "validation_failed",
                "fallback_reason": "provider_disabled",
            },
        )


class _NestedTraceMetadataRunner(_StubRunner):
    _nested_trace_metadata = {
        "trace_refs": {
            "validation_refs": ("validation_ref_nested_runtime",),
            "handoff_refs": ("handoff_ref_nested_runtime",),
            "tool_refs": ("tool_ref_nested_runtime",),
            "policy_refs": ("policy_ref_nested_runtime",),
            "provider_refs": ("provider_ref_nested_runtime",),
            "low_confidence_flags": ("low_confidence_nested_runtime",),
        }
    }

    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        return AgentRunResult(
            run_id=context.run_id,
            status="fake_runtime_succeeded",
            output_refs=("feedback_candidate_ref_nested",),
            trace_refs=("ackpt_nested_runtime",),
            metadata=self._nested_trace_metadata,
        )

    def get_status(self, run_id: str, owner_id: str) -> AgentRunStatus:
        return AgentRunStatus(
            run_id=run_id,
            status="fake_runtime_succeeded",
            owner_id=owner_id,
            output_refs=("feedback_candidate_ref_nested",),
            trace_refs=("ackpt_nested_runtime",),
            formal_write_blocked=True,
            metadata=self._nested_trace_metadata,
        )

    def get_timeline(self, run_id: str, owner_id: str, cursor: str | None = None, limit: int = 50) -> AgentRunTimelinePage:
        return AgentRunTimelinePage(
            run_id=run_id,
            events=(
                AgentTimelineEvent(
                    event_id="trace_event_nested_runtime",
                    event_type="runtime_trace_recorded",
                    summary="runtime event with nested P8 trace refs",
                    refs=("ackpt_nested_runtime",),
                    metadata=self._nested_trace_metadata,
                ),
            ),
            next_cursor=None,
        )


class _TraceRichTimelineRunner(_StubRunner):
    def get_timeline(self, run_id: str, owner_id: str, cursor: str | None = None, limit: int = 50) -> AgentRunTimelinePage:
        return AgentRunTimelinePage(
            run_id=run_id,
            events=(
                AgentTimelineEvent(
                    event_id="trace_event_timeline",
                    event_type="validation_failed",
                    summary="timeline event with P8 refs",
                    refs=("timeline_output_ref", "validation_ref_from_refs", "handoff_ref_from_refs"),
                    metadata={
                        "output_refs": ("timeline_output_ref_meta",),
                        "candidate_refs": ("timeline_candidate_ref",),
                        "plan_refs": ("plan_ref_event",),
                        "skill_refs": ("skill_ref_event",),
                        "tool_refs": ("runtime_tool_timeline",),
                        "policy_refs": ("policy_ref_timeline",),
                        "provider_refs": ("provider_ref_timeline",),
                        "validation_refs": ("validation_ref_from_metadata",),
                        "handoff_refs": ("handoff_ref_from_metadata",),
                        "low_confidence_flags": ("timeline_source_gap",),
                        "failure_reason": "validation_failed",
                        "fallback_reason": "provider_disabled",
                    },
                ),
            ),
            next_cursor=None,
        )


class _HandoffStatusRunner(_StubRunner):
    def get_status(self, run_id: str, owner_id: str) -> AgentRunStatus:
        return AgentRunStatus(
            run_id=run_id,
            status="running",
            owner_id=owner_id,
            trace_refs=("handoff_ref_status_trace",),
            metadata={"handoff_refs": ("handoff_ref_status_meta",)},
        )


class _HandoffSourceRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        payload = AgentCandidatePayload(
            candidate_ref="question_candidate_ref_1",
            candidate_type="question_candidate",
            payload_schema_id="schema.question_candidate.v1",
            payload={"candidate_ref": "question_candidate_ref_1", "question_text": "请解释候选事实边界。"},
            trace_refs=("trace_ref_candidate",),
            validation_refs=("validation_ref_candidate",),
        )
        return AgentRunResult(
            run_id=context.run_id,
            status="agent_orchestration_blocked",
            output_refs=("question_candidate_ref_1",),
            trace_refs=("trace_arun_source",),
            candidate_payloads=(payload,),
            metadata={"raw_prompt": "hidden prompt must not cross handoff"},
        )


class _AssetUpdateHandoffSourceRunner(_StubRunner):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        payload = AgentCandidatePayload(
            candidate_ref="asset_update_candidate_ref_payment_recovery",
            candidate_type="asset_update_candidate",
            payload_schema_id="polish_asset_update_candidate.v1",
            payload={
                "candidate_ref": "asset_update_candidate_ref_payment_recovery",
                "candidate_type": "project_asset_update_candidate",
                "asset_body_ref": "asset_body_ref_payment_recovery",
                "asset_schema_id": "project_asset.update_candidate.v1",
                "source_feedback_candidate_ref": "feedback_candidate_ref_1",
                "formal_write_blocked_until": "user_confirmation",
                "user_confirmation_required": True,
                "formal_refs": [],
            },
            trace_refs=("trace_ref_asset_candidate",),
            validation_refs=("validation_ref_asset_candidate",),
        )
        return AgentRunResult(
            run_id=context.run_id,
            status="agent_orchestration_blocked",
            output_refs=("asset_update_candidate_ref_payment_recovery",),
            trace_refs=("trace_arun_asset_source",),
            candidate_payloads=(payload,),
            metadata={"raw_prompt": "hidden prompt must not cross handoff"},
        )


class _RecordingHandoffTargetRunner(_StubRunner):
    last_command: AgentCommandEnvelope

    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        self.last_command = command
        return AgentRunResult(
            run_id=context.run_id,
            status="queued",
            output_refs=("feedback_candidate_ref_1",),
            metadata={"handoff_refs": command.metadata.get("handoff_refs", ())},
        )

    def get_timeline(self, run_id: str, owner_id: str, cursor: str | None = None, limit: int = 50) -> AgentRunTimelinePage:
        return AgentRunTimelinePage(
            run_id=run_id,
            events=(
                AgentTimelineEvent(
                    event_id="handoff_target_started",
                    event_type="handoff_received",
                    summary="target executor received a typed handoff",
                    refs=("feedback_candidate_ref_1",),
                ),
            ),
            next_cursor=None,
        )


def _runtime_loop_policy() -> AgentRuntimeLoopPolicy:
    return AgentRuntimeLoopPolicy(
        max_steps=3,
        max_retries=1,
        timeout_seconds=5,
        stop_conditions=P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
        allowed_tools=("evidence_selection", "context_retrieval", "question_drafting"),
        allowed_callers=("polish_question_agent",),
        side_effect_policy="candidate_write",
    )
