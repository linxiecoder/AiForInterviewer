"""Sanitized AI Runtime trace bridge contract."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable

from app.application.ai_runtime.contracts import (
    RuntimePolicyError,
    RuntimeUnavailableError,
    contains_sensitive_payload,
    sanitize_payload,
    validate_agent_runtime_status,
)
from app.application.ai_runtime.side_effect_guard import sanitize_checkpoint_metadata


@dataclass(frozen=True)
class AgentTraceRecord:
    trace_ref_id: str
    event_type: str
    owner_id: str
    run_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentTraceBridge:
    def __init__(self, writer: Callable[[AgentTraceRecord], None] | None = None) -> None:
        self._writer = writer
        self.records: list[AgentTraceRecord] = []

    def record_run_started(self, *, owner_id: str, run_id: str, ai_task_id: str, graph_name: str) -> AgentTraceRecord:
        return self._record(owner_id, run_id, "run_started", {"ai_task_id": ai_task_id, "graph_name": graph_name})

    def record_node_started(self, *, owner_id: str, run_id: str, node_name: str, input_refs: tuple[str, ...]) -> AgentTraceRecord:
        return self._record(owner_id, run_id, "node_started", {"node_name": node_name, "input_refs": input_refs})

    def record_node_finished(
        self, *, owner_id: str, run_id: str, node_name: str, status: str, output_refs: tuple[str, ...]
    ) -> AgentTraceRecord:
        validate_agent_runtime_status(status)
        return self._record(
            owner_id,
            run_id,
            "node_finished",
            {"node_name": node_name, "status": status, "output_refs": output_refs},
        )

    def record_llm_call(self, *, owner_id: str, run_id: str, llm_call_id: str, summary: dict[str, Any]) -> AgentTraceRecord:
        if contains_sensitive_payload(summary):
            raise RuntimePolicyError("sensitive LLM summary blocked")
        return self._record(owner_id, run_id, "llm_call", {"llm_call_id": llm_call_id, "summary": summary})

    def record_interrupt(
        self, *, owner_id: str, run_id: str, interrupt_id: str, schema_id: str, candidate_refs: tuple[str, ...]
    ) -> AgentTraceRecord:
        return self._record(
            owner_id,
            run_id,
            "interrupt",
            {"interrupt_id": interrupt_id, "schema_id": schema_id, "candidate_refs": candidate_refs},
        )

    def record_checkpoint_ref(
        self, *, owner_id: str, run_id: str, checkpoint_ref: str, metadata: dict[str, Any]
    ) -> AgentTraceRecord:
        checkpoint_metadata = sanitize_checkpoint_metadata({"checkpoint_id": checkpoint_ref, **metadata})
        return self._record(owner_id, run_id, "checkpoint_ref", checkpoint_metadata)

    def record_run_finished(
        self, *, owner_id: str, run_id: str, status: str, result_refs: tuple[str, ...]
    ) -> AgentTraceRecord:
        validate_agent_runtime_status(status)
        return self._record(owner_id, run_id, "run_finished", {"status": status, "result_refs": result_refs})

    def _record(self, owner_id: str, run_id: str, event_type: str, metadata: dict[str, Any]) -> AgentTraceRecord:
        if contains_sensitive_payload(metadata):
            raise RuntimePolicyError("sensitive trace metadata blocked")
        record = AgentTraceRecord(
            trace_ref_id="atrace_" + _stable_id(owner_id, run_id, event_type, repr(sorted(metadata.items()))),
            event_type=event_type,
            owner_id=owner_id,
            run_id=run_id,
            metadata=sanitize_payload(metadata),
        )
        try:
            if self._writer:
                self._writer(record)
        except Exception as exc:  # pragma: no cover - defensive bridge contract
            raise RuntimeUnavailableError("trace write failed before formal write") from exc
        self.records.append(record)
        return record


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:16]
