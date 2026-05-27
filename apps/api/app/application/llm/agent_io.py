"""Shared agent input objects for LLM prompt payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


_AGENT_PROMPT_BUNDLE_EXTRA_FIELD_KEYS = (
    "asset_id",
    "policy_version",
    "policy_source",
    "policy_source_type",
    "policy_source_version",
    "policy_fallback",
    "evidence_retrieval_hints",
    "evidence_selection_policy",
    "examples",
    "citation_rules",
    "refusal_and_low_confidence_policy",
    "conflict_check",
)
_AGENT_PROMPT_BUNDLE_STANDARD_FIELD_KEYS = frozenset(
    {
        "task_type",
        "prompt_version",
        "schema_id",
        "schema_version",
        "prompt",
        "input_data",
        "output_schema",
        "system_role",
        "developer_constraints",
        "user_task",
        "input_contract",
    }
)


@dataclass(frozen=True)
class AgentEvidenceItem:
    ref: str
    source_type: str
    title: str
    excerpt: str
    source_ref: dict[str, Any] = field(default_factory=dict)
    availability: str | None = None
    priority: int = 0
    reason: str | None = None
    keywords: tuple[str, ...] = ()

    def to_prompt_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ref": self.ref,
            "source_type": self.source_type,
            "title": self.title,
            "excerpt": self.excerpt,
        }
        if self.availability is not None:
            payload["availability"] = self.availability
        if self.source_ref:
            payload["source_ref"] = self.source_ref
        if self.priority != 0:
            payload["priority"] = self.priority
        if self.reason:
            payload["reason"] = self.reason
        if self.keywords:
            payload["keywords"] = list(self.keywords)
        return payload


@dataclass(frozen=True)
class AgentFocusTarget:
    ref: str
    title: str
    expected_capability: str
    missing_points: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_prompt_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ref": self.ref,
            "title": self.title,
            "expected_capability": self.expected_capability,
        }
        if self.missing_points:
            payload["missing_points"] = list(self.missing_points)
        metadata = _safe_metadata(self.metadata)
        if metadata:
            payload["metadata"] = metadata
        return payload


@dataclass(frozen=True)
class AgentPromptBundle:
    task_type: str
    prompt_version: str
    schema_id: str
    schema_version: str
    prompt: str
    input_data: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    system_role: str | None = None
    developer_constraints: tuple[str, ...] = ()
    user_task: str | None = None
    input_contract: dict[str, Any] = field(default_factory=dict)
    extra_fields: dict[str, Any] = field(default_factory=dict)

    def to_prompt_asset_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}

        _add_extra_field(payload, self.extra_fields, "asset_id")
        payload["prompt_version"] = self.prompt_version
        payload["schema_id"] = self.schema_id
        payload["schema_version"] = self.schema_version
        payload["task_type"] = self.task_type
        for key in (
            "policy_version",
            "policy_source",
            "policy_source_type",
            "policy_source_version",
            "policy_fallback",
        ):
            _add_extra_field(payload, self.extra_fields, key)
        payload["prompt"] = self.prompt
        if self.system_role is not None:
            payload["system_role"] = self.system_role
        if self.developer_constraints:
            payload["developer_constraints"] = list(self.developer_constraints)
        if self.user_task is not None:
            payload["user_task"] = self.user_task
        if self.input_contract:
            payload["input_contract"] = dict(self.input_contract)
        payload["input_data"] = dict(self.input_data)
        for key in ("evidence_retrieval_hints", "evidence_selection_policy"):
            _add_extra_field(payload, self.extra_fields, key)
        payload["output_schema"] = dict(self.output_schema)
        for key in (
            "examples",
            "citation_rules",
            "refusal_and_low_confidence_policy",
            "conflict_check",
        ):
            _add_extra_field(payload, self.extra_fields, key)
        return payload


def _add_extra_field(payload: dict[str, Any], extra_fields: dict[str, Any], key: str) -> None:
    if (
        key in _AGENT_PROMPT_BUNDLE_EXTRA_FIELD_KEYS
        and key not in _AGENT_PROMPT_BUNDLE_STANDARD_FIELD_KEYS
        and key in extra_fields
    ):
        payload[key] = extra_fields[key]


def _safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        if not isinstance(key, str) or not key:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
    return safe
