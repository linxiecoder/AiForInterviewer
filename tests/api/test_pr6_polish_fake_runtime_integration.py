from __future__ import annotations

from dataclasses import asdict

import pytest

from app.application.ai_runtime.business_graphs.polish_feedback_graph import (
    POLISH_FEEDBACK_FAKE_RUNTIME_VERSION,
    POLISH_FEEDBACK_GRAPH_FLAG,
    POLISH_FEEDBACK_GRAPH_NAME,
    POLISH_FEEDBACK_GRAPH_VERSION,
    build_polish_feedback_graph_descriptor,
)
from app.application.ai_runtime.contracts import (
    AgentCommandEnvelope,
    AgentRunContext,
    GraphDisabledError,
    RuntimeConflictError,
    RuntimeValidationError,
    contains_sensitive_payload,
)
from app.application.ai_runtime.interrupts import AgentInterruptService
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.langgraph.checkpointer import RefsOnlyLangGraphCheckpointer
from app.infrastructure.ai_runtime.langgraph.in_memory_runtime import InMemoryLangGraphRuntime
from app.infrastructure.ai_runtime.langgraph.serializer import LangGraphRuntimeSerializer


RAW_PROMPT_KEY = "raw" + "_prompt"
RAW_COMPLETION_KEY = "raw" + "_completion"
PROVIDER_PAYLOAD_KEY = "provider" + "_payload"
CHECKPOINT_PAYLOAD_KEY = "checkpoint" + "_payload"
SOURCE_BODY_KEY = "full" + "_source_body"
QUESTION_TEXT_KEY = "question" + "_text"
ANSWER_TEXT_KEY = "answer" + "_text"


def test_pr6_graph_flag_default_false_blocks_in_memory_execution_and_retains_legacy_path() -> None:
    descriptor = build_polish_feedback_graph_descriptor()
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_without_graph_flag())
    context = _context()

    assert descriptor.graph_name == POLISH_FEEDBACK_GRAPH_NAME == "polish_feedback_graph"
    assert descriptor.graph_version == POLISH_FEEDBACK_GRAPH_VERSION == "pr5-skeleton"
    assert descriptor.implementation_pr == "PR5"
    assert descriptor.default_enabled is False
    assert descriptor.provider_enabled is False
    assert descriptor.formal_write_targets == ()
    assert descriptor.db_business_write_targets == ()
    assert descriptor.disabled_behavior == "legacy_direct_path_retained"

    with pytest.raises(GraphDisabledError):
        runtime.start(context, context.command)


def test_pr6_feedback_direct_runtime_requires_descriptor_runtime_loop_policy() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag())
    command = AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("session_ref_1", "question_ref_1", "answer_ref_1"),
        requested_outputs=("result_refs", "candidate_refs", "suggestion_refs"),
        idempotency_key="idem_pr6",
        metadata={"request_digest": "digest_ref_1", "idempotency_key_hash": "idem_hash_ref_1"},
    )
    context = _context(command=command)

    with pytest.raises(RuntimeValidationError, match="runtime_loop_policy"):
        runtime.start(context, context.command)


def test_pr6_feedback_direct_runtime_rejects_runtime_loop_policy_mismatch() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag())
    command = _command(metadata={"runtime_loop_policy": _runtime_loop_policy_metadata({"max_steps": 4})})
    context = _context(command=command)

    with pytest.raises(RuntimeValidationError, match="runtime_loop_policy.max_steps"):
        runtime.start(context, context.command)


