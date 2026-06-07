from __future__ import annotations

import ast
import inspect
from pathlib import Path

from pydantic import BaseModel

import app.application.llm.agent_contracts as typed_agent_contracts
from app.application.llm import agent_io
from app.application.llm.agent_contracts import (
    AgentContract,
    AgentOutputEnvelope,
    TypedAgentFinalEnvelope,
    TypedAgentInputEnvelope,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class _InputPayload(BaseModel):
    answer_id: str


class _CandidatePayload(BaseModel):
    feedback_text: str


class _FinalPayload(BaseModel):
    status: str
    feedback_text: str


class _OtherCandidatePayload(BaseModel):
    question_text: str


def test_agent_contract_envelope_names_are_canonical() -> None:
    assert typed_agent_contracts.AgentOutputEnvelope is AgentOutputEnvelope
    assert hasattr(typed_agent_contracts, "AgentOutputEnvelope")
    assert hasattr(agent_io, "LegacyAgentOutputEnvelope")
    assert not hasattr(agent_io, "AgentOutputEnvelope")
    assert "Legacy dict-based Agent output envelope used by pre-schema-first agents" in (
        inspect.getdoc(agent_io.LegacyAgentOutputEnvelope) or ""
    )


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
    envelope = AgentOutputEnvelope[_CandidatePayload](
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


def test_agent_output_envelope_has_single_class_definition_and_no_legacy_import_alias() -> None:
    agent_output_class_defs: list[Path] = []
    forbidden_imports: list[Path] = []
    for root in (REPO_ROOT / "apps", REPO_ROOT / "tests"):
        for path in root.rglob("*.py"):
            source = path.read_text(encoding="utf-8-sig")
            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "AgentOutputEnvelope":
                    agent_output_class_defs.append(path.relative_to(REPO_ROOT))
                if isinstance(node, ast.ImportFrom) and node.module == "app.application.llm.agent_io":
                    if any(alias.name == "AgentOutputEnvelope" for alias in node.names):
                        forbidden_imports.append(path.relative_to(REPO_ROOT))

    assert agent_output_class_defs == [Path("apps/api/app/application/llm/agent_contracts.py")]
    assert forbidden_imports == []


def test_generic_envelopes_accept_different_payload_types() -> None:
    input_envelope = TypedAgentInputEnvelope[_InputPayload](
        agent_name="feedback",
        task_type="polish_feedback_generation",
        schema_id="feedback_input",
        schema_version="1.0",
        prompt_version="prompt.v1",
        payload=_InputPayload(answer_id="answer_001"),
    )
    output_envelope = AgentOutputEnvelope[_OtherCandidatePayload](
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
