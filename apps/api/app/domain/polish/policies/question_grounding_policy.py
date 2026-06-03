"""Pure grounding policy for Polish question generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from app.domain.polish.policies.source_support_policy import SourceSupportLevel, SourceSupportPolicy


CLAIM_MODE_CLARIFICATION_NEEDED = "clarification_needed"
CLAIM_MODE_JOB_GAP_PROBE = "job_gap_probe"

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


class QuestionGroundingAction(str, Enum):
    ALLOW = "allow"
    DOWNGRADE = "downgrade"
    BLOCK = "block"
    CLARIFY = "clarify"


@dataclass(frozen=True)
class QuestionGroundingInput:
    question_text: str
    claim_mode: str | None
    primary_evidence_ref: str | None
    primary_evidence_text: str | None
    evidence_refs: tuple[str, ...] = ()
    primary_source_type: str | None = None
    source_support_level: SourceSupportLevel | str | None = None
    confirmed_asset_texts: tuple[str, ...] = ()


@dataclass(frozen=True)
class QuestionGroundingDecision:
    action: QuestionGroundingAction
    passed: bool
    reason_codes: tuple[str, ...] = ()
    blocking_reason_codes: tuple[str, ...] = ()
    warning_reason_codes: tuple[str, ...] = ()
    requires_clarification: bool = False
    manual_review_recommended: bool = False


class QuestionGroundingPolicy:
    @classmethod
    def evaluate(cls, question: QuestionGroundingInput) -> QuestionGroundingDecision:
        blocking: list[str] = []
        warnings: list[str] = []
        normalized_question = question.question_text.strip()
        support_level = _support_level(question.source_support_level)
        evidence_refs = tuple(ref for ref in question.evidence_refs if str(ref).strip())

        if not normalized_question:
            blocking.append("question_text_required")
        if (
            question.claim_mode != CLAIM_MODE_CLARIFICATION_NEEDED
            and question.primary_evidence_ref not in evidence_refs
        ):
            blocking.append("primary_evidence_ref_missing")
        if (question.primary_source_type or "").strip().lower() in HISTORY_SOURCE_TYPES:
            blocking.append("history_evidence_not_allowed")

        is_hypothetical_or_clarification = _is_hypothetical_or_clarification(normalized_question)
        has_factual_candidate_claim = _has_factual_candidate_claim(normalized_question)

        if support_level == SourceSupportLevel.INSUFFICIENT_CONTEXT:
            if question.claim_mode != CLAIM_MODE_CLARIFICATION_NEEDED and not is_hypothetical_or_clarification:
                blocking.append("insufficient_context_requires_clarification")
            elif not is_hypothetical_or_clarification:
                warnings.append("insufficient_context_material_completion_expected")

        if support_level == SourceSupportLevel.JOB_GAP_ONLY:
            for phrase in FORBIDDEN_JOB_GAP_CLAIM_PHRASES:
                if phrase in normalized_question:
                    blocking.append(f"job_gap_probe_forbidden_claim:{phrase}")
            if has_factual_candidate_claim:
                blocking.append("job_gap_only_forbidden_candidate_experience_claim")
            if not is_hypothetical_or_clarification:
                warnings.append("job_gap_only_should_be_hypothetical_or_capability_compensation")

        if support_level == SourceSupportLevel.ADJACENT_PROJECT_EVIDENCE:
            if has_factual_candidate_claim:
                blocking.append("adjacent_project_evidence_forbidden_completed_experience_claim")
            if not is_hypothetical_or_clarification:
                blocking.append("adjacent_project_evidence_requires_hypothetical_extension")
            warnings.append("adjacent_project_evidence_requires_assumption")

        if not evidence_refs and not is_hypothetical_or_clarification:
            blocking.append("empty_evidence_refs_for_factual_question")

        confirmed_assets_text = " ".join(question.confirmed_asset_texts)
        unsupported_stack_terms = _unsupported_stack_terms(
            normalized_question,
            supported_text=" ".join(
                item
                for item in (
                    question.primary_evidence_text or "",
                    confirmed_assets_text,
                )
                if item
            ),
        )
        if unsupported_stack_terms:
            if has_factual_candidate_claim:
                blocking.append("unsupported_technology_stack_as_completed_experience")
                if confirmed_assets_text:
                    blocking.append("question_conflicts_with_canonical_assets")
            elif support_level != SourceSupportLevel.DIRECT_PROJECT_EVIDENCE:
                warnings.append("unsupported_technology_stack_requires_assumption")
            else:
                warnings.append("unsupported_technology_stack_requires_evidence_review")

        if question.claim_mode == CLAIM_MODE_JOB_GAP_PROBE:
            for phrase in FORBIDDEN_JOB_GAP_CLAIM_PHRASES:
                if phrase in normalized_question:
                    blocking.append(f"job_gap_probe_forbidden_claim:{phrase}")

        if question.claim_mode == CLAIM_MODE_CLARIFICATION_NEEDED and not is_hypothetical_or_clarification:
            missing_materials = [
                required for required in CLARIFICATION_REQUIRED_MATERIALS if required not in normalized_question
            ]
            if len(missing_materials) == len(CLARIFICATION_REQUIRED_MATERIALS):
                blocking.append("clarification_question_missing_material_request")
            elif missing_materials:
                warnings.append("clarification_question_partial_material_request")

        if (
            support_level == SourceSupportLevel.DIRECT_PROJECT_EVIDENCE
            and question.claim_mode != CLAIM_MODE_CLARIFICATION_NEEDED
            and question.primary_evidence_text
        ):
            overlap = _grounded_term_overlap(question.primary_evidence_text, normalized_question)
            if overlap < MIN_GROUNDED_TERM_OVERLAP:
                blocking.append("source_contamination_or_ungrounded_question")

        blocking_codes = tuple(dict.fromkeys(blocking))
        warning_codes = tuple(dict.fromkeys(warnings))
        reason_codes = tuple(dict.fromkeys((*blocking_codes, *warning_codes)))
        return QuestionGroundingDecision(
            action=_action(
                blocking_codes=blocking_codes,
                warning_codes=warning_codes,
                support_level=support_level,
            ),
            passed=not blocking_codes,
            reason_codes=reason_codes,
            blocking_reason_codes=blocking_codes,
            warning_reason_codes=warning_codes,
            requires_clarification=support_level == SourceSupportLevel.INSUFFICIENT_CONTEXT,
            manual_review_recommended=bool(warning_codes),
        )


def _action(
    *,
    blocking_codes: tuple[str, ...],
    warning_codes: tuple[str, ...],
    support_level: SourceSupportLevel,
) -> QuestionGroundingAction:
    if blocking_codes:
        if support_level == SourceSupportLevel.INSUFFICIENT_CONTEXT:
            return QuestionGroundingAction.CLARIFY
        return QuestionGroundingAction.BLOCK
    if warning_codes:
        return QuestionGroundingAction.DOWNGRADE
    return QuestionGroundingAction.ALLOW


def _support_level(value: SourceSupportLevel | str | None) -> SourceSupportLevel:
    return SourceSupportPolicy.normalize_level(value) or SourceSupportLevel.INSUFFICIENT_CONTEXT


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