def test_pr6_enabled_in_memory_integration_returns_refs_only_sanitized_schema() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag())
    context = _context(
        command=_command(
            metadata={
                "request_digest": "digest_ref_1",
                "idempotency_key_hash": "idem_hash_ref_1",
                "asset_update_candidate_refs": ["asset_update_candidate_ref_payment_recovery"],
                RAW_PROMPT_KEY: "hidden prompt",
                RAW_COMPLETION_KEY: "hidden completion",
                PROVIDER_PAYLOAD_KEY: {"token": "secret"},
                CHECKPOINT_PAYLOAD_KEY: {"state": "hidden"},
            },
        )
    )

    first = runtime.start(context, context.command)
    second = runtime.start(context, context.command)

    assert first == second
    assert first.status == "fake_runtime_succeeded"
    assert first.interrupt_refs == ()
    assert first.formal_refs == ()
    assert first.output_refs == (
        *tuple(first.metadata["output_refs"]["result_refs"]),
        *tuple(first.metadata["output_refs"]["candidate_refs"]),
    )
    assert first.trace_refs == tuple(first.metadata["trace_refs"]["checkpoint_refs"])
    assert len(first.candidate_payloads) == 2
    payloads_by_type = {candidate.candidate_type: candidate for candidate in first.candidate_payloads}
    feedback_payload = payloads_by_type["feedback_candidate"]
    asset_update_payload = payloads_by_type["asset_update_candidate"]
    assert feedback_payload.candidate_type == "feedback_candidate"
    assert feedback_payload.payload_schema_id == "polish_feedback_candidate.v1"
    assert feedback_payload.candidate_ref == first.metadata["output_refs"]["candidate_refs"][0]
    assert feedback_payload.validation_refs == tuple(first.metadata["trace_refs"]["validation_refs"])
    assert feedback_payload.trace_refs == (
        *tuple(first.metadata["trace_refs"]["checkpoint_refs"]),
        *tuple(first.metadata["trace_refs"]["validation_refs"]),
    )
    assert feedback_payload.payload["candidate_ref"] == feedback_payload.candidate_ref
    assert feedback_payload.payload["asset_update_candidate_refs"] == [asset_update_payload.candidate_ref]
    assert asset_update_payload.payload_schema_id == "polish_asset_update_candidate.v1"
    assert asset_update_payload.candidate_ref == "asset_update_candidate_ref_payment_recovery"
    assert asset_update_payload.validation_refs == feedback_payload.validation_refs
    assert asset_update_payload.trace_refs == feedback_payload.trace_refs
    assert asset_update_payload.payload == {
        "candidate_ref": "asset_update_candidate_ref_payment_recovery",
        "candidate_type": "project_asset_update_candidate",
        "asset_body_ref": "asset_body_ref_payment_recovery",
        "asset_schema_id": "project_asset.update_candidate.v1",
        "source_feedback_candidate_ref": feedback_payload.candidate_ref,
        "handoff_contract": "handoff.polish_feedback_agent.v1",
        "formal_write_blocked_until": "user_confirmation",
        "user_confirmation_required": True,
        "validation_refs": list(feedback_payload.validation_refs),
        "trace_refs": list(feedback_payload.trace_refs),
        "formal_refs": [],
        "sanitized": True,
    }

    payload = first.metadata
    assert payload["graph_name"] == "polish_feedback_graph"
    assert payload["graph_version"] == POLISH_FEEDBACK_FAKE_RUNTIME_VERSION == "pr6-fake-runtime"
    assert payload["status"] == "fake_runtime_succeeded"
    assert payload["input_refs"] == {
        "session_ref": "session_ref_1",
        "question_ref": "question_ref_1",
        "answer_ref": "answer_ref_1",
    }
    assert payload["output_refs"]["result_refs"][0].startswith("result_ref_")
    assert payload["output_refs"]["candidate_refs"][0].startswith("feedback_candidate_ref_")
    assert payload["output_refs"]["candidate_refs"][1] == "asset_update_candidate_ref_payment_recovery"
    assert payload["output_refs"]["asset_update_candidate_refs"] == [
        "asset_update_candidate_ref_payment_recovery"
    ]
    assert payload["output_refs"]["suggestion_refs"] == []
    assert payload["output_refs"]["formal_refs"] == []
    assert payload["trace_refs"]["checkpoint_refs"][0].startswith("ackpt_")
    assert payload["trace_refs"]["validation_refs"][0].startswith("validation_ref_")
    assert payload["trace_refs"]["low_confidence_refs"] == []
    assert payload["counters"] == {
        "provider_calls": 0,
        "formal_business_writes": 0,
        "db_business_writes": 0,
    }
    assert payload["rollback"] == {
        "checkpoint_refs_are_business_facts": False,
        "legacy_direct_path_retained_when_disabled": True,
    }
    assert contains_sensitive_payload(payload) is False


