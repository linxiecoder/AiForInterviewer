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

KNOWN_CONCRETE_ENTITIES = (
    "MinIO",
    "MQ",
    "MySQL",
    "PostgreSQL",
    "Redis",
    "Elasticsearch",
    "ES",
    "RocketMQ",
    "Kafka",
    "RabbitMQ",
    "OSS",
    "S3",
)

PRIMARY_EVIDENCE_GROUNDING_ISSUE = "primary_evidence_grounding_violation"
INSUFFICIENT_PRIMARY_EVIDENCE_FALLBACK = (
    "当前材料不足以支撑具体业务场景。请先补充一个你真实参与的项目链路，"
    "包括业务入口、你的职责边界、一个失败案例和一个验证指标，再按技术深度和表达结构回答。"
)
_PRIMARY_GROUNDING_GENERIC_TERMS = {
    "owner",
    "业务",
    "业务约束",
    "约束",
    "失败",
    "失败路径",
    "路径",
    "性能",
    "成本",
    "性能或成本",
    "性能或成本约束",
    "验证",
    "验证指标",
    "指标",
    "可观测",
    "核心",
    "视角",
    "说明",
    "围绕",
    "技术",
    "链路",
    "系统",
    "设计",
    "项目",
    "能力",
    "经验",
    "要求",
    "简历",
    "证据",
    "当前",
    "材料",
    "需要",
    "如何",
    "一个",
    "以及",
    "后续",
    "补充",
    "补齐",
    "计划",
    "trade-off",
    "业务约",
    "务约",
    "先限",
    "限定",
    "限定业务",
    "失败路",
    "败路",
    "性能或",
    "能或",
    "或成",
    "成本约",
    "本约",
    "证指",
    "如果",
    "状态",
    "收敛",
    "状态收敛",
    "一致",
    "一致性",
    "致性",
    "补偿",
    "资源",
    "可观",
    "观测",
    "对账",
    "重复",
    "消费",
    "重复消费",
}


@dataclass(frozen=True)
class QuestionQualityResult:
    quality_score: int
    blocking_issues: tuple[str, ...]
    warnings: tuple[str, ...]
    repair_suggestions: tuple[str, ...]
    allow_emit: bool
    low_confidence_flags: tuple[str, ...] = ()


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
    evidence_signals: Any | None = None,
    question_metadata: Any | None = None,
) -> QuestionQualityResult:
    blocking: list[str] = []
    warnings: list[str] = []
    repairs: list[str] = []
    low_flags: list[str] = [*getattr(evidence_signals, "low_confidence_flags", ())]
    low_flags.extend(getattr(question_metadata, "low_confidence_flags", ()) if question_metadata is not None else ())
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

    unsupported_entities = _unsupported_entities(question_text, scenario_constraint, evidence_signals)
    if unsupported_entities:
        blocking.append("unsupported_entity_reference")
    if _has_primary_evidence_grounding_violation(
        question_text=question_text,
        scenario_constraint=scenario_constraint,
        evidence_refs=tuple(str(ref) for ref in evidence_refs if str(ref)),
        question_metadata=question_metadata,
    ):
        blocking.append(PRIMARY_EVIDENCE_GROUNDING_ISSUE)

    if not evidence_refs or source_availability != "available":
        warnings.append("evidence_partially_available")
    if confidence_level == "low":
        warnings.append("low_confidence")
    if "weak_metric_evidence" in low_flags:
        warnings.append("weak_metric_evidence")
    if "weak_failure_evidence" in low_flags:
        warnings.append("weak_failure_evidence")
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
        low_confidence_flags=tuple(dict.fromkeys(low_flags)),
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
    return INSUFFICIENT_PRIMARY_EVIDENCE_FALLBACK


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


def _unsupported_entities(question_text: str, scenario_constraint: Any, evidence_signals: Any | None) -> tuple[str, ...]:
    supported = set(getattr(scenario_constraint, "system_components", ())) | set(
        getattr(scenario_constraint, "technical_entities", ())
    )
    if evidence_signals is not None:
        supported |= set(getattr(evidence_signals, "all_components", lambda: ())())
    supported |= _supported_aliases(supported)

    unsupported: list[str] = []
    for entity in KNOWN_CONCRETE_ENTITIES:
        if _mentions_entity(question_text, entity) and entity not in supported:
            unsupported.append(entity)
    return tuple(unsupported)


