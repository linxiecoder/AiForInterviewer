"""LLM wrapper for candidate memory/review enhancement with deterministic fallback."""

from __future__ import annotations

from copy import deepcopy
import os
from typing import Any

from app.infrastructure.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.infrastructure.llm.ports import LlmTransport
from app.infrastructure.llm.types import LlmTransportRequest, LlmTransportResult


CANDIDATE_LLM_ENABLED_ENV = "AIFI_POLISH_CANDIDATE_LLM_ENABLED"
CANDIDATE_REAL_PROVIDER_ENABLED_ENV = "AIFI_POLISH_CANDIDATE_REAL_PROVIDER_ENABLED"
POLISH_CANDIDATE_MEMORY_REVIEW_TASK_TYPE = "polish_candidate_memory_review"
POLISH_CANDIDATE_MEMORY_REVIEW_SCHEMA_ID = "polish_candidate_memory_review_v1"
POLISH_CANDIDATE_MEMORY_REVIEW_SCHEMA_VERSION = "1.0"
POLISH_CANDIDATE_MEMORY_REVIEW_CONTRACT_IDS = (
    "P-WEAKNESS-004",
    "P-ASSET-003",
    "P-TRAINING-003",
)

CANDIDATE_LLM_MODE_ACCEPTED = "llm_accepted"
CANDIDATE_LLM_MODE_FALLBACK = "llm_fallback"

FALLBACK_FEATURE_DISABLED = "feature_disabled"
FALLBACK_REAL_PROVIDER_DISABLED = "real_provider_disabled"
FALLBACK_PROVIDER_UNAVAILABLE = "provider_unavailable"
FALLBACK_PROVIDER_TIMEOUT = "provider_timeout"
FALLBACK_TRANSPORT_CONFIGURATION_ERROR = "transport_configuration_error"
FALLBACK_SCHEMA_INVALID = "schema_invalid"
FALLBACK_FORBIDDEN_OUTPUT_FIELD = "forbidden_output_field"

_TRUTHY = {"1", "true", "yes", "y", "on"}
_CANDIDATE_FIELDS = (
    "weakness_candidates",
    "asset_candidates",
    "training_suggestion_candidates",
    "oral_script_candidates",
    "polished_answer_candidates",
)
_FORBIDDEN_OUTPUT_KEYS = {
    "raw_prompt",
    "prompt",
    "system_prompt",
    "completion",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "provider_response",
    "raw_provider_response",
    "hidden_rubric",
    "hidden_scoring_rules",
    "secret",
    "api_key",
    "formal_weakness",
    "formal_asset",
    "formal_training_recommendation",
    "knowledge_base_write",
    "rag_write",
}
_FORBIDDEN_TEXT_MARKERS = (
    "raw_prompt",
    "raw prompt",
    "system_prompt",
    "system prompt",
    "completion",
    "provider_payload",
    "provider payload",
    "hidden_rubric",
    "hidden rubric",
    "hidden_scoring_rules",
    "secret=",
    "api_key",
    "bearer ",
    "formal_weakness",
    "formal_asset",
    "formal_training_recommendation",
    "knowledge_base_write",
    "rag_write",
)


class PolishCandidateLlmService:
    def __init__(self, transport: LlmTransport | None) -> None:
        self._transport = transport

    def enhance_with_llm_or_fallback(self, *, feedback_payload: dict[str, Any]) -> dict[str, Any]:
        if not should_enable_candidate_llm():
            return feedback_payload
        payload = deepcopy(feedback_payload)
        candidates = _candidate_records(payload)
        if not candidates:
            return _with_metadata(
                payload,
                mode=CANDIDATE_LLM_MODE_FALLBACK,
                fallback_reason="no_candidates",
                validation_status="not_requested",
            )
        if self._transport is None:
            return _with_metadata(
                payload,
                mode=CANDIDATE_LLM_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROVIDER_UNAVAILABLE,
                validation_status="not_requested",
            )
        if _provider_kind(self._transport) != "fake" and not should_allow_real_candidate_provider(self._transport):
            return _with_metadata(
                payload,
                mode=CANDIDATE_LLM_MODE_FALLBACK,
                fallback_reason=FALLBACK_REAL_PROVIDER_DISABLED,
                validation_status="not_requested",
            )
        try:
            transport_result = self._transport.generate(
                LlmTransportRequest(
                    contract_ids=POLISH_CANDIDATE_MEMORY_REVIEW_CONTRACT_IDS,
                    task_type=POLISH_CANDIDATE_MEMORY_REVIEW_TASK_TYPE,
                    input_refs=tuple(_candidate_ids(candidates)),
                    evidence_bundle=_candidate_evidence_bundle(candidates),
                )
            )
        except TimeoutError:
            return _with_metadata(
                payload,
                mode=CANDIDATE_LLM_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROVIDER_TIMEOUT,
                validation_status="not_requested",
            )
        except LlmTransportConfigurationError:
            return _with_metadata(
                payload,
                mode=CANDIDATE_LLM_MODE_FALLBACK,
                fallback_reason=FALLBACK_TRANSPORT_CONFIGURATION_ERROR,
                validation_status="not_requested",
            )
        except (LlmTransportUnavailableError, LlmTransportError):
            return _with_metadata(
                payload,
                mode=CANDIDATE_LLM_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROVIDER_UNAVAILABLE,
                validation_status="not_requested",
            )
        except LlmTransportResponseError:
            return _with_metadata(
                payload,
                mode=CANDIDATE_LLM_MODE_FALLBACK,
                fallback_reason=FALLBACK_SCHEMA_INVALID,
                validation_status="schema_invalid",
            )

        normalized = _validate_candidate_llm_output(transport_result, candidates=candidates)
        if normalized["valid"] is not True:
            return _with_metadata(
                payload,
                mode=CANDIDATE_LLM_MODE_FALLBACK,
                fallback_reason=str(normalized["reason"]),
                validation_status=str(normalized["validation_status"]),
            )
        return _apply_candidate_llm_output(payload, normalized["output"], transport_result)


