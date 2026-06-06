from __future__ import annotations

import pytest

from app.application.agents.contracts import P8_REQUIRED_RUNTIME_STOP_CONDITIONS
from app.application.ai_runtime.contracts import (
    AgentCommandEnvelope,
    AgentRunContext,
    AgentRunStatus,
    GraphDisabledError,
    RuntimeConflictError,
    RuntimePolicyError,
    RuntimeValidationError,
)
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.langgraph.checkpointer import RefsOnlyLangGraphCheckpointer
from app.infrastructure.ai_runtime.langgraph.in_memory_runtime import InMemoryLangGraphRuntime


RAW_KEY = "raw" + "_prompt"
PROVIDER_KEY = "provider_" + "payload"


def test_pr4_in_memory_runtime_fails_closed_when_runtime_flags_default_false() -> None:
    runtime = InMemoryLangGraphRuntime()
    context = _context()

    with pytest.raises(GraphDisabledError):
        runtime.start(context, context.command)


def test_pr4_in_memory_runtime_start_resume_and_timeline_are_sanitized() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_flags(), checkpointer=checkpointer)
    context = _context()

    started = runtime.start(context, context.command)
    resumed = runtime.resume(
        context,
        interrupt_ref=started.interrupt_refs[0],
        resume_payload={
            RAW_KEY: "hidden prompt",
            PROVIDER_KEY: {"secret": "hidden"},
            "action": "approve",
            "checkpoint_ref": started.trace_refs[0],
            "base_version": 1,
            "idempotency_key": "idem_pr4_resume",
        },
    )
    status = runtime.get_status(context.run_id, context.owner_id)
    timeline = runtime.get_timeline(context.run_id, context.owner_id)

    assert started.status == "interrupted"
    assert resumed.status == "succeeded"
    assert resumed.formal_refs == ()
    assert status.formal_write_blocked is True
    assert len(checkpointer.list_refs(context.owner_id, context.run_id)) == 2
    assert [event.event_type for event in timeline.events] == [
        "run_started",
        "checkpoint_recorded",
        "interrupt_opened",
        "run_resumed",
        "checkpoint_recorded",
        "run_succeeded",
    ]
    first_checkpoint_ref, second_checkpoint_ref = resumed.trace_refs
    assert timeline.events[0].metadata == {
        "ai_task_id": context.ai_task_id,
        "input_refs": context.command.input_refs,
    }
    assert timeline.events[1].metadata["checkpoint_refs"] == (first_checkpoint_ref,)
    assert timeline.events[2].metadata["interrupt_refs"] == started.interrupt_refs
    assert timeline.events[2].metadata["checkpoint_refs"] == (first_checkpoint_ref,)
    assert timeline.events[3].metadata == {
        "resume": {"action": "approve"},
        "interrupt_refs": started.interrupt_refs,
        "checkpoint_refs": (first_checkpoint_ref,),
    }
    assert timeline.events[4].metadata["checkpoint_refs"] == (second_checkpoint_ref,)
    assert timeline.events[5].metadata["output_refs"] == resumed.output_refs
    assert timeline.events[5].metadata["candidate_refs"] == resumed.output_refs
    assert timeline.events[5].metadata["checkpoint_refs"] == resumed.trace_refs
    serialized = repr((started, resumed, status, timeline, checkpointer.snapshot()))
    for forbidden in ("hidden prompt", "provider_payload", "secret", "checkpoint_payload", "formal_question"):
        assert forbidden not in serialized


def test_pr4_in_memory_runtime_start_timeline_preserves_p8_ref_matrix_from_command_metadata() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_flags())
    command = AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("runtime_input_ref_1",),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_pr4_p8_refs",
        metadata={
            "runtime_loop_policy": _runtime_loop_policy_metadata(),
            "plan_refs": ("plan_ref_runtime_start",),
            "skill_refs": ("skill_ref_runtime_start",),
            "tool_refs": ("tool_ref_runtime_start",),
            "policy_refs": ("policy_ref_runtime_start",),
            "provider_refs": ("provider_ref_runtime_start",),
            "validation_refs": ("validation_ref_runtime_start",),
            "handoff_refs": ("handoff_ref_runtime_start",),
            "low_confidence_flags": ("source_gap_runtime_start",),
            "failure_reason": "validation_failed_partial_result",
            "fallback_reason": "provider_disabled",
            RAW_KEY: "must not escape",
            PROVIDER_KEY: {"secret": "hidden"},
            "full_resume": {"answer": "hidden"},
            "full_jd": "hidden jd",
            "full_asset_body": "hidden asset",
            "api_key": "hidden key",
        },
    )
    context = AgentRunContext(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_pr4_p8_refs",
        ai_task_id="aitask_pr4_p8_refs",
        graph_name="pr4_fake_runtime",
        graph_version="pr4",
        command=command,
    )

    runtime.start(context, command)

    run_started = runtime.get_timeline(context.run_id, context.owner_id).events[0]
    assert run_started.event_type == "run_started"
    assert run_started.metadata == {
        "ai_task_id": context.ai_task_id,
        "input_refs": command.input_refs,
        "plan_refs": ("plan_ref_runtime_start",),
        "skill_refs": ("skill_ref_runtime_start",),
        "tool_refs": ("tool_ref_runtime_start",),
        "policy_refs": ("policy_ref_runtime_start",),
        "provider_refs": ("provider_ref_runtime_start",),
        "validation_refs": ("validation_ref_runtime_start",),
        "handoff_refs": ("handoff_ref_runtime_start",),
        "low_confidence_flags": ("source_gap_runtime_start",),
        "failure_reason": "validation_failed_partial_result",
        "fallback_reason": "provider_disabled",
    }
    serialized = repr(run_started)
    for forbidden in (
        "must not escape",
        "provider_payload",
        "secret",
        "full_resume",
        "full_jd",
        "full_asset_body",
        "api_key",
    ):
        assert forbidden not in serialized