def test_pr6_feedback_start_timeline_preserves_p8_ref_matrix_from_command_metadata() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag())
    command = _command(
        metadata={
            "request_digest": "digest_ref_feedback_p8_timeline",
            "idempotency_key_hash": "idem_hash_ref_feedback_p8_timeline",
            "plan_refs": ("plan_ref_feedback_start",),
            "skill_refs": ("skill_ref_feedback_start",),
            "tool_refs": ("tool_ref_feedback_start",),
            "policy_refs": ("policy_ref_feedback_start",),
            "provider_refs": ("provider_ref_feedback_start",),
            "validation_refs": ("validation_ref_feedback_command",),
            "handoff_refs": ("handoff_ref_feedback_command",),
            "low_confidence_flags": ("source_gap_feedback_command",),
            "failure_reason": "validation_failed_partial_result",
            "fallback_reason": "provider_disabled",
        }
    )
    context = _context(command=command)

    started = runtime.start(context, command)
    events = {event.event_type: event for event in runtime.get_timeline(context.run_id, context.owner_id).events}
    run_started = events["run_started"]
    run_succeeded = events["run_succeeded"]
    runtime_validation_refs = tuple(started.metadata["trace_refs"]["validation_refs"])

    expected_command_refs = {
        "plan_refs": ("plan_ref_feedback_start",),
        "skill_refs": ("skill_ref_feedback_start",),
        "tool_refs": ("tool_ref_feedback_start",),
        "policy_refs": ("policy_ref_feedback_start",),
        "provider_refs": ("provider_ref_feedback_start",),
        "handoff_refs": ("handoff_ref_feedback_command",),
        "low_confidence_flags": ("source_gap_feedback_command",),
        "failure_reason": "validation_failed_partial_result",
        "fallback_reason": "provider_disabled",
    }
    for key, expected in expected_command_refs.items():
        assert run_started.metadata[key] == expected
        assert run_succeeded.metadata[key] == expected
    assert run_started.metadata["validation_refs"] == ("validation_ref_feedback_command",)
    assert run_succeeded.metadata["validation_refs"] == (
        *runtime_validation_refs,
        "validation_ref_feedback_command",
    )

    serialized = repr((started, run_started, run_succeeded))
    for forbidden in ("raw_prompt", "provider_payload", "full_asset_body", "api_key", "token"):
        assert forbidden not in serialized


def test_pr6_replay_is_read_only_and_does_not_mutate_checkpoint_or_timeline_refs() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag(), checkpointer=checkpointer)
    context = _context()
    started = runtime.start(context, context.command)
    started_status = runtime.get_status(context.run_id, context.owner_id)
    before_snapshot = checkpointer.snapshot()
    before_timeline = runtime.get_timeline(context.run_id, context.owner_id)
    validation_refs = tuple(started.metadata["trace_refs"]["validation_refs"])

    replayed = runtime.replay(context, checkpoint_ref=started.trace_refs[0])

    assert started_status.trace_refs == (*started.trace_refs, *validation_refs)
    assert replayed.read_only is True
    assert replayed.formal_write_blocked is True
    assert replayed.output_refs == ()
    assert replayed.trace_refs == started.trace_refs
    assert replayed.timeline_refs == tuple(event.event_id for event in before_timeline.events)
    assert replayed.metadata["replay_compared_trace_refs"] == (*started.trace_refs, *validation_refs)
    assert replayed.metadata["replay_trace_match"] is True
    assert checkpointer.snapshot() == before_snapshot
    assert runtime.get_timeline(context.run_id, context.owner_id) == before_timeline
    assert runtime.get_status(context.run_id, context.owner_id).metadata["counters"] == {
        "provider_calls": 0,
        "formal_business_writes": 0,
        "db_business_writes": 0,
    }


def test_pr6_replay_preserves_feedback_trace_refs_metadata() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag())
    context = _context()
    started = runtime.start(context, context.command)
    validation_refs = tuple(started.metadata["trace_refs"]["validation_refs"])
    low_confidence_refs = tuple(started.metadata["trace_refs"]["low_confidence_refs"])

    replayed = runtime.replay(context, checkpoint_ref=started.trace_refs[0])

    assert replayed.metadata["trace_refs"] == {
        "checkpoint_refs": started.trace_refs,
        "validation_refs": validation_refs,
        "low_confidence_refs": low_confidence_refs,
    }
    assert replayed.metadata["validation_refs"] == validation_refs
    assert replayed.metadata["low_confidence_flags"] == low_confidence_refs


