"""Grounding checks for Phase 1 Polish question generation."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.polish.question_blueprint import (
    CLAIM_MODE_CLARIFICATION_NEEDED,
    CLAIM_MODE_JOB_GAP_PROBE,
    QuestionBlueprint,
)


FORBIDDEN_JOB_GAP_CLAIM_PHRASES = ("你负责过", "你实现过", "你主导过", "你参与过")
CLARIFICATION_REQUIRED_MATERIALS = ("业务入口", "职责边界", "失败案例", "验证指标")
MIN_GROUNDED_TERM_OVERLAP = 1
HISTORY_SOURCE_TYPES = {"history_feedback", "previous_answer", "previous_question", "turn_answer", "turn_feedback"}


@dataclass(frozen=True)
class GroundingResult:
    passed: bool
    validation_errors: tuple[str, ...] = ()


def validate_question_grounding(
    *,
    blueprint: QuestionBlueprint,
    question_text: str,
    primary_source_type: str | None,
) -> GroundingResult:
    errors: list[str] = []
    normalized_question = question_text.strip()
    if not normalized_question:
        errors.append("question_text_required")
    if (
        blueprint.claim_mode != CLAIM_MODE_CLARIFICATION_NEEDED
        and blueprint.primary_evidence_ref not in blueprint.evidence_refs
    ):
        errors.append("primary_evidence_ref_missing")
    if (primary_source_type or "").strip().lower() in HISTORY_SOURCE_TYPES:
        errors.append("history_evidence_not_allowed")
    if blueprint.claim_mode == CLAIM_MODE_JOB_GAP_PROBE:
        for phrase in FORBIDDEN_JOB_GAP_CLAIM_PHRASES:
            if phrase in normalized_question:
                errors.append(f"job_gap_probe_forbidden_claim:{phrase}")
    if blueprint.claim_mode == CLAIM_MODE_CLARIFICATION_NEEDED:
        for required in CLARIFICATION_REQUIRED_MATERIALS:
            if required not in normalized_question:
                errors.append(f"clarification_missing_material:{required}")
    if blueprint.claim_mode != CLAIM_MODE_CLARIFICATION_NEEDED and blueprint.primary_evidence_text:
        overlap = _grounded_term_overlap(blueprint.primary_evidence_text, normalized_question)
        if overlap < MIN_GROUNDED_TERM_OVERLAP:
            errors.append("source_contamination_or_ungrounded_question")
    return GroundingResult(passed=not errors, validation_errors=tuple(errors))


def _grounded_term_overlap(source_text: object, question_text: str) -> int:
    source_terms = _grounding_terms(source_text)
    question_terms = _grounding_terms(question_text)
    return len(source_terms & question_terms)


def _grounding_terms(value: object) -> set[str]:
    normalized = "".join(ch if ch.isalnum() or "\u4e00" <= ch <= "\u9fff" else " " for ch in str(value).lower())
    return {term for term in normalized.split() if len(term) >= 2}