def test_pr4_in_memory_runtime_resume_timeline_preserves_p8_ref_matrix_from_command_metadata() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_flags())
    command = AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("runtime_input_ref_resume",),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_pr4_p8_resume_refs",
        metadata={
            "runtime_loop_policy": _runtime_loop_policy_metadata(),
            "plan_refs": ("plan_ref_runtime_resume",),
            "skill_refs": ("skill_ref_runtime_resume",),
            "tool_refs": ("tool_ref_runtime_resume",),
            "policy_refs": ("policy_ref_runtime_resume",),
            "provider_refs": ("provider_ref_runtime_resume",),
            "validation_refs": ("validation_ref_runtime_resume",),
            "handoff_refs": ("handoff_ref_runtime_resume",),
            "low_confidence_flags": ("source_gap_runtime_resume",),
            "failure_reason": "validation_failed_partial_result",
            "fallback_reason": "provider_disabled",
            RAW_KEY: "must not escape",
            PROVIDER_KEY: {"secret": "hidden"},
            "full_resume": {"answer": "hidden"},
            "full_jd": "hidden jd",
            "full_asset_body": "hidden asset",
            "api_key": "hidden key",
        },
    )
    context = AgentRunContext(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_pr4_p8_resume_refs",
        ai_task_id="aitask_pr4_p8_resume_refs",
        graph_name="pr4_fake_runtime",
        graph_version="pr4",
        command=command,
    )

    started = runtime.start(context, command)
    runtime.resume(
        context,
        interrupt_ref=started.interrupt_refs[0],
        resume_payload={
            RAW_KEY: "hidden prompt",
            PROVIDER_KEY: {"secret": "hidden"},
            "action": "approve",
            "checkpoint_ref": started.trace_refs[0],
            "base_version": 1,
            "idempotency_key": "idem_pr4_p8_resume_refs",
        },
    )

    timeline = runtime.get_timeline(context.run_id, context.owner_id)
    run_resumed = next(event for event in timeline.events if event.event_type == "run_resumed")
    run_succeeded = next(event for event in timeline.events if event.event_type == "run_succeeded")
    expected_refs = {
        "plan_refs": ("plan_ref_runtime_resume",),
        "skill_refs": ("skill_ref_runtime_resume",),
        "tool_refs": ("tool_ref_runtime_resume",),
        "policy_refs": ("policy_ref_runtime_resume",),
        "provider_refs": ("provider_ref_runtime_resume",),
        "validation_refs": ("validation_ref_runtime_resume",),
        "handoff_refs": ("handoff_ref_runtime_resume",),
        "low_confidence_flags": ("source_gap_runtime_resume",),
        "failure_reason": "validation_failed_partial_result",
        "fallback_reason": "provider_disabled",
    }
    for key, expected in expected_refs.items():
        assert run_resumed.metadata[key] == expected
        assert run_succeeded.metadata[key] == expected

    serialized = repr((run_resumed, run_succeeded))
    for forbidden in (
        "hidden prompt",
        "must not escape",
        "provider_payload",
        "secret",
        "full_resume",
        "full_jd",
        "full_asset_body",
        "api_key",
    ):
        assert forbidden not in serialized


