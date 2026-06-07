from __future__ import annotations

import inspect

from pydantic import BaseModel

import app.application.llm.agent_contracts as typed_agent_contracts
from app.application.llm import agent_io
from app.application.llm.agent_contracts import (
    AgentContract,
    TypedAgentCandidateEnvelope,
    TypedAgentFinalEnvelope,
    TypedAgentInputEnvelope,
)


class _InputPayload(BaseModel):
    answer_id: str


class _CandidatePayload(BaseModel):
    feedback_text: str


class _FinalPayload(BaseModel):
    status: str
    feedback_text: str


class _OtherCandidatePayload(BaseModel):
    question_text: str


def test_agent_contract_envelope_names_do_not_collide_with_legacy_agent_io() -> None:
    assert not hasattr(typed_agent_contracts, "AgentOutputEnvelope")
    assert hasattr(typed_agent_contracts, "TypedAgentCandidateEnvelope")
    assert hasattr(agent_io, "AgentOutputEnvelope")
    assert "Legacy dict-based Agent output envelope" in (inspect.getdoc(agent_io.AgentOutputEnvelope) or "")


def test_agent_contract_generates_candidate_and_final_json_schema() -> None:
    contract = AgentContract[_InputPayload, _CandidatePayload, _FinalPayload](
        agent_name="feedback",
        task_type="polish_feedback_generation",
        schema_id="feedback_candidate",
        schema_version="1.0",
        prompt_version="prompt.v1",
        candidate_payload_model=_CandidatePayload,
        final_payload_model=_FinalPayload,
    )

    candidate_schema = contract.candidate_json_schema()
    final_schema = contract.final_json_schema()

    assert candidate_schema["properties"]["feedback_text"]["type"] == "string"
    assert "feedback_text" in candidate_schema["required"]
    assert final_schema["properties"]["status"]["type"] == "string"
    assert "status" in final_schema["required"]


def test_agent_output_envelope_keeps_metadata_out_of_payload() -> None:
    envelope = TypedAgentCandidateEnvelope[_CandidatePayload](
        agent_name="feedback",
        task_type="polish_feedback_generation",
        schema_id="feedback_candidate",
        schema_version="1.0",
        prompt_version="prompt.v1",
        metadata={
            "model_name": "deepseek-chat",
            "provider_status": "called",
            "request_id": "req_001",
        },
        payload=_CandidatePayload(feedback_text="可以展示的反馈"),
    )

    dumped = envelope.model_dump(mode="json")

    assert dumped["payload"] == {"feedback_text": "可以展示的反馈"}
    assert dumped["metadata"]["model_name"] == "deepseek-chat"
    assert "model_name" not in dumped["payload"]
    assert "provider_status" not in dumped["payload"]
    assert "request_id" not in dumped["payload"]


def test_generic_envelopes_accept_different_payload_types() -> None:
    input_envelope = TypedAgentInputEnvelope[_InputPayload](
        agent_name="feedback",
        task_type="polish_feedback_generation",
        schema_id="feedback_input",
        schema_version="1.0",
        prompt_version="prompt.v1",
        payload=_InputPayload(answer_id="answer_001"),
    )
    output_envelope = TypedAgentCandidateEnvelope[_OtherCandidatePayload](
        agent_name="question",
        task_type="polish_question_generation",
        schema_id="question_candidate",
        schema_version="1.0",
        prompt_version="prompt.v1",
        payload=_OtherCandidatePayload(question_text="请说明幂等设计。"),
    )
    final_envelope = TypedAgentFinalEnvelope[_FinalPayload](
        agent_name="feedback",
        task_type="polish_feedback_generation",
        schema_id="feedback_final",
        schema_version="1.0",
        prompt_version="prompt.v1",
        payload=_FinalPayload(status="generated", feedback_text="反馈文本"),
    )

    assert input_envelope.payload.answer_id == "answer_001"
    assert output_envelope.payload.question_text == "请说明幂等设计。"
    assert final_envelope.payload.status == "generated"
