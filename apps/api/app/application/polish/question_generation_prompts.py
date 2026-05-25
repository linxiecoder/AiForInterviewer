"""Blueprint-based surface prompt helpers for Phase 1 Polish question generation."""

from __future__ import annotations

from typing import Any

from app.application.polish.question_blueprint import (
    CLAIM_MODE_CLARIFICATION_NEEDED,
    CLAIM_MODE_JOB_GAP_PROBE,
    EvidenceScope,
    QuestionBlueprint,
)


QUESTION_SURFACE_PROMPT_VERSION = "polish_question_surface.phase1"


def build_question_surface_prompt(blueprint: QuestionBlueprint, scope: EvidenceScope) -> dict[str, Any]:
    return {
        "prompt_version": QUESTION_SURFACE_PROMPT_VERSION,
        "instruction": "只把 QuestionBlueprint 表达成题干，不新增事实、不做题型路由、不做 repair。",
        "question_kind": blueprint.question_kind,
        "claim_mode": blueprint.claim_mode,
        "progress_node_ref": blueprint.progress_node_ref,
        "node_title": blueprint.node_title,
        "expected_capability": blueprint.expected_capability,
        "primary_evidence_ref": blueprint.primary_evidence_ref,
        "primary_evidence_text": blueprint.primary_evidence_text,
        "evidence_refs": list(blueprint.evidence_refs),
        "required_answer_materials": list(blueprint.required_answer_materials),
        "source_count": len(scope.question_sources),
    }


def render_blueprint_question(blueprint: QuestionBlueprint, scope: EvidenceScope) -> str:
    title = _clean(blueprint.node_title) or "当前训练节点"
    capability = _clean(blueprint.expected_capability) or "说明关键技术链路、取舍和验证方式"
    primary_text = _compact(_clean(blueprint.primary_evidence_text))
    if blueprint.claim_mode == CLAIM_MODE_CLARIFICATION_NEEDED:
        return (
            f"围绕「{title}」，当前材料不足以支撑具体题干。请先补充一个真实项目材料，"
            "必须包含业务入口、职责边界、失败案例和验证指标。"
        )
    if blueprint.claim_mode == CLAIM_MODE_JOB_GAP_PROBE:
        return (
            f"围绕「{title}」，岗位侧需要验证「{capability}」。"
            f"请基于主要要求「{primary_text}」，说明你会如何补齐相关能力、如何设计验证路径，"
            "以及面试中应如何证明该能力。"
        )
    return (
        f"围绕「{title}」，请只基于主要证据「{primary_text}」展开："
        f"先说明业务背景和关键技术链路，再说明异常处理或关键取舍，最后用验证指标证明你具备「{capability}」。"
    )


def _clean(value: object) -> str:
    return str(value or "").strip()


def _compact(value: str, *, limit: int = 96) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return f"{value[:limit].rstrip()}..."