def test_pr6_asset_conflict_opens_checkpoint_bound_hitl_interrupt_without_formal_refs() -> None:
    interrupt_service = AgentInterruptService()
    runtime = InMemoryLangGraphRuntime(
        flag_resolver=_enabled_runtime_with_graph_flag(),
        interrupt_service=interrupt_service,
    )
    command = _command(
        metadata={
            "request_digest": "digest_ref_asset_conflict",
            "idempotency_key_hash": "idem_hash_ref_asset_conflict",
            "asset_conflict_ref": "asset_conflict_ref_payment_recovery",
            "asset_update_candidate_refs": ["asset_update_candidate_ref_payment_recovery"],
        }
    )
    context = _context(command=command)

    started = runtime.start(context, command)
    status = runtime.get_status(context.run_id, context.owner_id)
    timeline = runtime.get_timeline(context.run_id, context.owner_id)
    interrupt = interrupt_service.get_interrupt(started.interrupt_refs[0], owner_id=context.owner_id)

    assert started.status == "interrupted"
    assert status.status == "interrupted"
    assert len(started.interrupt_refs) == 1
    assert status.interrupt_refs == started.interrupt_refs
    assert started.formal_refs == ()
    assert started.metadata["output_refs"]["formal_refs"] == []
    assert interrupt is not None
    assert interrupt.interrupt_type == "asset_conflict"
    assert interrupt.resume_schema_id == "agent.resume.hitl.v1"
    assert interrupt.checkpoint_ref == started.trace_refs[0]
    assert interrupt.formal_refs == ()
    assert interrupt.drawer_payload["trigger_type"] == "asset_conflict"
    assert interrupt.drawer_payload["trigger_ref"] == "asset_conflict_ref_payment_recovery"
    assert interrupt.drawer_payload["candidate_refs"] == tuple(started.metadata["output_refs"]["candidate_refs"])
    assert interrupt.drawer_payload["validation_refs"] == tuple(started.metadata["trace_refs"]["validation_refs"])
    assert interrupt.drawer_payload["formal_write_blocked"] is True
    assert contains_sensitive_payload(interrupt.drawer_payload) is False
    assert [event.event_type for event in timeline.events] == [
        "run_started",
        "checkpoint_recorded",
        "validation_recorded",
        "interrupt_opened",
    ]
    events_by_type = {event.event_type: event for event in timeline.events}
    assert events_by_type["checkpoint_recorded"].metadata["checkpoint_refs"] == started.trace_refs
    assert events_by_type["validation_recorded"].metadata["validation_refs"] == tuple(
        started.metadata["trace_refs"]["validation_refs"]
    )
    assert events_by_type["interrupt_opened"].metadata["interrupt_refs"] == started.interrupt_refs
    assert events_by_type["interrupt_opened"].metadata["candidate_refs"] == tuple(
        started.metadata["output_refs"]["candidate_refs"]
    )
    assert events_by_type["interrupt_opened"].metadata["validation_refs"] == tuple(
        started.metadata["trace_refs"]["validation_refs"]
    )


@pytest.mark.parametrize(
    ("metadata_key", "trigger_ref", "interrupt_type", "expected_low_confidence_flags"),
    (
        (
            "formal_write_attempt_ref",
            "formal_write_attempt_ref_feedback_write",
            "formal_write_attempt",
            (),
        ),
        (
            "low_confidence_formal_update_ref",
            "low_confidence_ref_feedback_update",
            "low_confidence_formal_update",
            ("low_confidence_ref_feedback_update",),
        ),
        (
            "ambiguous_ownership_ref",
            "ambiguous_ownership_ref_feedback_owner",
            "ambiguous_ownership",
            (),
        ),
        (
            "validation_failed_partial_result_ref",
            "validation_failed_partial_result_ref_feedback_partial",
            "validation_failed_partial_result",
            (),
        ),
    ),
)
def test_pr6_remaining_hitl_triggers_open_checkpoint_bound_interrupts_and_resume(
    metadata_key: str,
    trigger_ref: str,
    interrupt_type: str,
    expected_low_confidence_flags: tuple[str, ...],
) -> None:
    interrupt_service = AgentInterruptService()
    runtime = InMemoryLangGraphRuntime(
        flag_resolver=_enabled_runtime_with_graph_flag(),
        interrupt_service=interrupt_service,
    )
    command = _command(
        metadata={
            "request_digest": f"digest_ref_{interrupt_type}",
            "idempotency_key_hash": f"idem_hash_ref_{interrupt_type}",
            metadata_key: trigger_ref,
            "asset_update_candidate_refs": ["asset_update_candidate_ref_payment_recovery"],
        }
    )
    context = _context(command=command)

    started = runtime.start(context, command)
    interrupt = interrupt_service.get_interrupt(started.interrupt_refs[0], owner_id=context.owner_id)

    assert started.status == "interrupted"
    assert started.formal_refs == ()
    assert len(started.interrupt_refs) == 1
    assert started.metadata["trace_refs"]["low_confidence_refs"] == list(expected_low_confidence_flags)
    assert interrupt is not None
    assert interrupt.interrupt_type == interrupt_type
    assert interrupt.checkpoint_ref == started.trace_refs[0]
    assert interrupt.drawer_payload["trigger_type"] == interrupt_type
    assert interrupt.drawer_payload["trigger_ref"] == trigger_ref
    assert interrupt.drawer_payload["low_confidence_flags"] == expected_low_confidence_flags

    resumed = runtime.resume(
        context,
        started.interrupt_refs[0],
        {
            "action": "defer_to_handoff",
            "checkpoint_ref": interrupt.checkpoint_ref,
            "base_version": interrupt.record_version,
            "idempotency_key": f"idem_resume_{interrupt_type}",
        },
    )

    resumed_interrupt = interrupt_service.get_interrupt(started.interrupt_refs[0], owner_id=context.owner_id)
    assert resumed.status == "succeeded"
    assert resumed.formal_refs == ()
    assert resumed_interrupt is not None
    assert resumed_interrupt.status == "resumed"


