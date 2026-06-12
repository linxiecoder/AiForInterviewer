"""Shared application-level context hygiene metadata contract."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.application.llm.types import P7_PROVIDER_FORBIDDEN_KEYS


class ContextHygieneStatus(str, Enum):
    CLEAN = "clean"
    PARTIAL = "partial"
    FALLBACK = "fallback"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


CONTEXT_HYGIENE_STATUSES = frozenset(status.value for status in ContextHygieneStatus)
REDACTED_CONTEXT_HYGIENE_DETAIL = "redacted_sensitive_detail"
CONTEXT_HYGIENE_FORBIDDEN_KEYS = frozenset(P7_PROVIDER_FORBIDDEN_KEYS) | frozenset(
    {
        "prompt",
        "system_prompt",
        "developer_prompt",
        "user_prompt",
        "completion",
        "provider_response",
        "raw_provider_response",
        "primary_evidence_text",
        "full_evidence_text",
        "full_source",
        "source_document",
    }
)
_SENSITIVE_TEXT_MARKERS = tuple(sorted(CONTEXT_HYGIENE_FORBIDDEN_KEYS))
_SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|token|secret|cookie)\s*[:=]\s*[^\s,;，；]+"
)


@dataclass(frozen=True)
class ContextHygieneMetadata:
    context_hygiene_status: ContextHygieneStatus
    safe_context_metadata: dict[str, Any] = field(default_factory=dict)
    fallback_reason: str | None = None
    validation_signals: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "context_hygiene_status": self.context_hygiene_status.value,
            "safe_context_metadata": dict(self.safe_context_metadata),
            "validation_signals": dict(self.validation_signals),
        }
        if self.fallback_reason is not None:
            payload["fallback_reason"] = self.fallback_reason
        return payload


def build_context_hygiene_metadata(
    *,
    status: ContextHygieneStatus | str,
    safe_context_metadata: dict[str, Any] | None = None,
    fallback_reason: str | None = None,
    validation_errors: tuple[str, ...] | list[str] = (),
    validation_signals: dict[str, Any] | None = None,
) -> ContextHygieneMetadata:
    signals = sanitize_safe_json(validation_signals or {}, max_items=16, max_depth=3)
    if not isinstance(signals, dict):
        signals = {}
    safe_errors = _safe_string_list(validation_errors, max_items=8, max_chars=160)
    if safe_errors:
        signals["validation_errors"] = safe_errors
    metadata = ContextHygieneMetadata(
        context_hygiene_status=normalize_context_hygiene_status(status),
        safe_context_metadata=sanitize_safe_context_metadata(safe_context_metadata or {}),
        fallback_reason=_safe_string(fallback_reason, max_chars=120),
        validation_signals=signals,
    )
    assert_safe_context_metadata(metadata.safe_context_metadata)
    return metadata


def normalize_context_hygiene_metadata(raw: object) -> dict[str, Any]:
    if isinstance(raw, ContextHygieneMetadata):
        return raw.to_dict()
    payload = raw if isinstance(raw, dict) else {}
    status = normalize_context_hygiene_status(payload.get("context_hygiene_status"))
    fallback_reason = _safe_string(payload.get("fallback_reason"), max_chars=120)
    safe_context_metadata = sanitize_safe_context_metadata(payload.get("safe_context_metadata") or {})
    validation_signals = sanitize_safe_json(
        payload.get("validation_signals") or {},
        max_items=16,
        max_depth=3,
    )
    if not isinstance(validation_signals, dict):
        validation_signals = {}
    result: dict[str, Any] = {
        "context_hygiene_status": status.value,
        "safe_context_metadata": safe_context_metadata,
        "fallback_reason": fallback_reason,
        "validation_signals": validation_signals,
    }
    assert_safe_context_metadata(result["safe_context_metadata"])
    return result


def normalize_context_hygiene_status(raw: ContextHygieneStatus | object) -> ContextHygieneStatus:
    if isinstance(raw, ContextHygieneStatus):
        return raw
    value = _safe_string(raw, max_chars=40)
    try:
        return ContextHygieneStatus(value)
    except ValueError:
        return ContextHygieneStatus.UNKNOWN


def sanitize_safe_context_metadata(raw: object) -> dict[str, Any]:
    value = sanitize_safe_json(raw, max_items=24, max_depth=4)
    return value if isinstance(value, dict) else {}


def sanitize_safe_json(raw: object, *, max_items: int, max_depth: int) -> Any:
    if max_depth <= 0:
        return None
    if raw is None or isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return raw
    if isinstance(raw, str):
        return _safe_string(raw, max_chars=600)
    if isinstance(raw, (list, tuple)):
        values: list[Any] = []
        for item in list(raw)[:max_items]:
            safe_item = sanitize_safe_json(item, max_items=max_items, max_depth=max_depth - 1)
            if safe_item is not None:
                values.append(safe_item)
        return values
    if isinstance(raw, dict):
        values: dict[str, Any] = {}
        for key, item in raw.items():
            if len(values) >= max_items:
                break
            safe_key = _safe_key(key)
            if not safe_key:
                continue
            safe_item = sanitize_safe_json(item, max_items=max_items, max_depth=max_depth - 1)
            if safe_item is not None:
                values[safe_key] = safe_item
        return values
    return _safe_string(raw, max_chars=600)


def assert_safe_context_metadata(metadata: object) -> None:
    unsafe_paths = _unsafe_paths(metadata)
    if unsafe_paths:
        raise ValueError("unsafe_context_hygiene_metadata:" + ",".join(unsafe_paths))


def _unsafe_paths(value: object, *, path: str = "$") -> tuple[str, ...]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = _normalize_key(key)
            item_path = f"{path}.{key}"
            if key_text in CONTEXT_HYGIENE_FORBIDDEN_KEYS or "prompt" in key_text:
                paths.append(item_path)
            paths.extend(_unsafe_paths(item, path=item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_unsafe_paths(item, path=f"{path}[{index}]"))
    elif isinstance(value, str) and _contains_sensitive_text(value):
        paths.append(path)
    return tuple(paths)


def _safe_string_list(value: object, *, max_items: int, max_chars: int) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    safe: list[str] = []
    for item in list(value)[:max_items]:
        text = _safe_string(item, max_chars=max_chars)
        if text:
            safe.append(text)
    return safe


def _safe_key(value: object) -> str | None:
    key = _safe_string(value, max_chars=120)
    if not key:
        return None
    normalized = _normalize_key(key)
    if normalized in CONTEXT_HYGIENE_FORBIDDEN_KEYS or "prompt" in normalized:
        return None
    return key


def _safe_string(value: object, *, max_chars: int) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    if _contains_sensitive_text(text):
        return REDACTED_CONTEXT_HYGIENE_DETAIL
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text


def _contains_sensitive_text(value: str) -> bool:
    normalized = _normalize_key(value)
    if _SENSITIVE_ASSIGNMENT_PATTERN.search(value):
        return True
    return any(marker in normalized for marker in _SENSITIVE_TEXT_MARKERS)


def _normalize_key(value: object) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")