def should_enable_candidate_llm() -> bool:
    return _truthy(os.getenv(CANDIDATE_LLM_ENABLED_ENV))


def should_allow_real_candidate_provider(transport: LlmTransport | None = None) -> bool:
    if transport is not None and _provider_kind(transport) == "fake":
        return True
    return _truthy(os.getenv(CANDIDATE_REAL_PROVIDER_ENABLED_ENV))


def _validate_candidate_llm_output(
    transport_result: LlmTransportResult,
    *,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    raw_output = transport_result.result
    if not isinstance(raw_output, dict):
        return _invalid(FALLBACK_SCHEMA_INVALID, "schema_invalid")
    if _contains_forbidden_output(raw_output):
        return _invalid(FALLBACK_FORBIDDEN_OUTPUT_FIELD, "schema_invalid")
    if raw_output.get("schema_id") != POLISH_CANDIDATE_MEMORY_REVIEW_SCHEMA_ID:
        return _invalid(FALLBACK_SCHEMA_INVALID, "schema_invalid")
    if raw_output.get("schema_version") != POLISH_CANDIDATE_MEMORY_REVIEW_SCHEMA_VERSION:
        return _invalid(FALLBACK_SCHEMA_INVALID, "schema_invalid")
    if raw_output.get("status") != "generated":
        return _invalid(FALLBACK_SCHEMA_INVALID, "schema_invalid")
    candidate_ids = set(_candidate_ids(candidates))
    enhancements = raw_output.get("candidate_enhancements")
    review_candidates = raw_output.get("review_recommendation_candidates")
    if not isinstance(enhancements, list) or not isinstance(review_candidates, list):
        return _invalid(FALLBACK_SCHEMA_INVALID, "schema_invalid")
    normalized_enhancements = []
    for item in enhancements:
        if not isinstance(item, dict):
            return _invalid(FALLBACK_SCHEMA_INVALID, "schema_invalid")
        candidate_id = _text(item.get("candidate_id"))
        if candidate_id is None or candidate_id not in candidate_ids:
            return _invalid("candidate_ref_invalid", "semantic_invalid")
        normalized_enhancements.append(
            {
                "candidate_id": candidate_id,
                "summary_hint": _text(item.get("summary_hint")) or "候选对象已通过 LLM 增强校验。",
                "review_focus": _text(item.get("review_focus")),
            }
        )
    normalized_reviews = []
    for item in review_candidates:
        if not isinstance(item, dict):
            return _invalid(FALLBACK_SCHEMA_INVALID, "schema_invalid")
        candidate_refs = _safe_candidate_refs(item.get("candidate_refs"), candidate_ids)
        if not candidate_refs:
            return _invalid("candidate_ref_invalid", "semantic_invalid")
        normalized_reviews.append(
            {
                "recommendation_id": _text(item.get("recommendation_id")) or f"review_rec_{candidate_refs[0]['resource_id']}",
                "title": _text(item.get("title")) or "候选复盘建议",
                "summary": _text(item.get("summary")) or "建议用户基于候选对象做一次复盘确认。",
                "candidate_refs": candidate_refs,
                "evidence_refs": _safe_ref_list(item.get("evidence_refs")),
            }
        )
    return {
        "valid": True,
        "output": {
            "candidate_enhancements": normalized_enhancements,
            "review_recommendation_candidates": normalized_reviews,
        },
    }


def _apply_candidate_llm_output(
    payload: dict[str, Any],
    output: dict[str, Any],
    transport_result: LlmTransportResult,
) -> dict[str, Any]:
    enhancements_by_id = {
        item["candidate_id"]: item
        for item in output["candidate_enhancements"]
    }
    for candidate in _candidate_records(payload):
        candidate_id = _text(candidate.get("candidate_id"))
        if candidate_id not in enhancements_by_id:
            continue
        candidate_payload = candidate.get("candidate_payload")
        if not isinstance(candidate_payload, dict):
            candidate_payload = {}
            candidate["candidate_payload"] = candidate_payload
        enhancement = enhancements_by_id[candidate_id]
        candidate_payload["llm_enhancement"] = {
            "status": "accepted",
            "summary_hint": enhancement["summary_hint"],
            "review_focus": enhancement.get("review_focus"),
            "confidence_level": _enum_value(transport_result.confidence_level),
            "trace_refs": list(transport_result.trace_refs),
            "evidence_refs": list(transport_result.evidence_refs),
            "formal_write_intent": False,
        }
        candidate["target_formal_ref"] = None
    payload["review_recommendation_candidates"] = output["review_recommendation_candidates"]
    return _with_metadata(
        payload,
        mode=CANDIDATE_LLM_MODE_ACCEPTED,
        fallback_reason=None,
        validation_status="valid",
        confidence_level=_enum_value(transport_result.confidence_level),
        trace_refs=list(transport_result.trace_refs),
        evidence_refs=list(transport_result.evidence_refs),
    )


def _with_metadata(
    payload: dict[str, Any],
    *,
    mode: str,
    fallback_reason: str | None,
    validation_status: str,
    confidence_level: str | None = None,
    trace_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    metadata = payload.get("feedback_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        payload["feedback_metadata"] = metadata
    metadata["candidate_llm_enhancement"] = {
        "mode": mode,
        "task_type": POLISH_CANDIDATE_MEMORY_REVIEW_TASK_TYPE,
        "validation_status": validation_status,
        "fallback_reason": fallback_reason,
        "confidence_level": confidence_level,
        "trace_refs": trace_refs or [],
        "evidence_refs": evidence_refs or [],
        "real_provider_enabled": _truthy(os.getenv(CANDIDATE_REAL_PROVIDER_ENABLED_ENV)),
    }
    return payload


def _candidate_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for field_name in _CANDIDATE_FIELDS:
        value = payload.get(field_name)
        if isinstance(value, list):
            records.extend(item for item in value if isinstance(item, dict))
    return records


def _candidate_evidence_bundle(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    safe_candidates = []
    evidence_refs: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = _text(candidate.get("candidate_id"))
        if candidate_id is None:
            continue
        candidate_evidence = _safe_ref_list(candidate.get("evidence_refs"))
        evidence_refs.extend(candidate_evidence)
        safe_candidates.append(
            {
                "candidate_id": candidate_id,
                "candidate_type": _text(candidate.get("candidate_type")),
                "title": _text(candidate.get("title")),
                "summary": _text(candidate.get("summary")),
                "evidence_excerpt": _text(candidate.get("evidence_excerpt")),
                "confidence_level": _text(candidate.get("confidence_level")),
                "evidence_refs": candidate_evidence,
            }
        )
    return {
        "schema_id": POLISH_CANDIDATE_MEMORY_REVIEW_SCHEMA_ID,
        "schema_version": POLISH_CANDIDATE_MEMORY_REVIEW_SCHEMA_VERSION,
        "candidate_ids": _candidate_ids(candidates),
        "candidates": safe_candidates,
        "evidence_refs": evidence_refs,
    }


def _candidate_ids(candidates: list[dict[str, Any]]) -> list[str]:
    return [
        candidate_id
        for candidate in candidates
        if (candidate_id := _text(candidate.get("candidate_id"))) is not None
    ]


def _contains_forbidden_output(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).lower()
            if any(forbidden in normalized_key for forbidden in _FORBIDDEN_OUTPUT_KEYS):
                return True
            if _contains_forbidden_output(item):
                return True
        return False
    if isinstance(value, list):
        return any(_contains_forbidden_output(item) for item in value)
    if isinstance(value, str):
        normalized_value = value.lower()
        return any(marker in normalized_value for marker in _FORBIDDEN_TEXT_MARKERS)
    return False


def _safe_candidate_refs(value: Any, candidate_ids: set[str]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    refs = []
    for item in value:
        if not isinstance(item, dict):
            continue
        resource_type = _text(item.get("resource_type"))
        resource_id = _text(item.get("resource_id"))
        if resource_type in {"polish_candidate", "weakness_candidate", "asset_candidate", "training_suggestion_candidate"} and resource_id in candidate_ids:
            refs.append({"resource_type": resource_type, "resource_id": resource_id})
    return refs


def _safe_ref_list(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    refs = []
    for item in value:
        if not isinstance(item, dict):
            continue
        resource_type = _text(item.get("resource_type") or item.get("trace_type"))
        resource_id = _text(item.get("resource_id") or item.get("trace_ref_id"))
        if resource_type and resource_id:
            refs.append({"resource_type": resource_type, "resource_id": resource_id})
    return refs


def _invalid(reason: str, validation_status: str) -> dict[str, Any]:
    return {"valid": False, "reason": reason, "validation_status": validation_status}


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    return trimmed[:400] if trimmed else None


def _provider_kind(transport: LlmTransport | None) -> str:
    status = str(getattr(transport, "status", "") or "").lower()
    if "fake" in status:
        return "fake"
    return "real" if transport is not None else "missing"


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in _TRUTHY
