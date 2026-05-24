"""Sanitized serializer boundary for PR4 LangGraph runtime infrastructure."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from app.application.ai_runtime.contracts import (
    AgentRunResult,
    AgentRunStatus,
    AgentRunTimelinePage,
    RuntimePolicyError,
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
