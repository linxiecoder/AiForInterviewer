"""Blueprint objects for Phase 1 Polish question generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.application.polish.entities import PolishQuestionSource


QUESTION_BLUEPRINT_VERSION = "polish_question_blueprint.phase1"

QUESTION_KIND_PROJECT_DEEP_DIVE = "project_deep_dive"
QUESTION_KIND_TECHNICAL_CHAIN_DEEP_DIVE = "technical_chain_deep_dive"
QUESTION_KIND_FAILURE_RECOVERY_DEEP_DIVE = "failure_recovery_deep_dive"
QUESTION_KIND_TRADEOFF_DESIGN = "tradeoff_design"
QUESTION_KIND_CLARIFICATION_NEEDED = "clarification_needed"

ALLOWED_QUESTION_KINDS = frozenset(
    {
        QUESTION_KIND_PROJECT_DEEP_DIVE,
        QUESTION_KIND_TECHNICAL_CHAIN_DEEP_DIVE,
        QUESTION_KIND_FAILURE_RECOVERY_DEEP_DIVE,
        QUESTION_KIND_TRADEOFF_DESIGN,
        QUESTION_KIND_CLARIFICATION_NEEDED,
    }
)

CLAIM_MODE_EVIDENCE_GROUNDED = "evidence_grounded"
CLAIM_MODE_JOB_GAP_PROBE = "job_gap_probe"
CLAIM_MODE_CLARIFICATION_NEEDED = "clarification_needed"


@dataclass(frozen=True)
class EvidenceScope:
    progress_node_ref: str
    node_title: str
    expected_capability: str
    missing_points: tuple[str, ...] = ()
    primary_evidence_ref: str | None = None
    primary_evidence_text: str | None = None
    primary_source_type: str | None = None
    evidence_refs: tuple[str, ...] = ()
    question_sources: tuple[PolishQuestionSource, ...] = ()
    context_digest: str | None = None
    dropped_context_summary: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QuestionBlueprint:
    question_kind: str
    claim_mode: str
    progress_node_ref: str
    node_title: str
    expected_capability: str
    primary_evidence_ref: str | None
    primary_evidence_text: str | None
    evidence_refs: tuple[str, ...]
    required_answer_materials: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


def build_question_blueprint(scope: EvidenceScope) -> QuestionBlueprint:
    claim_mode = _claim_mode(scope)
    question_kind = _question_kind(scope, claim_mode=claim_mode)
    required_materials = (
        ("业务入口", "职责边界", "失败案例", "验证指标")
        if claim_mode == CLAIM_MODE_CLARIFICATION_NEEDED
        else ()
    )
    evidence_refs = scope.evidence_refs
    if claim_mode == CLAIM_MODE_CLARIFICATION_NEEDED:
        evidence_refs = ()
    return QuestionBlueprint(
        question_kind=question_kind,
        claim_mode=claim_mode,
        progress_node_ref=scope.progress_node_ref,
        node_title=scope.node_title,
        expected_capability=scope.expected_capability,
        primary_evidence_ref=scope.primary_evidence_ref,
        primary_evidence_text=scope.primary_evidence_text,
        evidence_refs=evidence_refs,
        required_answer_materials=required_materials,
        metadata={
            "blueprint_version": QUESTION_BLUEPRINT_VERSION,
            "primary_source_type": scope.primary_source_type,
            "dropped_context_summary": scope.dropped_context_summary,
        },
    )


def _claim_mode(scope: EvidenceScope) -> str:
    if not scope.primary_evidence_ref or not _clean_text(scope.primary_evidence_text):
        return CLAIM_MODE_CLARIFICATION_NEEDED
    source_type = (scope.primary_source_type or "").strip().lower()
    if source_type.startswith("job_") or source_type in {"match_gap", "match_focus"}:
        return CLAIM_MODE_JOB_GAP_PROBE
    return CLAIM_MODE_EVIDENCE_GROUNDED


def _question_kind(scope: EvidenceScope, *, claim_mode: str) -> str:
    if claim_mode == CLAIM_MODE_CLARIFICATION_NEEDED:
        return QUESTION_KIND_CLARIFICATION_NEEDED
    text = " ".join(
        item
        for item in (scope.node_title, scope.expected_capability, " ".join(scope.missing_points))
        if item
    ).lower()
    if any(term in text for term in ("失败", "异常", "补偿", "降级", "恢复", "回滚")):
        return QUESTION_KIND_FAILURE_RECOVERY_DEEP_DIVE
    if any(term in text for term in ("取舍", "设计", "方案", "架构", "权衡")):
        return QUESTION_KIND_TRADEOFF_DESIGN
    if any(term in text for term in ("链路", "状态", "一致性", "事务", "锁", "技术")):
        return QUESTION_KIND_TECHNICAL_CHAIN_DEEP_DIVE
    return QUESTION_KIND_PROJECT_DEEP_DIVE


def _clean_text(value: object) -> str:
    return str(value or "").strip()
