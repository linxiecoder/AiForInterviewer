"""Generic Pydantic contracts for LLM-backed agents."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


InputPayloadT = TypeVar("InputPayloadT", bound=BaseModel)
CandidatePayloadT = TypeVar("CandidatePayloadT", bound=BaseModel)
FinalPayloadT = TypeVar("FinalPayloadT", bound=BaseModel)


class _AgentEnvelopeBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_name: str
    task_type: str
    schema_id: str
    schema_version: str
    prompt_version: str | None = None
    contract_ids: tuple[str, ...] = Field(default_factory=tuple)
    input_refs: tuple[str, ...] = Field(default_factory=tuple)
    trace_refs: tuple[str, ...] = Field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    low_confidence_flags: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TypedAgentInputEnvelope(_AgentEnvelopeBase, Generic[InputPayloadT]):
    payload: InputPayloadT


class TypedAgentCandidateEnvelope(_AgentEnvelopeBase, Generic[CandidatePayloadT]):
    payload: CandidatePayloadT


class TypedAgentFinalEnvelope(_AgentEnvelopeBase, Generic[FinalPayloadT]):
    payload: FinalPayloadT


class AgentContract(BaseModel, Generic[InputPayloadT, CandidatePayloadT, FinalPayloadT]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_name: str
    task_type: str
    schema_id: str
    schema_version: str
    prompt_version: str | None = None
    contract_ids: tuple[str, ...] = Field(default_factory=tuple)
    input_payload_model: type[InputPayloadT] | None = None
    candidate_payload_model: type[CandidatePayloadT]
    final_payload_model: type[FinalPayloadT]

    def candidate_json_schema(self) -> dict[str, Any]:
        return self.candidate_payload_model.model_json_schema()

    def final_json_schema(self) -> dict[str, Any]:
        return self.final_payload_model.model_json_schema()
