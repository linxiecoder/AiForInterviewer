from __future__ import annotations

from dataclasses import asdict

import pytest

from app.application.ai_runtime.contracts import (
    AgentCommandEnvelope,
    AgentRunContext,
    GraphDisabledError,
    contains_sensitive_payload,
)
from app.application.ai_runtime.registry import AgentGraphRegistry
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.langgraph.serializer import LangGraphRuntimeSerializer


def test_pr5_registers_default_off_polish_business_graph_descriptors() -> None:
    from app.application.ai_runtime.business_graphs.polish_feedback_graph import (
        POLISH_FEEDBACK_GRAPH_FLAG,
        POLISH_FEEDBACK_GRAPH_NAME,
        POLISH_FEEDBACK_GRAPH_VERSION,
        build_polish_feedback_graph_descriptor,
        run_polish_feedback_skeleton,
    )
    from app.application.ai_runtime.business_graphs.polish_question_graph import (
        POLISH_QUESTION_GRAPH_FLAG,
        POLISH_QUESTION_GRAPH_NAME,
        POLISH_QUESTION_GRAPH_VERSION,
        build_polish_question_graph_descriptor,
    )

    registry = AgentGraphRegistry.default()
    pr5_descriptors = {
        descriptor.graph_name: descriptor
        for descriptor in registry.list_graph_descriptors()
        if descriptor.implementation_pr == "PR5"
    }

    assert pr5_descriptors == {
        POLISH_FEEDBACK_GRAPH_NAME: build_polish_feedback_graph_descriptor(),
    }

    feedback_descriptor = pr5_descriptors[POLISH_FEEDBACK_GRAPH_NAME]
    assert feedback_descriptor.graph_name == POLISH_FEEDBACK_GRAPH_NAME == "polish_feedback_graph"
    assert feedback_descriptor.graph_version == POLISH_FEEDBACK_GRAPH_VERSION == "pr5-skeleton"
    assert (
        feedback_descriptor.runtime_flag_key
        == POLISH_FEEDBACK_GRAPH_FLAG
        == "AIFI_GRAPH_POLISH_FEEDBACK_ENABLED"
    )
    _assert_pr5_descriptor_is_default_off_refs_only(feedback_descriptor)
    assert feedback_descriptor.lifecycle_status == "placeholder"
    assert feedback_descriptor.migration_status == "skeleton_default_off_direct_path_retained"
    assert feedback_descriptor.runtime_side_effect_policy == "candidate_write"
    assert "formal_write_requested" in feedback_descriptor.runtime_stop_conditions
    assert feedback_descriptor.disabled_behavior == "legacy_direct_path_retained"

    question_descriptor = registry.get_graph_descriptor(POLISH_QUESTION_GRAPH_NAME)
    assert question_descriptor.graph_name == POLISH_QUESTION_GRAPH_NAME == "polish_question_graph"
    assert question_descriptor.graph_version == POLISH_QUESTION_GRAPH_VERSION == "pr9-agent-orchestration"
    assert (
        question_descriptor.runtime_flag_key
        == POLISH_QUESTION_GRAPH_FLAG
        == "AIFI_GRAPH_POLISH_QUESTION_ENABLED"
    )
    assert question_descriptor == build_polish_question_graph_descriptor()
    _assert_pr5_descriptor_is_default_off_refs_only(question_descriptor)
    assert question_descriptor.lifecycle_status == "active"
    assert question_descriptor.migration_status == "agent_orchestration_with_deterministic_fallback"
    assert question_descriptor.runtime_side_effect_policy == "candidate_write"
    assert "formal_write_requested" in question_descriptor.runtime_stop_conditions
    assert question_descriptor.disabled_behavior == "deterministic_fallback_with_reason"

    flag_decision = RuntimeFlagResolver().resolve_graph_flag(
        feedback_descriptor,
        actor_id="actor_1",
        caller="registry",
    )
    assert flag_decision.enabled is False
    assert flag_decision.source == "hardcoded_default"

    with pytest.raises(GraphDisabledError):
        run_polish_feedback_skeleton(context=_context(), command=_context().command)


