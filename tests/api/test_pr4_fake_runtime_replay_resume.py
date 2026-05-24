from __future__ import annotations

import pytest

from app.application.ai_runtime.contracts import AgentCommandEnvelope, AgentRunContext, GraphDisabledError, RuntimePolicyError
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.langgraph.checkpointer import RefsOnlyLangGraphCheckpointer
from app.infrastructure.ai_runtime.langgraph.fake_runtime import FakeLangGraphRuntime


RAW_KEY = "raw" + "_prompt"
PROVIDER_KEY = "provider_" + "payload"


def test_pr4_fake_runtime_fails_closed_when_runtime_flags_default_false() -> None:
    runtime = FakeLangGraphRuntime()
    context = _context()

    with pytest.raises(GraphDisabledError):
        runtime.start(context, context.command)


def test_pr4_fake_runtime_start_resume_and_timeline_are_sanitized() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    runtime = FakeLangGraphRuntime(flag_resolver=_enabled_flags(), checkpointer=checkpointer)
    context = _context()

    started = runtime.start(context, context.command)
    resumed = runtime.resume(
        context,
        interrupt_ref=started.interrupt_refs[0],
        resume_payload={RAW_KEY: "hidden prompt", PROVIDER_KEY: {"secret": "hidden"}, "decision": "approved"},
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
    serialized = repr((started, resumed, status, timeline, checkpointer.snapshot()))
    for forbidden in ("hidden prompt", "provider_payload", "secret", "checkpoint_payload", "formal_question"):
        assert forbidden not in serialized


def test_pr4_fake_runtime_replay_is_read_only_and_does_not_mutate_checkpoints() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    runtime = FakeLangGraphRuntime(flag_resolver=_enabled_flags(), checkpointer=checkpointer)
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


def test_pr4_fake_runtime_resume_does_not_bypass_runtime_gate() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    enabled_runtime = FakeLangGraphRuntime(flag_resolver=_enabled_flags(), checkpointer=checkpointer)
    context = _context()
    started = enabled_runtime.start(context, context.command)
    disabled_runtime = FakeLangGraphRuntime(
        flag_resolver=RuntimeFlagResolver(
            test_overrides={"AIFI_AI_RUNTIME_ENABLED": False, "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True}
        ),
        checkpointer=checkpointer,
    )

    with pytest.raises(GraphDisabledError):
        disabled_runtime.resume(context, interrupt_ref=started.interrupt_refs[0], resume_payload={"decision": "approved"})


def test_pr4_fake_runtime_start_rejects_command_mismatch() -> None:
    runtime = FakeLangGraphRuntime(flag_resolver=_enabled_flags())
    context = _context()
    mismatched_command = AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("different_runtime_input_ref",),
        requested_outputs=("candidate_refs",),
        idempotency_key="different_idem_pr4",
    )

    with pytest.raises(RuntimePolicyError, match="command must match context command"):
        runtime.start(context, mismatched_command)


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
        metadata={RAW_KEY: "must not escape"},
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
