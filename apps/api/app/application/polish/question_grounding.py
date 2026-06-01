"""Grounding checks for Phase 1 Polish question generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.application.polish.question_blueprint import (
    CLAIM_MODE_CLARIFICATION_NEEDED,
    CLAIM_MODE_JOB_GAP_PROBE,
    QuestionBlueprint,
)


FORBIDDEN_JOB_GAP_CLAIM_PHRASES = ("你负责过", "你实现过", "你主导过", "你参与过")
FACTUAL_CANDIDATE_CLAIM_PHRASES = (
    "你负责过",
    "你实现过",
    "你主导过",
    "你参与过",
    "你落地过",
    "你设计了",
    "你实现了",
    "你主导了",
    "你负责了",
    "你落地了",
    "在你负责的项目中",
    "在你做的项目中",
    "你亲身参与的项目",
)
HYPOTHETICAL_OR_CLARIFICATION_MARKERS = (
    "如果",
    "假设",
    "你会如何",
    "会如何",
    "如何补齐",
    "补齐相关能力",
    "设计验证路径",
    "能力补偿",
    "请先补充",
    "材料不足",
    "请提供真实材料",
    "能否补充",
)
CLARIFICATION_REQUIRED_MATERIALS = ("业务入口", "职责边界", "失败案例", "验证指标")
MIN_GROUNDED_TERM_OVERLAP = 1
HISTORY_SOURCE_TYPES = {"history_feedback", "previous_answer", "previous_question", "turn_answer", "turn_feedback"}
TECH_STACK_TERMS = (
    "Redis",
    "RocketMQ",
    "Kafka",
    "RabbitMQ",
    "MinIO",
    "MySQL",
    "PostgreSQL",
    "Elasticsearch",
    "OpenSearch",
    "MongoDB",
    "Kubernetes",
    "Docker",
    "FastAPI",
    "React",
    "Vue",
    "分布式锁",
    "事务消息",
    "半消息回查",
    "最终一致性",
    "状态机",
    "向量化",
)
SOURCE_SUPPORT_LEVELS = {
    "direct_project_evidence",
    "adjacent_project_evidence",
    "job_gap_only",
    "insufficient_context",
}


@dataclass(frozen=True)
class GroundingResult:
    passed: bool
    validation_errors: tuple[str, ...] = ()
    blocking_errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def validate_question_grounding(
    *,
    blueprint: QuestionBlueprint,
    question_text: str,
    primary_source_type: str | None,
    source_support_level: str | None = None,
    evidence_refs: tuple[str, ...] = (),
    canonical_project_assets: dict[str, Any] | None = None,
) -> GroundingResult:
    blocking: list[str] = []
    warnings: list[str] = []
    normalized_question = question_text.strip()
    support_level = _support_level(source_support_level)
    evidence_refs = tuple(ref for ref in evidence_refs if str(ref).strip())

    if not normalized_question:
        blocking.append("question_text_required")
    if (
        blueprint.claim_mode != CLAIM_MODE_CLARIFICATION_NEEDED
        and blueprint.primary_evidence_ref not in blueprint.evidence_refs
    ):
        blocking.append("primary_evidence_ref_missing")
    if (primary_source_type or "").strip().lower() in HISTORY_SOURCE_TYPES:
        blocking.append("history_evidence_not_allowed")

    is_hypothetical_or_clarification = _is_hypothetical_or_clarification(normalized_question)
    has_factual_candidate_claim = _has_factual_candidate_claim(normalized_question)

    if support_level == "insufficient_context":
        if blueprint.claim_mode != CLAIM_MODE_CLARIFICATION_NEEDED and not is_hypothetical_or_clarification:
            blocking.append("insufficient_context_requires_clarification")
        elif not is_hypothetical_or_clarification:
            warnings.append("insufficient_context_material_completion_expected")

    if support_level == "job_gap_only":
        for phrase in FORBIDDEN_JOB_GAP_CLAIM_PHRASES:
            if phrase in normalized_question:
                blocking.append(f"job_gap_probe_forbidden_claim:{phrase}")
        if has_factual_candidate_claim:
            blocking.append("job_gap_only_forbidden_candidate_experience_claim")
        if not is_hypothetical_or_clarification:
            warnings.append("job_gap_only_should_be_hypothetical_or_capability_compensation")

    if support_level == "adjacent_project_evidence":
        if has_factual_candidate_claim:
            blocking.append("adjacent_project_evidence_forbidden_completed_experience_claim")
        if not is_hypothetical_or_clarification:
            blocking.append("adjacent_project_evidence_requires_hypothetical_extension")
        warnings.append("adjacent_project_evidence_requires_assumption")

    if not evidence_refs and not is_hypothetical_or_clarification:
        blocking.append("empty_evidence_refs_for_factual_question")

    canonical_assets_text = _canonical_assets_text(canonical_project_assets)
    unsupported_stack_terms = _unsupported_stack_terms(
        normalized_question,
        supported_text=" ".join(
            item
            for item in (
                blueprint.primary_evidence_text or "",
                canonical_assets_text,
            )
            if item
        ),
    )
    if unsupported_stack_terms:
        if has_factual_candidate_claim:
            blocking.append("unsupported_technology_stack_as_completed_experience")
            if canonical_assets_text:
                blocking.append("question_conflicts_with_canonical_assets")
        elif support_level != "direct_project_evidence":
            warnings.append("unsupported_technology_stack_requires_assumption")
        else:
            warnings.append("unsupported_technology_stack_requires_evidence_review")

    if blueprint.claim_mode == CLAIM_MODE_JOB_GAP_PROBE:
        for phrase in FORBIDDEN_JOB_GAP_CLAIM_PHRASES:
            if phrase in normalized_question:
                blocking.append(f"job_gap_probe_forbidden_claim:{phrase}")

    if blueprint.claim_mode == CLAIM_MODE_CLARIFICATION_NEEDED and not is_hypothetical_or_clarification:
        missing_materials = [required for required in CLARIFICATION_REQUIRED_MATERIALS if required not in normalized_question]
        if len(missing_materials) == len(CLARIFICATION_REQUIRED_MATERIALS):
            blocking.append("clarification_question_missing_material_request")
        elif missing_materials:
            warnings.append("clarification_question_partial_material_request")

    if (
        support_level == "direct_project_evidence"
        and blueprint.claim_mode != CLAIM_MODE_CLARIFICATION_NEEDED
        and blueprint.primary_evidence_text
    ):
        overlap = _grounded_term_overlap(blueprint.primary_evidence_text, normalized_question)
        if overlap < MIN_GROUNDED_TERM_OVERLAP:
            blocking.append("source_contamination_or_ungrounded_question")

    validation_errors = tuple(dict.fromkeys((*blocking, *warnings)))
    return GroundingResult(
        passed=not blocking,
        validation_errors=validation_errors,
        blocking_errors=tuple(dict.fromkeys(blocking)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _support_level(value: str | None) -> str:
    text = str(value or "").strip().lower()
    return text if text in SOURCE_SUPPORT_LEVELS else "insufficient_context"


def _is_hypothetical_or_clarification(question_text: str) -> bool:
    return any(marker in question_text for marker in HYPOTHETICAL_OR_CLARIFICATION_MARKERS)


def _has_factual_candidate_claim(question_text: str) -> bool:
    return any(phrase in question_text for phrase in FACTUAL_CANDIDATE_CLAIM_PHRASES)


def _unsupported_stack_terms(question_text: str, *, supported_text: str) -> tuple[str, ...]:
    supported = supported_text.lower()
    unsupported: list[str] = []
    for term in TECH_STACK_TERMS:
        if term.lower() in question_text.lower() and term.lower() not in supported:
            unsupported.append(term)
    return tuple(unsupported)


def _canonical_assets_text(canonical_project_assets: dict[str, Any] | None) -> str:
    if not isinstance(canonical_project_assets, dict):
        return ""
    items = canonical_project_assets.get("items") if isinstance(canonical_project_assets.get("items"), list) else []
    parts: list[str] = []
    for item in items[:5]:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip() != "asset_confirmed":
            continue
        parts.extend(
            str(item.get(key) or "")
            for key in ("title", "summary", "content_excerpt")
            if str(item.get(key) or "").strip()
        )
    return " ".join(parts)


def _grounded_term_overlap(source_text: object, question_text: str) -> int:
    source_terms = _grounding_terms(source_text)
    question_terms = _grounding_terms(question_text)
    return len(source_terms & question_terms)


def _grounding_terms(value: object) -> set[str]:
    text = str(value or "")
    terms = {term.lower() for term in TECH_STACK_TERMS if term.lower() in text.lower()}
    normalized = "".join(ch if ch.isalnum() or "\u4e00" <= ch <= "\u9fff" else " " for ch in text.lower())
    terms.update(term for term in normalized.split() if len(term) >= 2)
    terms.update(re.findall(r"[a-z0-9_+#.-]{2,}", text.lower()))
    return terms