def test_pr4_in_memory_runtime_cancel_records_refs_only_timeline_event() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_flags())
    context = _context()

    started = runtime.start(context, context.command)
    resumed = runtime.resume(
        context,
        interrupt_ref=started.interrupt_refs[0],
        resume_payload={
            RAW_KEY: "hidden prompt",
            PROVIDER_KEY: {"secret": "hidden"},
            "action": "approve",
            "checkpoint_ref": started.trace_refs[0],
            "base_version": 1,
            "idempotency_key": "idem_pr4_cancel",
        },
    )

    cancelled = runtime.cancel(
        context.run_id,
        context.owner_id,
        reason="user_cancelled_after_review",
        actor_id=context.actor_id,
    )
    timeline = runtime.get_timeline(context.run_id, context.owner_id)
    cancel_event = timeline.events[-1]

    assert cancelled.status == "cancelled"
    assert cancelled.output_refs == resumed.output_refs
    assert cancel_event.event_type == "run_cancelled"
    assert cancel_event.refs == (*resumed.output_refs, *resumed.trace_refs)
    assert cancel_event.metadata == {
        "reason": "user_cancelled_after_review",
        "actor_id": context.actor_id,
        "output_refs": resumed.output_refs,
        "candidate_refs": resumed.output_refs,
        "checkpoint_refs": resumed.trace_refs,
        "provider_calls": 0,
        "formal_business_writes": 0,
    }
    serialized = repr(cancel_event)
    for forbidden in ("provider_payload", "secret", "checkpoint_payload", "formal_question"):
        assert forbidden not in serialized


def test_pr4_in_memory_runtime_resume_requires_checkpoint_version_and_allowed_action() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_flags())
    context = _context()
    started = runtime.start(context, context.command)
    interrupt_ref = started.interrupt_refs[0]

    with pytest.raises(RuntimeValidationError, match="checkpoint_ref"):
        runtime.resume(
            context,
            interrupt_ref=interrupt_ref,
            resume_payload={
                "action": "approve",
                "base_version": 1,
                "idempotency_key": "idem_missing_checkpoint",
            },
        )

    with pytest.raises(RuntimeConflictError, match="checkpoint"):
        runtime.resume(
            context,
            interrupt_ref=interrupt_ref,
            resume_payload={
                "action": "approve",
                "checkpoint_ref": "ackpt_wrong",
                "base_version": 1,
                "idempotency_key": "idem_wrong_checkpoint",
            },
        )

    with pytest.raises(RuntimeConflictError, match="stale"):
        runtime.resume(
            context,
            interrupt_ref=interrupt_ref,
            resume_payload={
                "action": "approve",
                "checkpoint_ref": started.trace_refs[0],
                "base_version": 0,
                "idempotency_key": "idem_stale_version",
            },
        )

    with pytest.raises(RuntimeValidationError, match="unsupported resume action"):
        runtime.resume(
            context,
            interrupt_ref=interrupt_ref,
            resume_payload={
                "action": "defer_to_handoff",
                "checkpoint_ref": started.trace_refs[0],
                "base_version": 1,
                "idempotency_key": "idem_bad_action",
            },
        )


def test_pr4_in_memory_runtime_replay_is_read_only_and_does_not_mutate_checkpoints() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_flags(), checkpointer=checkpointer)
    context = _context()
    runtime.start(context, context.command)
    latest = checkpointer.latest(context.owner_id, "pr4_fake_runtime", context.run_id)
    assert latest is not None
    before = checkpointer.snapshot()
    timeline_before = runtime.get_timeline(context.run_id, context.owner_id)

    replayed = runtime.replay(context, checkpoint_ref=latest.checkpoint_ref)

    assert replayed.read_only is True
    assert replayed.formal_write_blocked is True
    assert replayed.timeline_refs == tuple(event.event_id for event in timeline_before.events)
    assert checkpointer.snapshot() == before
    assert runtime.get_timeline(context.run_id, context.owner_id) == timeline_before


def test_pr4_in_memory_runtime_replay_preserves_failure_status_and_trace_comparison() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_flags(), checkpointer=checkpointer)
    context = _context()
    runtime.start(context, context.command)
    latest = checkpointer.latest(context.owner_id, "pr4_fake_runtime", context.run_id)
    assert latest is not None
    runtime._statuses[(context.owner_id, context.run_id)] = AgentRunStatus(
        run_id=context.run_id,
        status="validation_failed",
        owner_id=context.owner_id,
        trace_refs=(latest.checkpoint_ref, "validation_ref_runtime"),
        formal_write_blocked=True,
        metadata={
            "failure_reason": "validation_failed",
            "fallback_reason": "provider_disabled",
            "validation_refs": ("validation_ref_runtime",),
        },
    )

    replayed = runtime.replay(context, checkpoint_ref=latest.checkpoint_ref)

    assert replayed.status == "replayed_failed"
    assert replayed.read_only is True
    assert replayed.formal_write_blocked is True
    assert replayed.metadata["original_status"] == "validation_failed"
    assert replayed.metadata["failure_reason"] == "validation_failed"
    assert replayed.metadata["fallback_reason"] == "provider_disabled"
    assert replayed.metadata["replay_trace_match"] is True
    assert replayed.metadata["replay_compared_trace_refs"] == (latest.checkpoint_ref, "validation_ref_runtime")
    assert replayed.metadata["provider_calls"] == 0
    assert replayed.metadata["tool_calls"] == 0
    assert replayed.metadata["repository_writes"] == 0
    assert replayed.metadata["formal_business_writes"] == 0


