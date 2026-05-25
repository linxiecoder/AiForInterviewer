from __future__ import annotations

from dataclasses import asdict

from app.application.ai_runtime.business_graphs.polish_question_graph import (
    POLISH_QUESTION_GRAPH_FLAG,
    POLISH_QUESTION_GRAPH_NAME,
    POLISH_QUESTION_GRAPH_VERSION,
)
from app.application.ai_runtime.contracts import (
    AgentCommandEnvelope,
    AgentRunContext,
    contains_sensitive_payload,
)
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.langgraph.fake_runtime import FakeLangGraphRuntime


RAW_PROMPT_KEY = "raw" + "_prompt"
RAW_COMPLETION_KEY = "raw" + "_completion"
PROVIDER_PAYLOAD_KEY = "provider" + "_payload"
CHECKPOINT_PAYLOAD_KEY = "checkpoint" + "_payload"
FULL_RESUME_KEY = "full" + "_resume"
FULL_JD_KEY = "full" + "_jd"
FULL_ANSWER_KEY = "full" + "_answer"
HIDDEN_RUBRIC_KEY = "hidden" + "_rubric"
API_KEY = "api" + "_key"
FORBIDDEN_MARKERS = (
    RAW_PROMPT_KEY,
    RAW_COMPLETION_KEY,
    PROVIDER_PAYLOAD_KEY,
    CHECKPOINT_PAYLOAD_KEY,
    FULL_RESUME_KEY,
    FULL_JD_KEY,
    FULL_ANSWER_KEY,
    HIDDEN_RUBRIC_KEY,
    "token",
    "secret",
    "cookie",
    API_KEY,
)


def test_fake_runtime_polish_question_emits_agent_candidate_payload() -> None:
    runtime = FakeLangGraphRuntime(flag_resolver=_enabled_runtime_with_question_graph_flag())
    context = _context()

    result = runtime.start(context, context.command)

    assert result.status == "fake_runtime_succeeded"
    assert len(result.candidate_payloads) == 1
    candidate_payload = result.candidate_payloads[0]
    assert candidate_payload.candidate_type == "polish_question_candidate"
    assert candidate_payload.payload_schema_id == "polish_question_candidate.v1"
    assert candidate_payload.status == "accepted"
    assert candidate_payload.candidate_ref in result.output_refs
    assert candidate_payload.payload["candidate_ref"] == candidate_payload.candidate_ref
    assert candidate_payload.validation_refs
    assert result.formal_refs == ()
    assert result.metadata["provider_calls"] == 0
    assert result.metadata["db_business_writes"] == 0
    assert result.metadata["formal_business_writes"] == 0
    assert result.metadata["accepted_candidate_payload"] is True


def test_fake_runtime_polish_question_candidate_payload_is_sanitized() -> None:
    runtime = FakeLangGraphRuntime(flag_resolver=_enabled_runtime_with_question_graph_flag())
    command = _command(
        metadata={
            "request_digest": "digest_ref_1",
            "idempotency_key_hash": "idem_hash_ref_1",
            "context_digest": "ctx_ref_1",
            RAW_PROMPT_KEY: "hidden prompt",
            RAW_COMPLETION_KEY: "hidden completion",
            PROVIDER_PAYLOAD_KEY: {"token": "secret"},
            CHECKPOINT_PAYLOAD_KEY: {"state": "hidden"},
            FULL_RESUME_KEY: "hidden resume",
            FULL_JD_KEY: "hidden jd",
            FULL_ANSWER_KEY: "hidden answer",
            HIDDEN_RUBRIC_KEY: "hidden rubric",
            "cookie": "hidden cookie",
            API_KEY: "hidden api key",
        }
    )
    context = _context(command=command)

    result = runtime.start(context, command)
    payload = result.candidate_payloads[0].payload

    assert contains_sensitive_payload(payload) is False
    serialized = repr(asdict(result.candidate_payloads[0]))
    for marker in FORBIDDEN_MARKERS:
        assert marker not in serialized


def test_fake_runtime_polish_question_timeline_is_sanitized() -> None:
    runtime = FakeLangGraphRuntime(flag_resolver=_enabled_runtime_with_question_graph_flag())
    context = _context()

    runtime.start(context, context.command)
    timeline = runtime.get_timeline(context.run_id, context.owner_id)

    assert [event.event_type for event in timeline.events] == [
        "run_started",
        "checkpoint_recorded",
        "validation_recorded",
        "candidate_payload_emitted",
        "run_succeeded",
    ]
    serialized = repr(asdict(timeline))
    assert "question_text" not in serialized
    for marker in FORBIDDEN_MARKERS:
        assert marker not in serialized


def test_fake_runtime_polish_question_status_has_refs_only() -> None:
    runtime = FakeLangGraphRuntime(flag_resolver=_enabled_runtime_with_question_graph_flag())
    context = _context()

    result = runtime.start(context, context.command)
    status = runtime.get_status(context.run_id, context.owner_id)

    assert status.status == "fake_runtime_succeeded"
    assert status.output_refs == result.output_refs
    assert result.candidate_payloads[0].candidate_ref in status.output_refs
    assert status.trace_refs == result.trace_refs
    assert any(ref.startswith("ackpt_") for ref in status.trace_refs)
    assert any(ref.startswith("validation_ref_") for ref in status.trace_refs)
    assert status.formal_write_blocked is True
    assert status.metadata["sanitized"] is True
    assert status.metadata["accepted_candidate_payload"] is True
    assert "candidate" not in status.metadata
    assert "payload" not in status.metadata


def _enabled_runtime_with_question_graph_flag() -> RuntimeFlagResolver:
    return RuntimeFlagResolver(
        test_overrides={
            "AIFI_AI_RUNTIME_ENABLED": True,
            "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True,
            POLISH_QUESTION_GRAPH_FLAG: True,
        }
    )


def _context(command: AgentCommandEnvelope | None = None) -> AgentRunContext:
    command = command or _command()
    return AgentRunContext(
        owner_id="owner_pr5_c2",
        actor_id="owner_pr5_c2",
        run_id="arun_pr5_c2_fake_question",
        ai_task_id="aitask_pr5_c2_fake_question",
        graph_name=POLISH_QUESTION_GRAPH_NAME,
        graph_version=POLISH_QUESTION_GRAPH_VERSION,
        command=command,
    )


def _command(*, metadata: dict[str, object] | None = None) -> AgentCommandEnvelope:
    return AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("session_ref_1", "progress_node_payment_consistency", "completed_focus_ref_1"),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_pr5_c2_fake_question",
        metadata=metadata
        or {
            "request_digest": "digest_ref_1",
            "idempotency_key_hash": "idem_hash_ref_1",
            "context_digest": "ctx_ref_1",
        },
    )
