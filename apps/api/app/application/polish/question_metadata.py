"""Internal metadata model for evidence-aware polish questions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


QUESTION_METADATA_SCHEMA_ID = "polish_question_metadata"
QUESTION_METADATA_SCHEMA_VERSION = "1"
BUILDER_VERSION = "evidence-aware-question-builder-v1"
VALIDATOR_VERSION = "question-quality-validator-v2"
SIGNAL_VERSION = "evidence-signals-v1"


@dataclass(frozen=True)
class QuestionMetadata:
    question_pattern: str | None
    scenario_constraint_summary: str | None
    expected_answer_dimensions: tuple[str, ...]
    quality_score: int | None
    quality_warnings: tuple[str, ...]
    confidence_level: str | None
    low_confidence_flags: tuple[str, ...]
    evidence_signal_refs: tuple[str, ...]
    anti_repeat_refs: tuple[str, ...]
    source_availability: str | None = None
    primary_question_evidence: dict[str, Any] | None = None
    primary_question_evidence_ref: str | None = None
    claim_mode: str | None = None
    grounding_gate_result: str | None = None
    grounding_gate_issues: tuple[str, ...] = ()
    generated_at: str | None = None
    generation_mode: str | None = None
    request_source: str | None = None
    selected_primary_category_ref: str | None = None
    selected_secondary_category_ref: str | None = None
    selected_progress_node_ref: str | None = None
    selected_category_path: tuple[str, ...] = ()
    parent_question_id: str | None = None
    parent_answer_id: str | None = None
    parent_feedback_id: str | None = None
    exclude_question_refs: tuple[str, ...] = ()
    completed_focus_refs: tuple[str, ...] = ()
    focus_dimension: str | None = None
    focus_key: str | None = None
    template_signature: str | None = None
    blueprint_signature: str | None = None
    duplicate_gate_result: str | None = None
    similarity_checked: bool = False
    max_similarity_in_same_category: float | None = None
    mastery_exception_used: bool = False
    follow_up_reason: str | None = None
    follow_up_target_dimension: str | None = None
    builder_version: str = BUILDER_VERSION
    validator_version: str = VALIDATOR_VERSION
    signal_version: str = SIGNAL_VERSION
    schema_id: str = QUESTION_METADATA_SCHEMA_ID
    schema_version: str = QUESTION_METADATA_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "builder_version": self.builder_version,
            "validator_version": self.validator_version,
            "signal_version": self.signal_version,
            "question_pattern": self.question_pattern,
            "scenario_constraint_summary": self.scenario_constraint_summary,
            "expected_answer_dimensions": list(self.expected_answer_dimensions),
            "quality_score": self.quality_score,
            "quality_warnings": list(self.quality_warnings),
            "confidence_level": self.confidence_level,
            "low_confidence_flags": list(self.low_confidence_flags),
            "evidence_signal_refs": list(self.evidence_signal_refs),
            "anti_repeat_refs": list(self.anti_repeat_refs),
            "source_availability": self.source_availability,
            "primary_question_evidence": self.primary_question_evidence,
            "primary_question_evidence_ref": self.primary_question_evidence_ref,
            "claim_mode": self.claim_mode,
            "grounding_gate_result": self.grounding_gate_result,
            "grounding_gate_issues": list(self.grounding_gate_issues),
            "generated_at": self.generated_at,
            "generation_mode": self.generation_mode,
            "request_source": self.request_source,
            "selected_primary_category_ref": self.selected_primary_category_ref,
            "selected_secondary_category_ref": self.selected_secondary_category_ref,
            "selected_progress_node_ref": self.selected_progress_node_ref,
            "selected_category_path": list(self.selected_category_path),
            "parent_question_id": self.parent_question_id,
            "parent_answer_id": self.parent_answer_id,
            "parent_feedback_id": self.parent_feedback_id,
            "exclude_question_refs": list(self.exclude_question_refs),
            "completed_focus_refs": list(self.completed_focus_refs),
            "focus_dimension": self.focus_dimension,
            "focus_key": self.focus_key,
            "template_signature": self.template_signature,
            "blueprint_signature": self.blueprint_signature,
            "duplicate_gate_result": self.duplicate_gate_result,
            "similarity_checked": self.similarity_checked,
            "max_similarity_in_same_category": self.max_similarity_in_same_category,
            "mastery_exception_used": self.mastery_exception_used,
            "follow_up_reason": self.follow_up_reason,
            "follow_up_target_dimension": self.follow_up_target_dimension,
        }


def empty_question_metadata() -> QuestionMetadata:
    return QuestionMetadata(
        question_pattern=None,
        scenario_constraint_summary=None,
        expected_answer_dimensions=(),
        quality_score=None,
        quality_warnings=(),
        confidence_level=None,
        low_confidence_flags=(),
        evidence_signal_refs=(),
        anti_repeat_refs=(),
    )


def normalize_question_metadata(raw: object) -> dict[str, Any]:
    """Return a safe C-lite metadata object from persisted or legacy payloads."""

    payload = _metadata_payload(raw)
    if not payload:
        return empty_question_metadata().to_dict()

    normalized = {
        "schema_id": _string_or_none(payload.get("schema_id")) or QUESTION_METADATA_SCHEMA_ID,
        "schema_version": _string_or_none(payload.get("schema_version")) or QUESTION_METADATA_SCHEMA_VERSION,
        "builder_version": _string_or_none(payload.get("builder_version")) or BUILDER_VERSION,
        "validator_version": _string_or_none(payload.get("validator_version")) or VALIDATOR_VERSION,
        "signal_version": _string_or_none(payload.get("signal_version")) or SIGNAL_VERSION,
        "question_pattern": _string_or_none(payload.get("question_pattern")),
        "scenario_constraint_summary": _string_or_none(payload.get("scenario_constraint_summary"), max_chars=500),
        "expected_answer_dimensions": _string_list(payload.get("expected_answer_dimensions")),
        "quality_score": _quality_score_or_none(payload.get("quality_score")),
        "quality_warnings": _string_list(payload.get("quality_warnings")),
        "confidence_level": _string_or_none(payload.get("confidence_level")),
        "low_confidence_flags": _string_list(payload.get("low_confidence_flags")),
        "evidence_signal_refs": _string_list(payload.get("evidence_signal_refs")),
        "anti_repeat_refs": _string_list(payload.get("anti_repeat_refs")),
        "source_availability": _string_or_none(payload.get("source_availability")),
        "primary_question_evidence": _safe_primary_question_evidence(payload.get("primary_question_evidence")),
        "primary_question_evidence_ref": _string_or_none(
            payload.get("primary_question_evidence_ref"), max_chars=120
        ),
        "claim_mode": _string_or_none(payload.get("claim_mode"), max_chars=80),
        "grounding_gate_result": _string_or_none(payload.get("grounding_gate_result"), max_chars=80),
        "grounding_gate_issues": _string_list(payload.get("grounding_gate_issues")),
        "generated_at": _string_or_none(payload.get("generated_at"), max_chars=80),
        "generation_mode": _string_or_none(payload.get("generation_mode"), max_chars=80),
        "request_source": _string_or_none(payload.get("request_source"), max_chars=120),
        "selected_primary_category_ref": _string_or_none(
            payload.get("selected_primary_category_ref"), max_chars=120
        ),
        "selected_secondary_category_ref": _string_or_none(
            payload.get("selected_secondary_category_ref"), max_chars=120
        ),
        "selected_progress_node_ref": _string_or_none(payload.get("selected_progress_node_ref"), max_chars=120),
        "selected_category_path": _string_list(payload.get("selected_category_path")),
        "parent_question_id": _string_or_none(payload.get("parent_question_id"), max_chars=120),
        "parent_answer_id": _string_or_none(payload.get("parent_answer_id"), max_chars=120),
        "parent_feedback_id": _string_or_none(payload.get("parent_feedback_id"), max_chars=120),
        "exclude_question_refs": _string_list(payload.get("exclude_question_refs")),
        "completed_focus_refs": _string_list(payload.get("completed_focus_refs")),
        "focus_dimension": _string_or_none(payload.get("focus_dimension"), max_chars=160),
        "focus_key": _string_or_none(payload.get("focus_key"), max_chars=160),
        "template_signature": _string_or_none(payload.get("template_signature"), max_chars=240),
        "blueprint_signature": _string_or_none(payload.get("blueprint_signature"), max_chars=240),
        "duplicate_gate_result": _string_or_none(payload.get("duplicate_gate_result"), max_chars=120),
        "similarity_checked": _bool_or_false(payload.get("similarity_checked")),
        "max_similarity_in_same_category": _float_or_none(payload.get("max_similarity_in_same_category")),
        "mastery_exception_used": _bool_or_false(payload.get("mastery_exception_used")),
        "follow_up_reason": _string_or_none(payload.get("follow_up_reason"), max_chars=240),
        "follow_up_target_dimension": _string_or_none(payload.get("follow_up_target_dimension"), max_chars=240),
    }
    llm_keys = {
        "llm_task_type",
        "prompt_version",
        "question_schema_version",
        "llm_output_validation_status",
        "llm_generation_mode",
        "fallback_reason",
        "repair_attempted",
        "provider_summary",
        "model_summary",
        "validation_errors",
        "redaction_boundary",
    }
    if any(key in payload for key in llm_keys):
        normalized.update(
            {
                "llm_task_type": _string_or_none(payload.get("llm_task_type"), max_chars=120),
                "prompt_version": _string_or_none(payload.get("prompt_version"), max_chars=120),
                "question_schema_version": _int_or_none(payload.get("question_schema_version")),
                "llm_output_validation_status": _string_or_none(
                    payload.get("llm_output_validation_status"), max_chars=80
                ),
                "llm_generation_mode": _string_or_none(payload.get("llm_generation_mode"), max_chars=80),
                "fallback_reason": _string_or_none(payload.get("fallback_reason"), max_chars=120),
                "repair_attempted": _bool_or_false(payload.get("repair_attempted")),
                "provider_summary": _safe_summary_dict(payload.get("provider_summary")),
                "model_summary": _safe_summary_dict(payload.get("model_summary")),
                "validation_errors": _validation_errors(payload.get("validation_errors")),
                "redaction_boundary": _string_or_none(payload.get("redaction_boundary"), max_chars=160),
            }
        )
    return normalized


def question_metadata_to_dict(raw: object) -> dict[str, Any]:
    if isinstance(raw, QuestionMetadata):
        return normalize_question_metadata(raw.to_dict())
    to_dict = getattr(raw, "to_dict", None)
    if callable(to_dict):
        try:
            return normalize_question_metadata(to_dict())
        except Exception:
            return empty_question_metadata().to_dict()
    return normalize_question_metadata(raw)


def _metadata_payload(raw: object) -> dict[str, Any]:
    if isinstance(raw, QuestionMetadata):
        return raw.to_dict()
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}
    return {}


def _safe_primary_question_evidence(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    allowed_refs = _string_list(value.get("allowed_source_refs"))
    payload = {
        "ref": _string_or_none(value.get("ref"), max_chars=120),
        "source_type": _string_or_none(value.get("source_type"), max_chars=80),
        "title": _string_or_none(value.get("title"), max_chars=180),
        "summary": _string_or_none(value.get("summary"), max_chars=500),
        "claim_mode": _string_or_none(value.get("claim_mode"), max_chars=80),
        "allowed_source_refs": allowed_refs,
        "confidence_level": _string_or_none(value.get("confidence_level"), max_chars=40),
    }
    return payload if payload["ref"] and payload["summary"] else None


def _string_or_none(value: object, *, max_chars: int = 240) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    return text[:max_chars] if text else None


def _string_list(value: object, *, max_item_chars: int = 240) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items: list[object] = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        return []
    result: list[str] = []
    for item in raw_items:
        text = _string_or_none(item, max_chars=max_item_chars)
        if text and text not in result:
            result.append(text)
    return result


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool_or_false(value: object) -> bool:
    return bool(value) if isinstance(value, bool) else False


def _safe_summary_dict(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        text = _string_or_none(value, max_chars=80)
        return {"kind": text} if text else {}
    allowed = {"kind", "status", "validation_status", "confidence_level", "model_name", "error_type"}
    result: dict[str, Any] = {}
    for key in allowed:
        if key not in value:
            continue
        raw = value.get(key)
        if isinstance(raw, bool):
            result[key] = raw
        elif isinstance(raw, int):
            result[key] = raw
        else:
            text = _string_or_none(raw, max_chars=120)
            if text:
                result[key] = text
    return result


def _validation_errors(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value[:20]:
        if not isinstance(item, dict):
            continue
        code = _string_or_none(item.get("code"), max_chars=120)
        message = _string_or_none(item.get("message"), max_chars=200)
        if code:
            result.append({"code": code, "message": message or code})
    return result


def _quality_score_or_none(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        score = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, min(100, score))


def _dedupe(items: list[str]) -> tuple[str, ...]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return tuple(result)