def test_pr6_asset_conflict_resume_validates_checkpoint_version_and_action_at_runner_boundary() -> None:
    def started_asset_conflict_run():
        interrupt_service = AgentInterruptService()
        runtime = InMemoryLangGraphRuntime(
            flag_resolver=_enabled_runtime_with_graph_flag(),
            interrupt_service=interrupt_service,
        )
        command = _command(
            metadata={
                "request_digest": "digest_ref_asset_conflict",
                "idempotency_key_hash": "idem_hash_ref_asset_conflict",
                "asset_conflict_ref": "asset_conflict_ref_payment_recovery",
                "asset_update_candidate_refs": ["asset_update_candidate_ref_payment_recovery"],
            }
        )
        context = _context(command=command)
        started = runtime.start(context, command)
        interrupt = interrupt_service.get_interrupt(started.interrupt_refs[0], owner_id=context.owner_id)
        assert interrupt is not None
        return runtime, interrupt_service, context, started, interrupt

    runtime, _, context, started, interrupt = started_asset_conflict_run()
    with pytest.raises(RuntimeValidationError, match="checkpoint_ref"):
        runtime.resume(
            context,
            started.interrupt_refs[0],
            {
                "action": "defer_to_handoff",
                "base_version": interrupt.record_version,
                "idempotency_key": "idem_missing_checkpoint",
            },
        )

    runtime, _, context, started, interrupt = started_asset_conflict_run()
    with pytest.raises(RuntimeConflictError, match="checkpoint"):
        runtime.resume(
            context,
            started.interrupt_refs[0],
            {
                "action": "defer_to_handoff",
                "checkpoint_ref": "ackpt_wrong",
                "base_version": interrupt.record_version,
                "idempotency_key": "idem_wrong_checkpoint",
            },
        )

    runtime, _, context, started, interrupt = started_asset_conflict_run()
    with pytest.raises(RuntimeConflictError, match="stale"):
        runtime.resume(
            context,
            started.interrupt_refs[0],
            {
                "action": "defer_to_handoff",
                "checkpoint_ref": interrupt.checkpoint_ref,
                "base_version": interrupt.record_version - 1,
                "idempotency_key": "idem_stale_version",
            },
        )

    runtime, _, context, started, interrupt = started_asset_conflict_run()
    with pytest.raises(RuntimeValidationError, match="unsupported resume action"):
        runtime.resume(
            context,
            started.interrupt_refs[0],
            {
                "action": "approve",
                "checkpoint_ref": interrupt.checkpoint_ref,
                "base_version": interrupt.record_version,
                "idempotency_key": "idem_bad_action",
            },
        )

    runtime, interrupt_service, context, started, interrupt = started_asset_conflict_run()
    resumed = runtime.resume(
        context,
        started.interrupt_refs[0],
        {
            "action": "defer_to_handoff",
            "checkpoint_ref": interrupt.checkpoint_ref,
            "base_version": interrupt.record_version,
            "idempotency_key": "idem_valid_resume",
        },
    )

    resumed_interrupt = interrupt_service.get_interrupt(started.interrupt_refs[0], owner_id=context.owner_id)
    assert resumed.status == "succeeded"
    assert resumed.formal_refs == ()
    assert runtime.get_status(context.run_id, context.owner_id).interrupt_refs == ()
    assert resumed_interrupt is not None
    assert resumed_interrupt.status == "resumed"
    assert runtime.get_timeline(context.run_id, context.owner_id).events[-3].metadata == {
        "resume": {"action": "defer_to_handoff"},
        "interrupt_refs": started.interrupt_refs,
        "checkpoint_refs": started.trace_refs,
        "candidate_refs": tuple(started.metadata["output_refs"]["candidate_refs"]),
        "validation_refs": tuple(started.metadata["trace_refs"]["validation_refs"]),
    }


