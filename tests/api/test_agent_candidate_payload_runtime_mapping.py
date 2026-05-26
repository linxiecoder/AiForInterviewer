from __future__ import annotations

from dataclasses import asdict

import pytest

from app.application.ai_runtime.business_graphs.polish_question_graph import (
    POLISH_QUESTION_GRAPH_FLAG,
    POLISH_QUESTION_GRAPH_NAME,
    POLISH_QUESTION_GRAPH_VERSION,
)
from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentCommandEnvelope,
    AgentRunContext,
    RuntimePolicyError,
    RuntimeValidationError,
)
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.langgraph import polish_question_runtime as polish_question_runtime_module
from app.infrastructure.ai_runtime.langgraph.in_memory_runtime import InMemoryLangGraphRuntime
from app.infrastructure.ai_runtime.langgraph.serializer import (
    build_agent_candidate_payload_from_runtime_output,
)


RAW_PROMPT_KEY = "raw" + "_prompt"
CHECKPOINT_PAYLOAD_KEY = "checkpoint" + "_payload"


def test_runtime_candidate_output_maps_to_agent_candidate_payload() -> None:
    payload = build_agent_candidate_payload_from_runtime_output(_runtime_candidate_output())

    assert isinstance(payload, AgentCandidatePayload)
    assert payload.candidate_ref == "question_candidate_ref_mapping"
    assert payload.candidate_type == "polish_question_candidate"
    assert payload.payload_schema_id == "polish_question_candidate.v1"
    assert payload.status == "accepted"
    assert payload.payload["candidate_ref"] == payload.candidate_ref
    assert payload.trace_refs == ("ackpt_runtime_mapping", "validation_ref_mapping")
    assert payload.validation_refs == ("validation_ref_mapping",)


def test_runtime_candidate_output_rejects_raw_payload() -> None:
    output = _runtime_candidate_output(
        payload={
            "candidate_ref": "question_candidate_ref_mapping",
            RAW_PROMPT_KEY: "hidden prompt",
            "question_text": "请说明你如何推进一次跨团队问题定位。",
        }
    )

    with pytest.raises(RuntimePolicyError, match="sensitive"):
        build_agent_candidate_payload_from_runtime_output(output)


def test_runtime_candidate_output_rejects_checkpoint_payload() -> None:
    output = _runtime_candidate_output(**{CHECKPOINT_PAYLOAD_KEY: {"state": "hidden"}})

    with pytest.raises(RuntimePolicyError, match="checkpoint payload"):
        build_agent_candidate_payload_from_runtime_output(output)


def test_runtime_candidate_output_requires_schema_and_candidate_ref() -> None:
    output = _runtime_candidate_output()
    output.pop("candidate_ref")

    with pytest.raises(RuntimeValidationError, match="candidate_ref"):
        build_agent_candidate_payload_from_runtime_output(output)

    output = _runtime_candidate_output(payload_schema_id="")

    with pytest.raises(RuntimeValidationError, match="payload_schema_id"):
        build_agent_candidate_payload_from_runtime_output(output)


def test_in_memory_runtime_uses_runtime_candidate_payload_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []
    real_builder = polish_question_runtime_module.build_agent_candidate_payload_from_runtime_output

    def recording_builder(output: dict[str, object]) -> AgentCandidatePayload:
        calls.append(output)
        return real_builder(output)

    monkeypatch.setattr(
        polish_question_runtime_module,
        "build_agent_candidate_payload_from_runtime_output",
        recording_builder,
    )
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_question_graph_flag())
    context = _context()

    result = runtime.start(context, context.command)

    assert len(calls) == 1
    assert calls[0]["candidate_ref"] == result.candidate_payloads[0].candidate_ref
    serialized = repr(asdict(result.candidate_payloads[0]))
    assert RAW_PROMPT_KEY not in serialized
    assert CHECKPOINT_PAYLOAD_KEY not in serialized


def _runtime_candidate_output(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "candidate_ref": "question_candidate_ref_mapping",
        "candidate_type": "polish_question_candidate",
        "payload_schema_id": "polish_question_candidate.v1",
        "status": "accepted",
        "payload": {
            "candidate_ref": "question_candidate_ref_mapping",
            "question_text": "请说明你如何推进一次跨团队问题定位。",
            "quality_gate": {"passed": True, "status": "accepted"},
            "sanitized": True,
        },
        "trace_refs": ("ackpt_runtime_mapping", "validation_ref_mapping"),
        "validation_refs": ("validation_ref_mapping",),
        "low_confidence_flags": (),
    }
    values.update(overrides)
    return values


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
        owner_id="owner_pr5_c3",
        actor_id="owner_pr5_c3",
        run_id="arun_pr5_c3_fake_question",
        ai_task_id="aitask_pr5_c3_fake_question",
        graph_name=POLISH_QUESTION_GRAPH_NAME,
        graph_version=POLISH_QUESTION_GRAPH_VERSION,
        command=command,
    )


def _command() -> AgentCommandEnvelope:
    return AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("session_ref_1", "progress_node_payment_consistency"),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_pr5_c3_fake_question",
        metadata={
            "request_digest": "digest_ref_1",
            "idempotency_key_hash": "idem_hash_ref_1",
            "context_digest": "ctx_ref_1",
        },
    )
