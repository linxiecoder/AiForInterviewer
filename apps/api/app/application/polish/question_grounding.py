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
UNSUPPORTED_INVENTORY_PIPELINE_TERMS = (
    "1GB 日志",
    "上传入口",
    "解析",
    "切块",
    "向量化",
    "入库",
    "15 秒到 3 秒",
)
INVENTORY_EVIDENCE_TERMS = ("库存", "分布式锁", "事务消息")
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
    primary_text = blueprint.primary_evidence_text or ""
    if any(term in primary_text for term in INVENTORY_EVIDENCE_TERMS):
        for unsupported in UNSUPPORTED_INVENTORY_PIPELINE_TERMS:
            if unsupported in normalized_question:
                errors.append(f"unsupported_inventory_pipeline_term:{unsupported}")
    return GroundingResult(passed=not errors, validation_errors=tuple(errors))
