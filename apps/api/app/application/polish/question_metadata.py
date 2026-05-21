"""Internal metadata model for evidence-aware polish questions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.application.polish.evidence_signals import EvidenceSignalSet, SIGNAL_VERSION


QUESTION_METADATA_SCHEMA_ID = "polish_question_metadata"
QUESTION_METADATA_SCHEMA_VERSION = "1"
BUILDER_VERSION = "evidence-aware-question-builder-v1"
VALIDATOR_VERSION = "question-quality-validator-v2"


class QuestionBuilderVersion(str, Enum):
    EVIDENCE_AWARE_V1 = BUILDER_VERSION


class QuestionMetadataLowConfidenceFlag(str, Enum):
    SOURCE_UNAVAILABLE = "source_unavailable"
    EVIDENCE_MISSING = "evidence_missing"
    ABSTRACT_NODE_ONLY = "abstract_node_only"
    WEAK_METRIC_EVIDENCE = "weak_metric_evidence"
    WEAK_FAILURE_EVIDENCE = "weak_failure_evidence"
    VALIDATOR_REPAIRED = "validator_repaired"
    PATTERN_FALLBACK = "pattern_fallback"


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
    generated_at: str | None = None
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
            "generated_at": self.generated_at,
        }


def build_question_metadata(
    *,
    question_pattern: str | None,
    scenario_constraint: Any,
    expected_answer_dimensions: tuple[str, ...],
    quality_result: Any,
    evidence_signals: EvidenceSignalSet | None,
    anti_repeat_refs: tuple[str, ...] = (),
    additional_low_confidence_flags: tuple[str, ...] = (),
    source_availability: str | None = None,
    generated_at: str | None = None,
) -> QuestionMetadata:
    signal_refs = evidence_signals.evidence_refs if evidence_signals is not None else ()
    quality_flags = tuple(getattr(quality_result, "low_confidence_flags", ()))
    low_flags = _dedupe(
        [
            *tuple(getattr(scenario_constraint, "low_confidence_flags", ())),
            *(evidence_signals.low_confidence_flags if evidence_signals is not None else ()),
            *quality_flags,
            *additional_low_confidence_flags,
        ]
    )
    confidence_level = (
        evidence_signals.confidence_level
        if evidence_signals is not None and evidence_signals.confidence_level
        else getattr(scenario_constraint, "confidence_level", None)
    )
    return QuestionMetadata(
        question_pattern=question_pattern,
        scenario_constraint_summary=_scenario_summary(scenario_constraint),
        expected_answer_dimensions=tuple(expected_answer_dimensions),
        quality_score=getattr(quality_result, "quality_score", None),
        quality_warnings=tuple(getattr(quality_result, "warnings", ())),
        confidence_level=confidence_level,
        low_confidence_flags=low_flags,
        evidence_signal_refs=signal_refs,
        anti_repeat_refs=anti_repeat_refs,
        source_availability=source_availability,
        generated_at=generated_at,
    )


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
        "generated_at": _string_or_none(payload.get("generated_at"), max_chars=80),
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


def _scenario_summary(scenario_constraint: Any) -> str | None:
    parts = [
        getattr(scenario_constraint, "business_constraint", None),
        getattr(scenario_constraint, "failure_mode", None),
        getattr(scenario_constraint, "scale_or_performance_constraint", None),
        getattr(scenario_constraint, "consistency_constraint", None),
    ]
    text = "；".join(str(part) for part in parts if part)
    return text[:500] if text else None


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