def test_pr4_in_memory_runtime_replay_preserves_nested_trace_refs_metadata() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_flags(), checkpointer=checkpointer)
    context = _context()
    runtime.start(context, context.command)
    latest = checkpointer.latest(context.owner_id, "pr4_fake_runtime", context.run_id)
    assert latest is not None
    runtime._statuses[(context.owner_id, context.run_id)] = AgentRunStatus(
        run_id=context.run_id,
        status="validation_failed",
        owner_id=context.owner_id,
        trace_refs=(latest.checkpoint_ref,),
        formal_write_blocked=True,
        metadata={
            "trace_refs": {
                "validation_refs": ("validation_ref_nested_replay",),
                "handoff_refs": ("handoff_ref_nested_replay",),
                "policy_refs": ("policy_ref_nested_replay",),
                "provider_refs": ("provider_ref_nested_replay",),
                "low_confidence_refs": ("source_gap_nested_replay",),
            },
        },
    )

    replayed = runtime.replay(context, checkpoint_ref=latest.checkpoint_ref)

    assert replayed.metadata["trace_refs"] == {
        "validation_refs": ("validation_ref_nested_replay",),
        "handoff_refs": ("handoff_ref_nested_replay",),
        "policy_refs": ("policy_ref_nested_replay",),
        "provider_refs": ("provider_ref_nested_replay",),
        "low_confidence_refs": ("source_gap_nested_replay",),
    }
    assert replayed.metadata["validation_refs"] == ("validation_ref_nested_replay",)
    assert replayed.metadata["handoff_refs"] == ("handoff_ref_nested_replay",)
    assert replayed.metadata["policy_refs"] == ("policy_ref_nested_replay",)
    assert replayed.metadata["provider_refs"] == ("provider_ref_nested_replay",)
    assert replayed.metadata["low_confidence_flags"] == ("source_gap_nested_replay",)


def test_pr4_in_memory_runtime_resume_does_not_bypass_runtime_gate() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    enabled_runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_flags(), checkpointer=checkpointer)
    context = _context()
    started = enabled_runtime.start(context, context.command)
    disabled_runtime = InMemoryLangGraphRuntime(
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": False, "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True}
        ),
        checkpointer=checkpointer,
    )

    with pytest.raises(GraphDisabledError):
        disabled_runtime.resume(context, interrupt_ref=started.interrupt_refs[0], resume_payload={"decision": "approved"})


def test_pr4_in_memory_runtime_start_rejects_command_mismatch() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_flags())
    context = _context()
    mismatched_command = AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("different_runtime_input_ref",),
        requested_outputs=("candidate_refs",),
        idempotency_key="different_idem_pr4",
    )

    with pytest.raises(RuntimePolicyError, match="command must match context command"):
        runtime.start(context, mismatched_command)


def test_pr4_in_memory_runtime_start_requires_runtime_loop_policy_metadata() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_flags())
    command = AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("runtime_input_ref_1",),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_pr4_missing_policy",
        metadata={RAW_KEY: "must not escape"},
    )
    context = AgentRunContext(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_pr4_missing_policy",
        ai_task_id="aitask_pr4_missing_policy",
        graph_name="pr4_fake_runtime",
        graph_version="pr4",
        command=command,
    )

    with pytest.raises(RuntimeValidationError, match="runtime_loop_policy"):
        runtime.start(context, context.command)


def _enabled_flags() -> RuntimeFlagResolver:
    return RuntimeFlagResolver(
        test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True}
    )


def _context() -> AgentRunContext:
    command = AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("runtime_input_ref_1",),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_pr4",
        metadata={"runtime_loop_policy": _runtime_loop_policy_metadata(), RAW_KEY: "must not escape"},
    )
    return AgentRunContext(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_pr4_fake",
        ai_task_id="aitask_pr4_fake",
        graph_name="pr4_fake_runtime",
        graph_version="pr4",
        command=command,
    )


def _runtime_loop_policy_metadata() -> dict[str, object]:
    return {
        "max_steps": 8,
        "max_retries": 1,
        "timeout_seconds": 30,
        "stop_conditions": P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
        "allowed_tools": ("generic_runtime_tool",),
        "allowed_callers": ("generic_runtime",),
        "side_effect_policy": "candidate_write",
    }