def test_pr6_asset_conflict_resume_timeline_retains_candidate_and_validation_refs() -> None:
    interrupt_service = AgentInterruptService()
    runtime = InMemoryLangGraphRuntime(
        flag_resolver=_enabled_runtime_with_graph_flag(),
        interrupt_service=interrupt_service,
    )
    command = _command(
        metadata={
            "request_digest": "digest_ref_asset_conflict_timeline",
            "idempotency_key_hash": "idem_hash_ref_asset_conflict_timeline",
            "asset_conflict_ref": "asset_conflict_ref_payment_timeline",
            "asset_update_candidate_refs": ["asset_update_candidate_ref_payment_timeline"],
        }
    )
    context = _context(command=command)
    started = runtime.start(context, command)
    interrupt = interrupt_service.get_interrupt(started.interrupt_refs[0], owner_id=context.owner_id)
    assert interrupt is not None

    runtime.resume(
        context,
        started.interrupt_refs[0],
        {
            "action": "defer_to_handoff",
            "checkpoint_ref": interrupt.checkpoint_ref,
            "base_version": interrupt.record_version,
            "idempotency_key": "idem_valid_resume_timeline",
        },
    )

    resume_event = runtime.get_timeline(context.run_id, context.owner_id).events[-3]

    assert resume_event.event_type == "run_resumed"
    assert resume_event.metadata["candidate_refs"] == tuple(started.metadata["output_refs"]["candidate_refs"])
    assert resume_event.metadata["validation_refs"] == tuple(started.metadata["trace_refs"]["validation_refs"])


def test_pr6_feedback_cancel_timeline_retains_candidate_and_validation_refs() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag())
    command = _command(
        metadata={
            "request_digest": "digest_ref_feedback_cancel_timeline",
            "idempotency_key_hash": "idem_hash_ref_feedback_cancel_timeline",
            "asset_update_candidate_refs": ["asset_update_candidate_ref_cancel_timeline"],
        }
    )
    context = _context(command=command)
    started = runtime.start(context, command)

    cancelled = runtime.cancel(
        context.run_id,
        context.owner_id,
        reason="user_cancelled_feedback_candidate_review",
        actor_id=context.actor_id,
    )
    cancel_event = runtime.get_timeline(context.run_id, context.owner_id).events[-1]

    assert cancelled.status == "cancelled"
    assert cancel_event.event_type == "run_cancelled"
    assert cancel_event.metadata["candidate_refs"] == tuple(started.metadata["output_refs"]["candidate_refs"])
    assert cancel_event.metadata["validation_refs"] == tuple(started.metadata["trace_refs"]["validation_refs"])
    assert cancel_event.metadata["checkpoint_refs"] == started.trace_refs
    assert cancel_event.metadata["provider_calls"] == 0
    assert cancel_event.metadata["formal_business_writes"] == 0


def test_pr6_checkpoint_refs_are_runtime_refs_and_rollback_is_flag_only() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    enabled_runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag(), checkpointer=checkpointer)
    context = _context()
    started = enabled_runtime.start(context, context.command)
    checkpoint_snapshot = checkpointer.snapshot()

    assert started.metadata["output_refs"]["formal_refs"] == []
    assert all(item["formal_business_ref"] is None for item in checkpoint_snapshot)
    assert all(item["checkpoint_ref"].startswith("ackpt_") for item in checkpoint_snapshot)
    assert all(item["checkpoint_ref"] in started.metadata["trace_refs"]["checkpoint_refs"] for item in checkpoint_snapshot)
    assert started.metadata["rollback"]["checkpoint_refs_are_business_facts"] is False

    disabled_runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_without_graph_flag(), checkpointer=checkpointer)
    with pytest.raises(GraphDisabledError):
        disabled_runtime.start(context, context.command)

    assert checkpointer.snapshot() == checkpoint_snapshot