def _has_primary_evidence_grounding_violation(
    *,
    question_text: str,
    scenario_constraint: Any,
    evidence_refs: tuple[str, ...],
    question_metadata: Any | None,
) -> bool:
    primary = _primary_question_evidence(question_metadata)
    if not primary:
        return False

    summary = str(primary.get("summary") or "").strip()
    title = str(primary.get("title") or "").strip()
    source_type = str(primary.get("source_type") or "").strip()
    claim_mode = str(primary.get("claim_mode") or "").strip()
    allowed_refs = tuple(str(ref).strip() for ref in primary.get("allowed_source_refs", ()) if str(ref).strip())

    if allowed_refs and any(ref not in allowed_refs for ref in evidence_refs):
        return True
    if claim_mode == "job_gap_probe" and _has_any(
        question_text, ("你负责过", "你实现过", "你做过", "你主导过", "你参与过")
    ):
        return True
    if source_type == "insufficient" or claim_mode == "clarification_needed":
        return _fabricates_specific_business_context(question_text)
    if not summary:
        return False

    primary_terms = _grounding_terms(f"{title} {summary}")
    if primary_terms and not any(_contains_grounding_term(question_text, term) for term in primary_terms):
        return _has_specific_business_context(question_text)
    if claim_mode == "job_gap_probe":
        return False

    scenario_terms = _scenario_specific_terms(scenario_constraint)
    unsupported_scenario_terms = scenario_terms - primary_terms
    hits = [term for term in unsupported_scenario_terms if _contains_grounding_term(question_text, term)]
    return len(hits) >= 2 or any(_contains_digit_or_ascii(term) for term in hits)


def _primary_question_evidence(question_metadata: Any | None) -> dict[str, Any] | None:
    if isinstance(question_metadata, dict):
        value = question_metadata.get("primary_question_evidence")
        return value if isinstance(value, dict) else None
    value = getattr(question_metadata, "primary_question_evidence", None)
    return value if isinstance(value, dict) else None


def _scenario_specific_terms(scenario_constraint: Any) -> set[str]:
    terms: set[str] = set()
    for value in (
        *getattr(scenario_constraint, "system_components", ()),
        *getattr(scenario_constraint, "technical_entities", ()),
        *getattr(scenario_constraint, "metrics", ()),
    ):
        terms |= _grounding_terms(str(value))
    for value in (
        getattr(scenario_constraint, "business_constraint", None),
        getattr(scenario_constraint, "failure_mode", None),
        getattr(scenario_constraint, "scale_or_performance_constraint", None),
        getattr(scenario_constraint, "consistency_constraint", None),
    ):
        text = str(value or "")
        if re.search(r"[A-Za-z0-9]", text):
            terms |= _grounding_terms(text)
    return terms


def _grounding_terms(text: str) -> set[str]:
    terms: set[str] = set()
    normalized = text.lower()
    for match in re.findall(r"[a-z][a-z0-9+.#-]*|\d+(?:\.\d+)?%?", normalized):
        _add_grounding_term(terms, match)
    for segment in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        if len(segment) <= 12:
            _add_grounding_term(terms, segment)
        for size in (2, 3, 4):
            if len(segment) < size:
                continue
            for index in range(0, len(segment) - size + 1):
                _add_grounding_term(terms, segment[index : index + size])
    return terms


def _add_grounding_term(terms: set[str], term: str) -> None:
    clean = term.strip().lower()
    if len(clean) < 2 or clean in _PRIMARY_GROUNDING_GENERIC_TERMS:
        return
    if any(clean in generic or generic in clean for generic in _PRIMARY_GROUNDING_GENERIC_TERMS if len(generic) >= 2):
        return
    terms.add(clean)


def _contains_grounding_term(question_text: str, term: str) -> bool:
    if not term:
        return False
    return term.lower() in question_text.lower()


def _contains_digit_or_ascii(term: str) -> bool:
    return bool(re.search(r"[a-z0-9]", term))


def _fabricates_specific_business_context(question_text: str) -> bool:
    if _has_specific_business_context(question_text):
        return True
    clarification_terms = ("业务入口", "职责边界", "失败案例", "验证指标", "补充")
    return not all(term in question_text for term in clarification_terms)


def _has_specific_business_context(question_text: str) -> bool:
    return any(_mentions_entity(question_text, entity) for entity in KNOWN_CONCRETE_ENTITIES)


def _supported_aliases(supported: set[str]) -> set[str]:
    aliases: set[str] = set()
    if "Elasticsearch" in supported:
        aliases.add("ES")
    if "ES" in supported:
        aliases.add("Elasticsearch")
    return aliases


def _mentions_entity(question_text: str, entity: str) -> bool:
    if entity in {"ES", "S3", "MQ", "Redis"}:
        return bool(re.search(rf"(?<![A-Za-z0-9]){re.escape(entity)}(?![A-Za-z0-9])", question_text))
    return entity in question_text

def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)
