"""Quality validation for deterministic polish questions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from app.application.polish.question_patterns import QuestionPattern


LEGACY_TEMPLATE_PHRASES = (
    "请选一个你实际参与的具体场景",
    "讲清楚当时要解决的问题",
    "你负责的技术改造或决策",
    "为什么这样取舍",
    "上线后如何验证效果",
)

KNOWN_CONCRETE_ENTITIES = ("MinIO", "MQ", "MySQL", "Redis", "ES")


@dataclass(frozen=True)
class QuestionQualityResult:
    quality_score: int
    blocking_issues: tuple[str, ...]
    warnings: tuple[str, ...]
    repair_suggestions: tuple[str, ...]
    allow_emit: bool


def validate_question_quality(
    *,
    question_text: str,
    selected_pattern: QuestionPattern,
    theme_strategy: Any,
    scenario_constraint: Any,
    evidence_refs: list[str] | tuple[str, ...],
    recent_question_texts: list[str] | tuple[str, ...],
    source_availability: str,
    confidence_level: str,
) -> QuestionQualityResult:
    blocking: list[str] = []
    warnings: list[str] = []
    repairs: list[str] = []
    theme = getattr(theme_strategy, "theme", "mixed")

    if _is_legacy_template(question_text):
        blocking.append("legacy_template")
    if theme not in selected_pattern.applicable_themes:
        blocking.append("pattern_theme_mismatch")
    missing_required = [
        element for element in selected_pattern.required_question_elements if element not in question_text
    ]
    if missing_required:
        blocking.append("missing_pattern_required_elements")
        repairs.append("append_expected_answer_dimensions")

    if theme in {"technical", "mixed"} and "业务约束" not in question_text and "新业务约束" not in question_text:
        blocking.append("missing_business_constraint")
    if theme in {"technical", "mixed"} and not _has_engineering_closure(question_text):
        blocking.append("missing_failure_tradeoff_or_convergence")
    if theme == "mixed" and not all(term in question_text for term in ("显性技术", "隐性表达", "权重")):
        blocking.append("missing_mixed_weights")
        repairs.append("add_weight_hint")
    if theme == "communication" and "STAR" not in question_text:
        blocking.append("missing_star_structure")
    if _is_highly_repeated(question_text, recent_question_texts):
        blocking.append("highly_repeated_recent_question")
    if _looks_like_answer_leak(question_text):
        blocking.append("answer_leak")
    if _too_broad(question_text):
        blocking.append("question_too_broad")
        repairs.append("compress_to_main_question")

    unsupported_entities = _unsupported_entities(question_text, scenario_constraint)
    if unsupported_entities:
        blocking.append("unsupported_entity_reference")

    if not evidence_refs or source_availability != "available":
        warnings.append("evidence_partially_available")
    if confidence_level == "low":
        warnings.append("low_confidence")
    if not _has_any(question_text, ("指标", "吞吐", "耗时", "错误率", "成功率", "水位", "成本")):
        warnings.append("metrics_not_specific")
    if "成本" not in question_text:
        warnings.append("cost_constraint_weak")
    if not _has_any(question_text, ("可观测", "trace", "监控", "告警", "指标")):
        warnings.append("observability_constraint_weak")

    if "owner" not in question_text and "Owner" not in question_text:
        repairs.append("add_owner_perspective")
    if selected_pattern.expected_answer_dimensions and not _has_any(question_text, ("回答重点", "请按")):
        repairs.append("append_expected_answer_dimensions")

    score = max(0, 100 - len(blocking) * 35 - len(warnings) * 5)
    allow_emit = not blocking and score >= 70
    return QuestionQualityResult(
        quality_score=score,
        blocking_issues=tuple(dict.fromkeys(blocking)),
        warnings=tuple(dict.fromkeys(warnings)),
        repair_suggestions=tuple(dict.fromkeys(repairs)),
        allow_emit=allow_emit,
    )


def repair_question_text(
    *,
    question_text: str,
    selected_pattern: QuestionPattern,
    theme_strategy: Any,
    citations: str,
) -> str:
    repaired = question_text.strip()
    if selected_pattern.expected_answer_dimensions and "回答重点" not in repaired:
        repaired = (
            f"{repaired.rstrip('。')}。回答重点："
            f"{'、'.join(selected_pattern.expected_answer_dimensions[:6])}。"
        )
    if getattr(theme_strategy, "theme", "") == "mixed" and "权重比例" not in repaired:
        repaired = (
            f"本题权重比例为显性技术 {theme_strategy.explicit_weight}%、"
            f"隐性表达 {theme_strategy.implicit_weight}%。{repaired}"
        )
    if "owner" not in repaired.lower() and "Owner" not in repaired:
        repaired = repaired.replace("请", "请从 Owner 视角", 1)
    if citations and citations not in repaired:
        repaired = f"{repaired}{citations}"
    return repaired


def fallback_question_text(
    *,
    focus: str,
    selected_pattern: QuestionPattern,
    citations: str,
) -> str:
    dimensions = "、".join(selected_pattern.expected_answer_dimensions[:6])
    if selected_pattern.pattern_id == "star_communication_refactor":
        return (
            f"低置信度：围绕「{focus}」，当前材料不足以支撑更细的技术追问。"
            "请用 STAR 结构回答，先做背景压缩，再明确个人职责边界，按逻辑顺序说明关键动作，"
            "最后用复盘总结或口语化表达收束。"
            f"回答重点：{dimensions}。{citations}"
        )
    if selected_pattern.pattern_id == "mixed_technical_expression":
        return (
            f"低置信度：本题仍按显性技术 / 隐性表达的权重比例观察。围绕「{focus}」，"
            "请先限定业务约束，再说明一个失败路径下的技术深度、性能或成本约束、验证指标和核心 trade-off，"
            "同时用清晰的表达结构组织答案。"
            f"回答重点：{dimensions}。{citations}"
        )
    return (
        f"低置信度：围绕「{focus}」，当前材料不足以支撑具体组件追问。"
        "请先限定业务约束、补充项目链路、关键指标、失败案例和系统组件，再说明一个失败路径下的"
        "性能或成本约束、验证指标、收敛口径和核心 trade-off。"
        f"回答重点：{dimensions}。{citations}"
    )


def _is_legacy_template(question_text: str) -> bool:
    hits = sum(1 for phrase in LEGACY_TEMPLATE_PHRASES if phrase in question_text)
    return hits >= 4


def _has_engineering_closure(question_text: str) -> bool:
    return _has_any(
        question_text,
        (
            "失败",
            "兜底",
            "trade-off",
            "取舍",
            "状态机",
            "收敛",
            "补偿",
            "重试",
            "对账",
            "降级",
            "成本权衡",
        ),
    )


def _is_highly_repeated(question_text: str, recent_question_texts: list[str] | tuple[str, ...]) -> bool:
    normalized = _normalize_for_repeat(question_text)
    for recent in recent_question_texts[-5:]:
        if not recent:
            continue
        ratio = SequenceMatcher(None, normalized, _normalize_for_repeat(recent)).ratio()
        if ratio >= 0.82:
            return True
    return False


def _normalize_for_repeat(text: str) -> str:
    text = re.sub(r"「[^」]+」", "「FOCUS」", text)
    text = re.sub(r"\[[0-9]+\]", "", text)
    return " ".join(text.split())


def _looks_like_answer_leak(question_text: str) -> bool:
    leak_markers = ("参考答案：", "标准答案：", "完整参考答案", "答案如下", "可以这样回答：")
    return any(marker in question_text for marker in leak_markers)


def _too_broad(question_text: str) -> bool:
    question_marks = question_text.count("？") + question_text.count("?")
    separators = question_text.count("；") + question_text.count(";")
    return len(question_text) > 760 or question_marks + separators > 8


def _unsupported_entities(question_text: str, scenario_constraint: Any) -> tuple[str, ...]:
    supported = set(getattr(scenario_constraint, "system_components", ())) | set(
        getattr(scenario_constraint, "technical_entities", ())
    )
    unsupported: list[str] = []
    for entity in KNOWN_CONCRETE_ENTITIES:
        if entity in question_text and entity not in supported:
            unsupported.append(entity)
    return tuple(unsupported)


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)