def test_pr5_polish_feedback_skeleton_is_deterministic_refs_only_and_sanitized() -> None:
    from app.application.ai_runtime.business_graphs.polish_feedback_graph import (
        POLISH_FEEDBACK_GRAPH_FLAG,
        run_polish_feedback_skeleton,
    )

    resolver = RuntimeFlagResolver(test_overrides={POLISH_FEEDBACK_GRAPH_FLAG: True})
    context = _context(
        command=AgentCommandEnvelope(
            entrypoint="start",
            input_refs=("session_ref_1", "question_ref_1", "answer_ref_1"),
            requested_outputs=("result_refs", "candidate_refs", "suggestion_refs"),
            idempotency_key="idem_pr5",
            metadata={
                "safe_context_ref": "ctx_ref_1",
                "raw_prompt": "hidden",
                "provider_payload": {"secret": "sk-demo"},
                "checkpoint_payload": {"state": "hidden"},
            },
        )
    )

    first = run_polish_feedback_skeleton(context=context, command=context.command, flag_resolver=resolver)
    second = run_polish_feedback_skeleton(context=context, command=context.command, flag_resolver=resolver)

    assert first == second
    assert len(first.output_refs) == 3
    assert first.output_refs[0].startswith("result_ref_")
    assert first.output_refs[1].startswith("candidate_ref_")
    assert first.output_refs[2].startswith("suggestion_ref_")
    assert len(first.trace_refs) == 1
    assert first.trace_refs[0].startswith("ackpt_")
    assert first.interrupt_refs == ()
    assert first.formal_refs == ()
    assert first.metadata["provider_calls"] == 0
    assert first.metadata["formal_business_writes"] == 0
    assert first.metadata["db_business_writes"] == 0
    assert first.metadata["checkpoint_refs_only"] is True
    assert first.metadata["checkpoint_refs_are_business_facts"] is False
    assert first.metadata["sanitized"] is True

    serialized = LangGraphRuntimeSerializer().serialize_run_result(first)
    assert contains_sensitive_payload(serialized) is False
    assert "raw_prompt" not in repr(serialized)
    assert "provider_payload" not in repr(serialized)
    assert "checkpoint_payload" not in repr(serialized)
    assert "sk-demo" not in repr(serialized)


def test_pr5_polish_feedback_replay_is_read_only_and_has_no_writes_to_undo() -> None:
    from app.application.ai_runtime.business_graphs.polish_feedback_graph import replay_polish_feedback_skeleton

    replay = replay_polish_feedback_skeleton(context=_context(), checkpoint_ref="ackpt_2e136a52112155ae")

    assert replay.read_only is True
    assert replay.formal_write_blocked is True
    assert replay.output_refs == ()
    assert replay.trace_refs == ("ackpt_2e136a52112155ae",)
    assert replay.timeline_refs == ()
    assert asdict(replay)["formal_write_blocked"] is True


def _context(command: AgentCommandEnvelope | None = None) -> AgentRunContext:
    command = command or AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("session_ref_1", "question_ref_1", "answer_ref_1"),
        requested_outputs=("result_refs",),
        idempotency_key="idem_pr5",
    )
    return AgentRunContext(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_pr5",
        ai_task_id="aitask_pr5",
        graph_name="polish_feedback_graph",
        graph_version="pr5-skeleton",
        command=command,
    )


def _assert_pr5_descriptor_is_default_off_refs_only(descriptor: object) -> None:
    assert descriptor.default_enabled is False
    assert descriptor.provider_enabled is False
    assert descriptor.formal_write_targets == ()
    assert descriptor.db_business_write_targets == ()
    assert descriptor.rollback_safe is True
