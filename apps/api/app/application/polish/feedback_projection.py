"""Response-safe projection helpers for Polish feedback payloads."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, Final

from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
)


PENDING_FEEDBACK_TEXT: Final = "本轮反馈尚未生成"
DEFAULT_FEEDBACK_GENERATION_ERROR_CODE: Final = "llm_transport_generation_failed"
REDACTED_SENSITIVE_FEEDBACK_DETAIL: Final = "redacted_sensitive_detail"

ANSWER_NEXT_RECOMMENDED_ACTIONS: Final = (
    "answer_again",
    "continue_same_question",
)
FAILED_FEEDBACK_NEXT_RECOMMENDED_ACTIONS: Final = (
    "retry_same_question",
    "continue_same_question",
)

FEEDBACK_PAYLOAD_RESPONSE_TOP_LEVEL_KEYS: Final = frozenset(POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS) | frozenset(
    {
        "error",
        "retryable",
        "user_visible_status",
        "validation_errors",
    }
)

FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_KEYS: Final = frozenset(
    {
        "prompt",
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "user_prompt",
        "internal_prompt",
        "completion",
        "raw_completion",
        "full_completion",
        "completion_text",
        "reasoning_content",
        "provider_payload",
        "raw_provider",
        "raw_provider_payload",
        "provider_response",
        "raw_provider_response",
        "hidden_rubric",
        "full_evidence_text",
        "full_resume",
        "full_jd",
        "token",
        "api_key",
        "cookie",
        "secret",
        "hidden_scoring",
        "hidden_scoring_rules",
    }
)

FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_VALUE_MARKERS: Final = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "user_prompt",
    "internal_prompt",
    "raw_completion",
    "full_completion",
    "completion_text",
    "reasoning_content",
    "completion",
    "provider_payload",
    "raw_provider",
    "raw_provider_payload",
    "provider_response",
    "raw_provider_response",
    "hidden_rubric",
    "full_evidence_text",
    "full_resume",
    "full_resume_markdown",
    "full_jd",
    "full_jd_text",
    "hidden_scoring",
    "hidden_scoring_rules",
)

FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_ASSIGNMENT_PATTERNS: Final = (
    re.compile(r"api[_-]?key\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"cookie\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"token\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"secret\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"\bbearer\s+[a-z0-9._~+/=-]+", re.IGNORECASE),
)


def response_safe_feedback_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _with_legacy_feedback_text(payload)
    sanitized = _drop_forbidden_feedback_payload_response_keys(normalized)
    return sanitized if isinstance(sanitized, dict) else {}


def pending_feedback_payload(
    *,
    answer_id: str,
    session_id: str,
    question_id: str,
    feedback_id: str | None,
    trace_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
        "status": "pending",
        "feedback_text": PENDING_FEEDBACK_TEXT,
        "answer_summary": None,
        "score_result": None,
        "loss_points": [],
        "reference_answer": None,
        "next_recommended_actions": list(ANSWER_NEXT_RECOMMENDED_ACTIONS),
        "trace_refs": trace_refs,
        "low_confidence_flags": [],
        "feedback_metadata": {
            "llm_called": False,
            "pending_reason": "feedback_not_generated",
            "answer_id": answer_id,
            "session_id": session_id,
            "question_id": question_id,
        },
    }
    if feedback_id:
        payload["feedback_id"] = feedback_id
    return payload


def feedback_text_from_payload(payload: Mapping[str, Any] | None, fallback: str | None = None) -> str | None:
    if payload is None:
        return fallback
    for key in ("feedback_text", "feedback_summary"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


def feedback_error_code(
    validation_errors: Sequence[str],
    *,
    default: str = DEFAULT_FEEDBACK_GENERATION_ERROR_CODE,
) -> str:
    return next((error for error in validation_errors if error), default)


def redact_feedback_payload_text(value: str) -> str:
    normalized = re.sub(r"[\s-]+", "_", value.lower())
    if any(marker in normalized for marker in FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_VALUE_MARKERS):
        return REDACTED_SENSITIVE_FEEDBACK_DETAIL
    if any(pattern.search(value) for pattern in FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_ASSIGNMENT_PATTERNS):
        return REDACTED_SENSITIVE_FEEDBACK_DETAIL
    return value


def _with_legacy_feedback_text(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    if not _has_text(normalized.get("feedback_text")):
        legacy_text = feedback_text_from_payload(normalized)
        if legacy_text is not None:
            normalized["feedback_text"] = legacy_text
    return normalized


def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_forbidden_feedback_payload_response_key(key: str) -> bool:
    normalized = key.strip().lower()
    return normalized in FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_KEYS or "prompt" in normalized


def _drop_forbidden_feedback_payload_response_keys(value: Any, *, _depth: int = 0) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _drop_forbidden_feedback_payload_response_keys(item, _depth=_depth + 1)
            for key, item in value.items()
            if not _is_forbidden_feedback_payload_response_key(str(key))
            and (_depth != 0 or str(key) in FEEDBACK_PAYLOAD_RESPONSE_TOP_LEVEL_KEYS)
        }
    if isinstance(value, list):
        return [_drop_forbidden_feedback_payload_response_keys(item, _depth=_depth) for item in value]
    if isinstance(value, tuple):
        return [_drop_forbidden_feedback_payload_response_keys(item, _depth=_depth) for item in value]
    if isinstance(value, str):
        return redact_feedback_payload_text(value)
    return value
