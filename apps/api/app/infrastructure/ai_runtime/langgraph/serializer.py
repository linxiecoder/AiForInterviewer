"""Sanitized serializer boundary for PR4 LangGraph runtime infrastructure."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from collections.abc import Iterable, Mapping
from typing import Any

from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentRunResult,
    AgentRunStatus,
    AgentRunTimelinePage,
    RuntimePolicyError,
    RuntimeValidationError,
    contains_sensitive_payload,
    is_sensitive_key,
    sanitize_payload,
)


_INTERNAL_METADATA_KEYS = frozenset(
    {
        "checkpoint_id",
        "checkpoint_namespace",
        "thread_id",
        "state_hash",
        "checkpoint_payload",
        "compiled_graph",
        "agent_state",
        "__pregel_internal",
        "_internal_graph_state",
    }
)


class LangGraphRuntimeSerializer:
    """Converts runtime objects to public, sanitized payloads only."""

    def serialize_graph_state(self, raw_state: Any) -> dict[str, Any]:
        raise RuntimePolicyError("raw internal graph state cannot cross the PR4 serializer boundary")

    def serialize_run_result(self, result: AgentRunResult) -> dict[str, Any]:
        return _strip_private_runtime_metadata(asdict(result))

    def serialize_run_status(self, status: AgentRunStatus) -> dict[str, Any]:
        return _strip_private_runtime_metadata(asdict(status))

    def serialize_timeline_page(self, page: AgentRunTimelinePage) -> dict[str, Any]:
        return {
            "run_id": page.run_id,
            "events": tuple(
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "summary": event.summary,
                    "refs": event.refs,
                    "metadata": _public_metadata(event.metadata),
                }
                for event in page.events
            ),
            "next_cursor": page.next_cursor,
        }

    def serialize_runtime_payload(self, payload: Any) -> Any:
        if is_dataclass(payload):
            payload = asdict(payload)
        return _strip_private_runtime_metadata(payload)


def build_agent_candidate_payload_from_runtime_output(
    runtime_output: Mapping[str, Any],
) -> AgentCandidatePayload:
    """Map sanitized graph output into the formal application candidate contract."""

    if not isinstance(runtime_output, Mapping):
        raise RuntimeValidationError("runtime candidate output must be a mapping")
    _reject_checkpoint_payload(runtime_output)
    if contains_sensitive_payload(runtime_output):
        raise RuntimePolicyError("runtime candidate output contains sensitive content")

    candidate_ref = _required_runtime_candidate_string(runtime_output, "candidate_ref")
    candidate_type = _required_runtime_candidate_string(runtime_output, "candidate_type")
    payload_schema_id = _required_runtime_candidate_string(runtime_output, "payload_schema_id")
    status = _required_runtime_candidate_string(runtime_output, "status")
    if status != "accepted":
        raise RuntimeValidationError("runtime candidate status must be accepted")

    payload = runtime_output.get("payload")
    if not isinstance(payload, dict):
        raise RuntimeValidationError("runtime candidate payload must be a dict")
    payload_candidate_ref = str(payload.get("candidate_ref") or "").strip()
    if payload_candidate_ref != candidate_ref:
        raise RuntimeValidationError("runtime candidate payload candidate_ref must match candidate_ref")

    return AgentCandidatePayload(
        candidate_ref=candidate_ref,
        candidate_type=candidate_type,
        payload_schema_id=payload_schema_id,
        payload=payload,
        status=status,
        trace_refs=_runtime_ref_tuple(runtime_output.get("trace_refs"), "trace_refs"),
        validation_refs=_runtime_ref_tuple(runtime_output.get("validation_refs"), "validation_refs"),
        low_confidence_flags=_runtime_ref_tuple(
            runtime_output.get("low_confidence_flags"),
            "low_confidence_flags",
        ),
    )


def map_runtime_candidate_payloads(
    runtime_outputs: Iterable[Mapping[str, Any]] | None,
) -> tuple[AgentCandidatePayload, ...]:
    if runtime_outputs is None:
        return ()
    if isinstance(runtime_outputs, (str, bytes, Mapping)):
        raise RuntimeValidationError("runtime candidate payloads must be an iterable of mappings")
    return tuple(build_agent_candidate_payload_from_runtime_output(output) for output in runtime_outputs)


def _strip_private_runtime_metadata(payload: Any) -> Any:
    sanitized = sanitize_payload(payload)
    if isinstance(sanitized, dict):
        public: dict[str, Any] = {}
        for key, value in sanitized.items():
            normalized = str(key).strip().lower()
            if normalized in _INTERNAL_METADATA_KEYS or is_sensitive_key(key):
                continue
            if normalized == "metadata" and isinstance(value, dict):
                public[str(key)] = _public_metadata(value)
            else:
                public[str(key)] = _strip_private_runtime_metadata(value)
        return public
    if isinstance(sanitized, list):
        return [_strip_private_runtime_metadata(item) for item in sanitized]
    if isinstance(sanitized, tuple):
        return tuple(_strip_private_runtime_metadata(item) for item in sanitized)
    return sanitized


def _public_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    public: dict[str, Any] = {}
    sanitized = sanitize_payload(metadata)
    for key, value in sanitized.items():
        normalized = str(key).strip().lower()
        if normalized in _INTERNAL_METADATA_KEYS or is_sensitive_key(key):
            continue
        public[str(key)] = _strip_private_runtime_metadata(value)
    return public


def _required_runtime_candidate_string(runtime_output: Mapping[str, Any], field_name: str) -> str:
    value = str(runtime_output.get(field_name) or "").strip()
    if not value:
        raise RuntimeValidationError(f"runtime candidate {field_name} is required")
    if contains_sensitive_payload(value):
        raise RuntimePolicyError(f"runtime candidate {field_name} contains sensitive content")
    return value


def _runtime_ref_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values: Iterable[Any] = (value,)
    elif isinstance(value, Iterable):
        values = value
    else:
        raise RuntimeValidationError(f"runtime candidate {field_name} must be iterable")
    refs = tuple(str(ref).strip() for ref in values if str(ref).strip())
    if contains_sensitive_payload(refs):
        raise RuntimePolicyError(f"runtime candidate {field_name} contains sensitive content")
    return refs


def _reject_checkpoint_payload(runtime_output: Mapping[str, Any]) -> None:
    for key in runtime_output:
        normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
        if normalized == "checkpoint_payload":
            raise RuntimePolicyError("runtime candidate output cannot use checkpoint payload")
