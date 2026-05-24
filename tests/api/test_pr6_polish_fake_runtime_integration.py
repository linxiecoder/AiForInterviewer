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
    RuntimeValidationError,
    contains_sensitive_payload,
)
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.langgraph.checkpointer import RefsOnlyLangGraphCheckpointer
from app.infrastructure.ai_runtime.langgraph.fake_runtime import FakeLangGraphRuntime
from app.infrastructure.ai_runtime.langgraph.serializer import LangGraphRuntimeSerializer


RAW_PROMPT_KEY = "raw" + "_prompt"
RAW_COMPLETION_KEY = "raw" + "_completion"
PROVIDER_PAYLOAD_KEY = "provider" + "_payload"
CHECKPOINT_PAYLOAD_KEY = "checkpoint" + "_payload"
SOURCE_BODY_KEY = "full" + "_source_body"
QUESTION_TEXT_KEY = "question" + "_text"
ANSWER_TEXT_KEY = "answer" + "_text"


def test_pr6_graph_flag_default_false_blocks_fake_execution_and_retains_legacy_path() -> None:
    descriptor = build_polish_feedback_graph_descriptor()
    runtime = FakeLangGraphRuntime(flag_resolver=_enabled_runtime_without_graph_flag())
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


def test_pr6_enabled_fake_integration_returns_refs_only_sanitized_schema() -> None:
    runtime = FakeLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag())
    context = _context(
        command=AgentCommandEnvelope(
            entrypoint="start",
            input_refs=("session_ref_1", "question_ref_1", "answer_ref_1"),
            requested_outputs=("result_refs", "candidate_refs", "suggestion_refs"),
            idempotency_key="idem_pr6",
            metadata={
                "request_digest": "digest_ref_1",
                "idempotency_key_hash": "idem_hash_ref_1",
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
        first.metadata["output_refs"]["result_refs"][0],
        first.metadata["output_refs"]["candidate_refs"][0],
    )
    assert first.trace_refs == tuple(first.metadata["trace_refs"]["checkpoint_refs"])

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
    assert payload["output_refs"]["candidate_refs"][0].startswith("candidate_ref_")
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


def test_pr6_replay_is_read_only_and_does_not_mutate_checkpoint_or_timeline_refs() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    runtime = FakeLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag(), checkpointer=checkpointer)
    context = _context()
    started = runtime.start(context, context.command)
    before_snapshot = checkpointer.snapshot()
    before_timeline = runtime.get_timeline(context.run_id, context.owner_id)

    replayed = runtime.replay(context, checkpoint_ref=started.trace_refs[0])

    assert replayed.read_only is True
    assert replayed.formal_write_blocked is True
    assert replayed.output_refs == ()
    assert replayed.trace_refs == started.trace_refs
    assert replayed.timeline_refs == tuple(event.event_id for event in before_timeline.events)
    assert checkpointer.snapshot() == before_snapshot
    assert runtime.get_timeline(context.run_id, context.owner_id) == before_timeline
    assert runtime.get_status(context.run_id, context.owner_id).metadata["counters"] == {
        "provider_calls": 0,
        "formal_business_writes": 0,
        "db_business_writes": 0,
    }


def test_pr6_checkpoint_refs_are_runtime_refs_and_rollback_is_flag_only() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    enabled_runtime = FakeLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag(), checkpointer=checkpointer)
    context = _context()
    started = enabled_runtime.start(context, context.command)
    checkpoint_snapshot = checkpointer.snapshot()

    assert started.metadata["output_refs"]["formal_refs"] == []
    assert all(item["formal_business_ref"] is None for item in checkpoint_snapshot)
    assert all(item["checkpoint_ref"].startswith("ackpt_") for item in checkpoint_snapshot)
    assert all(item["checkpoint_ref"] in started.metadata["trace_refs"]["checkpoint_refs"] for item in checkpoint_snapshot)
    assert started.metadata["rollback"]["checkpoint_refs_are_business_facts"] is False

    disabled_runtime = FakeLangGraphRuntime(flag_resolver=_enabled_runtime_without_graph_flag(), checkpointer=checkpointer)
    with pytest.raises(GraphDisabledError):
        disabled_runtime.start(context, context.command)

    assert checkpointer.snapshot() == checkpoint_snapshot


def test_pr6_rejects_raw_text_inputs_and_exposes_no_private_runtime_markers() -> None:
    runtime = FakeLangGraphRuntime(flag_resolver=_enabled_runtime_with_graph_flag())

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
    return AgentCommandEnvelope(
        entrypoint="start",
        input_refs=input_refs,
        requested_outputs=("result_refs", "candidate_refs", "suggestion_refs"),
        idempotency_key="idem_pr6",
        metadata=metadata or {"request_digest": "digest_ref_1", "idempotency_key_hash": "idem_hash_ref_1"},
    )
