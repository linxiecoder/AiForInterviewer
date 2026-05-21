"""Internal metadata model for evidence-aware polish questions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.application.polish.evidence_signals import EvidenceSignalSet, SIGNAL_VERSION


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
    builder_version: str = BUILDER_VERSION
    validator_version: str = VALIDATOR_VERSION
    signal_version: str = SIGNAL_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_pattern": self.question_pattern,
            "scenario_constraint_summary": self.scenario_constraint_summary,
            "expected_answer_dimensions": list(self.expected_answer_dimensions),
            "quality_score": self.quality_score,
            "quality_warnings": list(self.quality_warnings),
            "confidence_level": self.confidence_level,
            "low_confidence_flags": list(self.low_confidence_flags),
            "evidence_signal_refs": list(self.evidence_signal_refs),
            "anti_repeat_refs": list(self.anti_repeat_refs),
            "builder_version": self.builder_version,
            "validator_version": self.validator_version,
            "signal_version": self.signal_version,
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


def _scenario_summary(scenario_constraint: Any) -> str | None:
    parts = [
        getattr(scenario_constraint, "business_constraint", None),
        getattr(scenario_constraint, "failure_mode", None),
        getattr(scenario_constraint, "scale_or_performance_constraint", None),
        getattr(scenario_constraint, "consistency_constraint", None),
    ]
    text = "；".join(str(part) for part in parts if part)
    return text[:500] if text else None


def _dedupe(items: list[str]) -> tuple[str, ...]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return tuple(result)