def test_pr6_rejects_raw_text_inputs_and_exposes_no_private_runtime_markers() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag())

    with pytest.raises(RuntimeValidationError):
        runtime.start(
            _context(command=_command(input_refs=("raw session", "question_ref_1", "answer_ref_1"))),
            _command(input_refs=("raw session", "question_ref_1", "answer_ref_1")),
        )

    command_with_text_metadata = _command(metadata={QUESTION_TEXT_KEY: "hidden question", ANSWER_TEXT_KEY: "hidden answer"})
    with pytest.raises(RuntimeValidationError):
        runtime.start(_context(command=command_with_text_metadata), command_with_text_metadata)

    sensitive_command = _command(
        metadata={
            "request_digest": "digest_ref_1",
            "idempotency_key_hash": "idem_hash_ref_1",
            RAW_PROMPT_KEY: "hidden prompt",
            RAW_COMPLETION_KEY: "hidden completion",
            PROVIDER_PAYLOAD_KEY: {"token": "secret"},
            CHECKPOINT_PAYLOAD_KEY: {"state": "hidden"},
            SOURCE_BODY_KEY: "hidden source body",
        }
    )
    result = runtime.start(_context(command=sensitive_command), sensitive_command)
    public_payload = LangGraphRuntimeSerializer().serialize_run_result(result)
    public_repr = repr((public_payload, asdict(result)))
    for marker in (
        RAW_PROMPT_KEY,
        RAW_COMPLETION_KEY,
        PROVIDER_PAYLOAD_KEY,
        CHECKPOINT_PAYLOAD_KEY,
        SOURCE_BODY_KEY,
        "hidden prompt",
        "hidden completion",
        "hidden question",
        "hidden answer",
        "secret",
    ):
        assert marker not in public_repr


def _enabled_runtime_with_graph_flag() -> RuntimeFlagResolver:
    return RuntimeFlagResolver(
        test_overrides={
            "AIFI_AI_RUNTIME_ENABLED": True,
            "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True,
            POLISH_FEEDBACK_GRAPH_FLAG: True,
        }
    )


def _enabled_runtime_without_graph_flag() -> RuntimeFlagResolver:
    return RuntimeFlagResolver(
        test_overrides={
            "AIFI_AI_RUNTIME_ENABLED": True,
            "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True,
        }
    )


def _context(command: AgentCommandEnvelope | None = None) -> AgentRunContext:
    command = command or _command()
    return AgentRunContext(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_pr6_fake",
        ai_task_id="aitask_pr6_fake",
        graph_name=POLISH_FEEDBACK_GRAPH_NAME,
        graph_version=POLISH_FEEDBACK_GRAPH_VERSION,
        command=command,
    )


def _command(
    *,
    input_refs: tuple[str, ...] = ("session_ref_1", "question_ref_1", "answer_ref_1"),
    metadata: dict[str, object] | None = None,
) -> AgentCommandEnvelope:
    command_metadata: dict[str, object] = {
        "request_digest": "digest_ref_1",
        "idempotency_key_hash": "idem_hash_ref_1",
        "runtime_loop_policy": _runtime_loop_policy_metadata(),
    }
    command_metadata.update(metadata or {})
    return AgentCommandEnvelope(
        entrypoint="start",
        input_refs=input_refs,
        requested_outputs=("result_refs", "candidate_refs", "suggestion_refs"),
        idempotency_key="idem_pr6",
        metadata=command_metadata,
    )


def _runtime_loop_policy_metadata(overrides: dict[str, object] | None = None) -> dict[str, object]:
    descriptor = build_polish_feedback_graph_descriptor()
    metadata: dict[str, object] = {
        "max_steps": descriptor.runtime_max_steps,
        "max_retries": descriptor.runtime_max_retries,
        "timeout_seconds": descriptor.runtime_timeout_seconds,
        "stop_conditions": descriptor.runtime_stop_conditions,
        "allowed_tools": descriptor.runtime_allowed_tools,
        "allowed_callers": descriptor.runtime_allowed_callers,
        "side_effect_policy": descriptor.runtime_side_effect_policy,
    }
    metadata.update(overrides or {})
    return metadata
