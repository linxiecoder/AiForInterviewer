"""Progress Tree quality-first initial generation planner."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from app.application.polish.progress_context import has_sufficient_progress_context, truncate_text
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
)
from app.application.polish.progress_v2_prompts import (
    POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
    POLISH_PROGRESS_TREE_CONTRACT_IDS,
    build_progress_quality_first_menu_prompt,
)
from app.application.llm.structured_output import (
    filter_untrusted_structured_metadata,
    normalize_structured_status,
    structured_validation_errors_to_dicts,
)
from app.application.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.application.llm.ports import LlmTransport
from app.application.llm.types import LlmTransportRequest


PROGRESS_TREE_STATUS_READY = "ready"
PROGRESS_TREE_STATUS_FAILED = "failed"
PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT = "insufficient_context"

_RESUME_DEEP_DIVE = "resume_deep_dive"
_JD_GAP_LEARNING = "jd_gap_learning"
_DISPLAY_CATEGORY_TITLES = {
    _RESUME_DEEP_DIVE: "深度打磨类",
    _JD_GAP_LEARNING: "补齐学习类",
}
_ALLOWED_CATEGORIES = set(_DISPLAY_CATEGORY_TITLES)
_ALLOWED_BASIS_TYPES = {"resume_signal", "jd_requirement", "match_gap", "mixed"}
_QUALITY_FIRST_MAX_PRIMARY_NODES = 9
_QUALITY_FIRST_LOW_NODE_COUNT = 4
_QUALITY_FIRST_TARGET_MIN_PRIMARY_NODES = 6
_QUALITY_FIRST_CHECKLIST_TERMS = (
    "Linux",
    "Shell",
    "Git",
    "版本控制",
    "年限",
    "研发经验",
    "工作经验",
    "基础工具",
    "工具熟练",
    "通用工具",
)
_QUALITY_FIRST_GENERIC_TERMS = (
    "岗位能力拆解",
    "缺口补齐路径",
    "工程实践边界",
    "通用软技能",
    "综合能力",
    "基础能力",
    "工具熟练度",
    "技术栈熟悉度",
    "岗位匹配度",
)
_QUALITY_FIRST_COST_TERMS = ("成本", "资源优化", "资源利用率", "FinOps", "预算")

_ALLOWED_CONFIDENCE_LEVELS = {"high", "medium", "low"}
_ABSTRACT_TITLE_FRAGMENTS = {
    "项目真实性与个人贡献边界",
    "岗位匹配缺口与技术深度防御",
    "项目真实性",
    "个人贡献边界",
    "技术深度",
    "岗位匹配缺口",
}
_FORBIDDEN_DISPLAY_REPLACEMENTS = (
    ("攻击点", "追问方向"),
    ("攻击", "追问"),
    ("拷问", "深入追问"),
    ("技术碾压", "技术深挖"),
    ("碾压", "深度考察"),
    ("吊打", "明显优于"),
    ("火力", "追问强度"),
    ("红队", "审查"),
    ("必挂", "高风险"),
    ("必过", "更稳妥"),
    ("压力追问", "连续追问"),
    ("压迫", "连续追问"),
    ("击穿", "暴露"),
    ("杀招", "关键策略"),
    ("红旗", "失分风险"),
    ("防御", "表达准备"),
    ("P7", "高阶"),
    ("项自", "项目"),
    ("责献", "贡献"),
)
_FORBIDDEN_DISPLAY_TERMS = tuple(term for term, _ in _FORBIDDEN_DISPLAY_REPLACEMENTS)


class PolishProgressTreeQualityFirstPlanner:
    """Generate the initial Progress Tree with one quality-first planning call."""

    def __init__(self, transport: LlmTransport | None) -> None:
        self._transport = transport

    def generate_initial(self, context: dict[str, Any]) -> dict[str, Any]:
        if not has_sufficient_progress_context(context):
            return _quality_first_insufficient_artifacts(context)
        if self._transport is None:
            return _quality_first_failed_artifacts(
                context,
                reason="llm_transport_missing",
                validation_errors=[
                    {
                        "field": "transport",
                        "code": "missing",
                        "reason": "LLM transport is not configured.",
                    }
                ],
            )

        try:
            result = self._transport.generate(
                LlmTransportRequest(
                    contract_ids=POLISH_PROGRESS_TREE_CONTRACT_IDS,
                    task_type=POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
                    input_refs=_input_refs(context),
                    evidence_bundle=build_progress_quality_first_menu_prompt(context),
                )
            )
        except TimeoutError:
            return _quality_first_failed_artifacts(context, reason="provider_timeout")
        except (LlmTransportConfigurationError, LlmTransportUnavailableError):
            return _quality_first_failed_artifacts(context, reason="provider_unavailable")
        except LlmTransportResponseError:
            return _quality_first_failed_artifacts(context, reason="provider_response_invalid")

        payload = result.result
        if not isinstance(payload, dict):
            return _quality_first_failed_artifacts(
                context,
                reason="provider_response_invalid",
                validation_errors=[
                    {
                        "field": "result",
                        "code": "invalid_type",
                        "reason": "Quality-first planner result root must be an object.",
                    }
                ],
            )
        normalized = _normalize_quality_first_menu_payload(payload, context=context)
        if normalized is None:
            reason = _quality_first_payload_failure_reason(payload)
            return _quality_first_failed_artifacts(
                context,
                reason=reason,
                validation_errors=_quality_first_validation_errors(payload, reason=reason),
            )
        nodes, low_confidence_flags, quality_summary, deferred_candidates = normalized
        if not nodes:
            reason = "quality_first_all_nodes_deferred" if deferred_candidates else "quality_first_no_usable_nodes"
            return _quality_first_failed_artifacts(
                context,
                reason=reason,
                validation_errors=[
                    {
                        "field": "menu_categories.nodes",
                        "code": "all_deferred" if deferred_candidates else "empty",
                        "reason": "All quality-first planner nodes were deferred."
                        if deferred_candidates
                        else "Quality-first planner returned no usable nodes.",
                    }
                ],
            )

        metadata = {
            "pipeline_status": "success",
            "generation_mode": "quality_first",
            "planner_schema_id": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
            "input_context_mode": "full_resume_full_job",
            "task_types": [POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE],
            "prompt_versions": [POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION],
            "low_confidence_flags": _dedupe_strings(low_confidence_flags, limit=20),
            "failure_reason": None,
            "quality_summary": quality_summary,
            "deferred_candidates": deferred_candidates,
        }
        plan = {
            "schema_id": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
            "status": PROGRESS_TREE_STATUS_READY,
            "context_digest": context["content_digest"],
            "nodes": nodes,
            "v2_metadata": metadata,
        }
        return {
            "status": PROGRESS_TREE_STATUS_READY,
            "progress_tree_plan": plan,
            "progress_tree_state": _quality_first_initial_state_from_nodes(nodes, context=context),
            "progress_percent": 0,
        }


def _normalize_quality_first_menu_payload(
    payload: dict[str, Any],
    *,
    context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any], list[dict[str, Any]]] | None:
    canonical_status, status_warnings, status_errors = normalize_structured_status(payload.get("status"))
    if status_errors or canonical_status not in {"success", "partial"}:
        return None
    categories = payload.get("menu_categories")
    if not isinstance(categories, list):
        return None

    nodes: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    low_confidence_flags = _sanitize_string_list(payload.get("low_confidence_flags"), limit=20)
    low_confidence_flags.extend(status_warnings)
    deferred_candidates = _normalize_quality_first_deferred_candidates(
        payload.get("deferred_candidates"),
        context_digest=context["content_digest"],
    )
    _trusted_metadata, ignored_metadata_keys = filter_untrusted_structured_metadata(payload.get("metadata"))
    if ignored_metadata_keys:
        low_confidence_flags.append("llm_metadata_ignored")
    raw_node_count = 0
    valid_category_seen = False
    for category_index, category_payload in enumerate(categories, start=1):
        if not isinstance(category_payload, dict):
            low_confidence_flags.append("quality_first_category_invalid")
            continue
        category = str(category_payload.get("category") or "").strip()
        if category not in _ALLOWED_CATEGORIES:
            low_confidence_flags.append("quality_first_category_unknown")
            continue
        valid_category_seen = True
        display_category_title = _sanitize_display_text(
            category_payload.get("display_category_title") or _DISPLAY_CATEGORY_TITLES[category],
            max_chars=80,
        ) or _DISPLAY_CATEGORY_TITLES[category]
        raw_nodes = category_payload.get("nodes")
        if not isinstance(raw_nodes, list):
            low_confidence_flags.append(f"quality_first_{category}_nodes_missing")
            continue
        for node_index, item in enumerate(raw_nodes, start=1):
            raw_node_count += 1
            node = _normalize_quality_first_node(
                item,
                category=category,
                display_category_title=display_category_title,
                index=(category_index * 100) + node_index,
                category_node_index=node_index,
                context_digest=context["content_digest"],
            )
            if node is None:
                low_confidence_flags.append("quality_first_bad_leaf_removed")
                continue
            normalized_title = _normalize_label_for_compare(node["display_title"])
            if normalized_title in seen_titles:
                low_confidence_flags.append("quality_first_duplicate_leaf_removed")
                continue
            seen_titles.add(normalized_title)
            nodes.append(node)

    if not valid_category_seen:
        return None
    if raw_node_count >= 10:
        low_confidence_flags.append("quota_filling_risk")

    nodes, gate_deferred_candidates, gate_flags = _quality_first_apply_quality_gates(nodes, context=context)
    deferred_candidates.extend(gate_deferred_candidates)
    low_confidence_flags.extend(gate_flags)
    nodes = sorted(nodes, key=lambda node: _quality_first_node_sort_key(node, context=context))

    category_counts = {
        _RESUME_DEEP_DIVE: sum(1 for node in nodes if node.get("category") == _RESUME_DEEP_DIVE),
        _JD_GAP_LEARNING: sum(1 for node in nodes if node.get("category") == _JD_GAP_LEARNING),
    }
    if nodes and len(nodes) < _QUALITY_FIRST_LOW_NODE_COUNT:
        low_confidence_flags.append("quality_first_low_primary_node_count")
    elif nodes and len(nodes) < _QUALITY_FIRST_TARGET_MIN_PRIMARY_NODES:
        low_confidence_flags.append("quality_first_primary_nodes_below_target")
    if nodes and category_counts[_RESUME_DEEP_DIVE] == 0:
        low_confidence_flags.append("quality_first_resume_deep_dive_missing")
    if nodes and category_counts[_JD_GAP_LEARNING] == 0:
        low_confidence_flags.append("quality_first_jd_gap_learning_missing")
    deferred_candidates = _dedupe_quality_first_deferred_candidates(
        deferred_candidates,
        main_titles={_normalize_label_for_compare(node["display_title"]) for node in nodes},
    )

    planner_summary = _sanitize_display_text(payload.get("planner_summary"), max_chars=800)
    quality_summary = {
        "status": "ready" if canonical_status == "success" else "partial",
        "planner_summary": planner_summary,
        "leaf_count": len(nodes),
        "deferred_count": len(deferred_candidates),
        "category_counts": category_counts,
        "validation": "quality_gate",
    }
    return nodes, low_confidence_flags, quality_summary, deferred_candidates


def _normalize_quality_first_node(
    item: object,
    *,
    category: str,
    display_category_title: str,
    index: int,
    category_node_index: int,
    context_digest: str,
) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    raw_title = item.get("display_title") or item.get("exam_point") or item.get("title")
    if _looks_bad_quality_first_title(raw_title):
        return None
    display_title = _sanitize_display_text(raw_title, max_chars=120) or "待补充考点"
    exam_point = _sanitize_display_text(item.get("exam_point") or display_title, max_chars=160) or display_title
    if _looks_bad_quality_first_title(display_title) or _looks_bad_quality_first_title(exam_point):
        return None
    basis_type, basis_flags = _quality_first_basis_type(item.get("basis_type"), category=category)
    resume_signal = _sanitize_optional_text(item.get("resume_signal"), max_chars=240)
    jd_basis = _sanitize_optional_text(item.get("jd_basis"), max_chars=240)
    depth_goal = (
        _sanitize_display_text(item.get("depth_goal"), max_chars=120)
        or "补充该方向的关键原理、设计取舍和落地细节"
    )
    preparation_goal = (
        _sanitize_display_text(item.get("preparation_goal"), max_chars=600)
        or _default_preparation_goal(category, exam_point)
    )
    first_question = (
        _sanitize_display_text(item.get("first_question"), max_chars=120)
        or "请结合你的经历说明这个方向的设计思路和关键取舍。"
    )
    follow_up_focus = _sanitize_string_list(item.get("follow_up_focus"), limit=4)
    if not follow_up_focus:
        follow_up_focus = _default_follow_up_focus(category, exam_point)
    expected_answer_signals = _sanitize_string_list(item.get("expected_answer_signals"), limit=5)
    if not expected_answer_signals:
        expected_answer_signals = _default_expected_answer_signals(category)
    common_loss_risks = _sanitize_string_list(item.get("common_loss_risks"), limit=5)
    if not common_loss_risks:
        common_loss_risks = _default_common_loss_risks(category)
    evidence_refs = _sanitize_string_list(item.get("evidence_refs") or item.get("evidence_chunk_ids"), limit=8)
    evidence_notes = _sanitize_string_list(item.get("evidence_notes"), limit=8)
    low_confidence_flags = _sanitize_string_list(item.get("low_confidence_flags"), limit=8)
    low_confidence_flags.extend(basis_flags)
    node_code = _sanitize_display_text(item.get("node_code"), max_chars=20) or _default_node_code(
        category,
        category_node_index,
    )
    confidence_level = _enum_value(item.get("confidence_level"), _ALLOWED_CONFIDENCE_LEVELS, "medium")
    node_ref = truncate_text(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
    related_match_gaps = _sanitize_string_list(item.get("related_match_gaps"), limit=6)
    node = {
        "progress_node_ref": node_ref or _node_ref(context_digest, f"quality:{category}:{node_code}:{display_title}"),
        "node_code": node_code,
        "category": category,
        "display_category_title": display_category_title,
        "display_title": display_title,
        "exam_point": exam_point,
        "basis_type": basis_type,
        "resume_signal": resume_signal,
        "jd_basis": jd_basis,
        "depth_goal": depth_goal,
        "preparation_goal": preparation_goal,
        "first_question": first_question,
        "follow_up_focus": follow_up_focus,
        "expected_answer_signals": expected_answer_signals,
        "common_loss_risks": common_loss_risks,
        "evidence_refs": evidence_refs,
        "evidence_notes": evidence_notes,
        "confidence_level": confidence_level,
        "low_confidence_flags": low_confidence_flags,
        "title": display_title,
        "expected_capability": depth_goal,
        "children": [],
        "node_type": "project_deep_dive" if category == _RESUME_DEEP_DIVE else "job_gap",
        "interview_intent": preparation_goal,
        "interview_method": "technical_deep_dive" if category == _RESUME_DEEP_DIVE else "learning_plan",
        "follow_up_method": "technical_deep_dive" if category == _RESUME_DEEP_DIVE else "learning_plan",
        "attack_style": "technical_deep_dive" if category == _RESUME_DEEP_DIVE else "learning_plan",
        "difficulty_level": "advanced" if confidence_level == "high" else "intermediate",
        "priority": _bounded_int(item.get("priority"), lower=1, upper=999, fallback=index),
        "priority_reason": _sanitize_display_text(item.get("priority_reason"), max_chars=240)
        or "该节点具备岗位贴合和面试追问价值。",
        "related_job_requirements": _dedupe_strings([jd_basis], limit=3),
        "related_resume_evidence": _dedupe_strings([resume_signal], limit=3),
        "related_match_gaps": related_match_gaps,
        "missing_points": related_match_gaps,
        "recommended_first_question": first_question,
        "follow_up_directions": follow_up_focus,
        "red_flags": common_loss_risks,
        "evidence_chunk_ids": evidence_refs,
        "evidence_bindings": [],
        "grounding_status": "partially_grounded" if evidence_refs else "weakly_grounded",
    }
    return _sanitize_node_display_fields(node)


def _quality_first_basis_type(value: object, *, category: str) -> tuple[str, list[str]]:
    fallback = "resume_signal" if category == _RESUME_DEEP_DIVE else "jd_requirement"
    text = truncate_text(value, max_chars=80)
    if text in _ALLOWED_BASIS_TYPES:
        return text, []
    return fallback, ["basis_type_normalized"]


def _quality_first_apply_quality_gates(
    nodes: list[dict[str, Any]],
    *,
    context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    kept: list[dict[str, Any]] = []
    deferred_candidates: list[dict[str, Any]] = []
    flags: list[str] = []
    low_evidence_jd_nodes = 0

    for node in nodes:
        defer_reason, defer_flag = _quality_first_defer_reason(node, context=context)
        if not defer_reason and _quality_first_is_low_evidence_jd_gap(node):
            low_evidence_jd_nodes += 1
            if low_evidence_jd_nodes > 2:
                defer_reason = "低证据 JD gap 节点已超过主树保留上限，延后作为补充核验项。"
                defer_flag = "quality_first_jd_low_evidence_deferred"
        if defer_reason:
            deferred_candidates.append(_quality_first_deferred_candidate_from_node(node, reason=defer_reason))
            flags.append(defer_flag)
            continue
        kept.append(node)

    if len(kept) > _QUALITY_FIRST_MAX_PRIMARY_NODES:
        flags.extend(["quota_filling_risk", "quality_first_primary_nodes_trimmed"])
        ordered = sorted(kept, key=lambda item: _quality_first_node_sort_key(item, context=context))
        kept = ordered[:_QUALITY_FIRST_MAX_PRIMARY_NODES]
        for node in ordered[_QUALITY_FIRST_MAX_PRIMARY_NODES:]:
            deferred_candidates.append(
                _quality_first_deferred_candidate_from_node(
                    node,
                    reason="主树超过 9 个节点，按优先级、证据和连续追问价值延后。",
                )
            )

    return kept, deferred_candidates, _dedupe_strings(flags, limit=20)


def _quality_first_defer_reason(node: dict[str, Any], *, context: dict[str, Any]) -> tuple[str | None, str]:
    if _quality_first_cost_without_context(node, context=context):
        return "材料中缺少明确成本或资源优化证据，不进入主训练路径。", "quality_first_cost_control_deferred"
    if _quality_first_looks_checklist_node(node) and _quality_first_node_low_support(node):
        return "该节点更像低证据 JD checklist，适合作为补充核验项。", "quality_first_checklist_deferred"
    if _quality_first_looks_generic_node(node) and _quality_first_node_low_support(node):
        return "节点标题或考点过于泛化，缺少主训练路径价值。", "quality_first_generic_node_deferred"
    return None, ""


def _quality_first_is_low_evidence_jd_gap(node: dict[str, Any]) -> bool:
    return (
        node.get("category") == _JD_GAP_LEARNING
        and node.get("confidence_level") == "low"
        and not _quality_first_evidence_refs(node)
    )


def _quality_first_node_low_support(node: dict[str, Any]) -> bool:
    return node.get("confidence_level") == "low" or not _quality_first_evidence_refs(node)


def _quality_first_looks_checklist_node(node: dict[str, Any]) -> bool:
    text = _quality_first_node_text(node)
    return any(_quality_first_contains(text, term) for term in _QUALITY_FIRST_CHECKLIST_TERMS)


def _quality_first_looks_generic_node(node: dict[str, Any]) -> bool:
    text = _quality_first_node_text(node)
    if any(term in text for term in _QUALITY_FIRST_GENERIC_TERMS):
        return True
    title = str(node.get("display_title") or node.get("title") or "")
    exam_point = str(node.get("exam_point") or "")
    return len(title) <= 4 or len(exam_point) <= 4


def _quality_first_cost_without_context(node: dict[str, Any], *, context: dict[str, Any]) -> bool:
    node_text = _quality_first_node_text(node)
    if not any(_quality_first_contains(node_text, term) for term in _QUALITY_FIRST_COST_TERMS):
        return False
    context_text = _quality_first_context_text(context)
    return not any(_quality_first_contains(context_text, term) for term in _QUALITY_FIRST_COST_TERMS)


def _quality_first_node_sort_key(node: dict[str, Any], *, context: dict[str, Any]) -> tuple[int, int, int, int, int]:
    text = _quality_first_node_text(node)
    keywords = _quality_first_priority_keywords(context)
    matches_focus = any(keyword and keyword in text for keyword in keywords)
    evidence_count = len(_quality_first_evidence_refs(node))
    confidence_rank = {"high": 0, "medium": 1, "low": 2}.get(str(node.get("confidence_level") or ""), 2)
    category = node.get("category")
    basis_type = node.get("basis_type")
    if category == _RESUME_DEEP_DIVE and evidence_count and confidence_rank == 0:
        category_rank = 0
    elif category == _RESUME_DEEP_DIVE and evidence_count:
        category_rank = 1
    elif category == _JD_GAP_LEARNING and basis_type in {"match_gap", "mixed"}:
        category_rank = 2
    elif category == _JD_GAP_LEARNING and evidence_count:
        category_rank = 3
    else:
        category_rank = 4
    return (
        category_rank,
        0 if matches_focus else 1,
        confidence_rank,
        0 if evidence_count else 1,
        _bounded_int(node.get("priority"), lower=1, upper=999, fallback=999),
    )


def _quality_first_deferred_candidate_from_node(node: dict[str, Any], *, reason: str) -> dict[str, Any]:
    return {
        "display_title": _sanitize_display_text(node.get("display_title") or node.get("title"), max_chars=120)
        or "待补充候选项",
        "category": _category_value(node),
        "reason": _sanitize_display_text(reason, max_chars=240) or "低优先级候选项，暂不进入主训练路径。",
        "basis_type": _enum_value(node.get("basis_type"), _ALLOWED_BASIS_TYPES, "jd_requirement"),
        "evidence_refs": _quality_first_evidence_refs(node),
        "confidence_level": _enum_value(node.get("confidence_level"), _ALLOWED_CONFIDENCE_LEVELS, "low"),
        "suggested_trigger": "主路径完成后，或用户主动要求补充核验该方向时再启用。",
    }


def _normalize_quality_first_deferred_candidates(
    value: object,
    *,
    context_digest: str,
) -> list[dict[str, Any]]:
    del context_digest
    if not isinstance(value, list):
        return []
    candidates: list[dict[str, Any]] = []
    for item in value[:20]:
        if not isinstance(item, dict):
            continue
        title = _sanitize_display_text(item.get("display_title") or item.get("title"), max_chars=120)
        if not title:
            continue
        category = truncate_text(item.get("category"), max_chars=80)
        if category not in _ALLOWED_CATEGORIES:
            category = _JD_GAP_LEARNING
        basis_type, _flags = _quality_first_basis_type(item.get("basis_type"), category=category)
        candidates.append(
            {
                "display_title": title,
                "category": category,
                "reason": _sanitize_display_text(item.get("reason"), max_chars=240)
                or "低优先级候选项，暂不进入主训练路径。",
                "basis_type": basis_type,
                "evidence_refs": _sanitize_string_list(item.get("evidence_refs") or item.get("evidence_chunk_ids"), limit=8),
                "confidence_level": _enum_value(item.get("confidence_level"), _ALLOWED_CONFIDENCE_LEVELS, "low"),
                "suggested_trigger": _sanitize_display_text(item.get("suggested_trigger"), max_chars=160)
                or "主路径完成后，或用户主动要求补充核验该方向时再启用。",
            }
        )
    return candidates


def _dedupe_quality_first_deferred_candidates(
    candidates: list[dict[str, Any]],
    *,
    main_titles: set[str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        title_key = _normalize_label_for_compare(candidate.get("display_title"))
        if not title_key or title_key in seen or title_key in main_titles:
            continue
        seen.add(title_key)
        result.append(candidate)
        if len(result) >= 20:
            break
    return result


def _quality_first_node_text(node: dict[str, Any]) -> str:
    return " ".join(
        str(node.get(field) or "")
        for field in (
            "display_title",
            "title",
            "exam_point",
            "resume_signal",
            "jd_basis",
            "depth_goal",
            "priority_reason",
        )
    )


def _quality_first_context_text(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(_quality_first_context_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_quality_first_context_text(item) for item in value)
    return str(value or "")


def _quality_first_evidence_refs(node: dict[str, Any]) -> list[str]:
    return _dedupe_strings(
        _string_list(node.get("evidence_refs"), limit=8) + _string_list(node.get("evidence_chunk_ids"), limit=8),
        limit=8,
    )


def _quality_first_contains(text: str, term: str) -> bool:
    if term.isascii():
        return term.lower() in text.lower()
    return term in text


def _quality_first_initial_state_from_nodes(
    nodes: list[dict[str, Any]],
    *,
    context: dict[str, Any],
) -> dict[str, Any]:
    flat_nodes = _flatten_v2_nodes(nodes)
    node_states = [
        {
            "progress_node_ref": node["progress_node_ref"],
            "status": "pending",
            "completed_questions_count": 0,
            "latest_feedback_summary": None,
        }
        for node in flat_nodes
    ]
    current_priority = _quality_first_priority(flat_nodes, context=context)
    return {
        "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_READY if flat_nodes and current_priority else PROGRESS_TREE_STATUS_FAILED,
        "node_states": node_states,
        "current_priority": current_priority,
        "updated_from_turns_count": 0,
        "progress": {"progress_percent": 0},
    }


def _quality_first_priority(
    flat_nodes: list[dict[str, Any]],
    *,
    context: dict[str, Any],
) -> dict[str, Any] | None:
    if not flat_nodes:
        return None
    node = sorted(flat_nodes, key=lambda item: _quality_first_node_sort_key(item, context=context))[0]
    return {
        "progress_node_ref": node["progress_node_ref"],
        "title": _sanitize_display_text(node["title"], max_chars=120) or "待补充考点",
        "expected_capability": _sanitize_display_text(
            node["expected_capability"],
            max_chars=600,
        )
        or "补充该方向的关键原理、设计取舍和落地细节",
        "priority_reason": _sanitize_display_text(node.get("priority_reason"), max_chars=600)
        or "优先从简历中置信度较高且可连续追问的节点开始。",
    }


def _quality_first_priority_keywords(context: dict[str, Any]) -> list[str]:
    match_context = context.get("match_context")
    if not isinstance(match_context, dict):
        return []
    values: list[str] = []
    for field in ("interview_focus", "missing_points", "improvement_points"):
        values.extend(_string_list(match_context.get(field), limit=6))
    return [value for value in values if len(value) >= 2][:12]


def _quality_first_payload_failure_reason(payload: dict[str, Any]) -> str:
    _canonical_status, _status_warnings, status_errors = normalize_structured_status(payload.get("status"))
    if status_errors:
        if any(error.code == "failed" for error in status_errors):
            return "quality_first_status_failed"
        return "quality_first_status_invalid"

    categories = payload.get("menu_categories")
    if not isinstance(categories, list):
        return "quality_first_menu_categories_missing"

    valid_categories = [
        item
        for item in categories
        if isinstance(item, dict) and str(item.get("category") or "").strip() in _ALLOWED_CATEGORIES
    ]
    if not valid_categories:
        return "quality_first_schema_invalid"

    present_categories = {str(item.get("category") or "").strip() for item in valid_categories}
    if not {_RESUME_DEEP_DIVE, _JD_GAP_LEARNING}.issubset(present_categories):
        return "quality_first_category_missing"

    has_raw_nodes = any(isinstance(item.get("nodes"), list) and item.get("nodes") for item in valid_categories)
    if not has_raw_nodes:
        return "quality_first_no_usable_nodes"
    return "quality_first_schema_invalid"


def _quality_first_validation_errors(payload: dict[str, Any], *, reason: str) -> list[dict[str, str]]:
    _canonical_status, _status_warnings, status_errors = normalize_structured_status(payload.get("status"))
    if status_errors:
        return structured_validation_errors_to_dicts(status_errors)

    categories = payload.get("menu_categories")
    if not isinstance(categories, list):
        return [
            {
                "field": "menu_categories",
                "code": "missing_or_invalid",
                "reason": "menu_categories must be a list.",
            }
        ]

    errors: list[dict[str, str]] = []
    present_categories: set[str] = set()
    for index, item in enumerate(categories[:12]):
        if not isinstance(item, dict):
            errors.append(
                {
                    "field": f"menu_categories[{index}]",
                    "code": "invalid_type",
                    "reason": "Category item must be an object.",
                }
            )
            continue
        category = str(item.get("category") or "").strip()
        if category not in _ALLOWED_CATEGORIES:
            errors.append(
                {
                    "field": f"menu_categories[{index}].category",
                    "code": "unsupported",
                    "reason": "Category is not allowed.",
                }
            )
            continue
        present_categories.add(category)
        if not isinstance(item.get("nodes"), list):
            errors.append(
                {
                    "field": f"menu_categories[{index}].nodes",
                    "code": "missing_or_invalid",
                    "reason": "Category nodes must be a list.",
                }
            )

    missing_categories = [_RESUME_DEEP_DIVE, _JD_GAP_LEARNING]
    missing_categories = [category for category in missing_categories if category not in present_categories]
    if missing_categories:
        errors.append(
            {
                "field": "menu_categories",
                "code": "missing_required_category",
                "reason": ",".join(missing_categories),
            }
        )
    if reason == "quality_first_no_usable_nodes":
        errors.append(
            {
                "field": "menu_categories.nodes",
                "code": "no_usable_nodes",
                "reason": "No usable menu nodes were returned.",
            }
        )
    if reason == "quality_first_all_nodes_deferred":
        errors.append(
            {
                "field": "menu_categories.nodes",
                "code": "all_deferred",
                "reason": "All returned menu nodes were deferred by quality policy.",
            }
        )
    if not errors:
        errors.append(
            {
                "field": "menu_categories",
                "code": "schema_invalid",
                "reason": "Quality-first menu payload failed validation.",
            }
        )
    return errors[:8]


def _quality_first_failed_artifacts(
    context: dict[str, Any],
    *,
    reason: str,
    validation_errors: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    low_confidence_flags = _dedupe_strings([reason], limit=20)
    metadata = {
        "pipeline_status": "failed",
        "generation_mode": "quality_first",
        "planner_schema_id": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
        "input_context_mode": "full_resume_full_job",
        "task_types": [POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE],
        "prompt_versions": [POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION],
        "low_confidence_flags": low_confidence_flags,
        "failure_reason": reason,
        "validation_errors": validation_errors or [],
        "quality_summary": {
            "status": "failed",
            "leaf_count": 0,
            "validation": "failed",
        },
    }
    plan = {
        "schema_id": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_FAILED,
        "context_digest": context["content_digest"],
        "nodes": [],
        "failure_reason": reason,
        "v2_metadata": metadata,
    }
    return {
        "status": PROGRESS_TREE_STATUS_FAILED,
        "progress_tree_plan": plan,
        "progress_tree_state": _empty_state(PROGRESS_TREE_STATUS_FAILED),
        "progress_percent": 0,
    }


def _quality_first_insufficient_artifacts(context: dict[str, Any]) -> dict[str, Any]:
    plan = {
        "schema_id": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "context_digest": context["content_digest"],
        "nodes": [],
        "v2_metadata": {
            "pipeline_status": "partial",
            "generation_mode": "quality_first",
            "planner_schema_id": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
            "input_context_mode": "full_resume_full_job",
            "task_types": [POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE],
            "prompt_versions": [POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION],
            "low_confidence_flags": ["insufficient_context"],
            "failure_reason": "insufficient_context",
            "quality_summary": {"status": "insufficient_context"},
        },
    }
    return {
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "progress_tree_plan": plan,
        "progress_tree_state": _empty_state(PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT),
        "progress_percent": 0,
    }


def _looks_bad_quality_first_title(value: object) -> bool:
    text = truncate_text(value, max_chars=160) or ""
    normalized = _normalize_label_for_compare(text)
    bad_exact = {
        "1能力补齐",
        "能力补齐",
        "类别一",
        "类别二",
        "项目经历深挖与贡献边界验证",
    }
    bad_normalized = {_normalize_label_for_compare(item) for item in bad_exact}
    if normalized in bad_normalized:
        return True
    if text.startswith(("面向 xxx 构建 xxx", "针对 xxx 问题", "5年以上 xxx")):
        return True
    if _looks_abstract_title(text):
        return True
    return False


def _empty_state(status: str) -> dict[str, Any]:
    return {
        "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
        "status": status,
        "node_states": [],
        "current_priority": None,
        "updated_from_turns_count": 0,
        "progress": {"progress_percent": 0},
    }


def _normalize_label_for_compare(value: object) -> str:
    text = truncate_text(value, max_chars=1000) or ""
    return "".join(ch.lower() for ch in text if ch.isalnum())


def _looks_abstract_title(title: str) -> bool:
    sanitized = _sanitize_display_text(title, max_chars=160)
    return any(fragment == sanitized or fragment in sanitized for fragment in _ABSTRACT_TITLE_FRAGMENTS)


def _category_value(item: dict[str, Any]) -> str:
    category = truncate_text(item.get("category"), max_chars=80)
    if category in _ALLOWED_CATEGORIES:
        return category
    basis_type = truncate_text(item.get("basis_type"), max_chars=80)
    node_type = truncate_text(item.get("node_type"), max_chars=80)
    if basis_type in {"jd_requirement", "match_gap"} or node_type == "job_gap":
        return _JD_GAP_LEARNING
    if item.get("jd_basis") and not item.get("resume_signal"):
        return _JD_GAP_LEARNING
    return _RESUME_DEEP_DIVE


def _default_node_code(category: str, index: int) -> str:
    prefix = "A" if category == _JD_GAP_LEARNING else "D"
    return f"{prefix}{index}"


def _default_preparation_goal(category: str, exam_point: str) -> str:
    if category == _JD_GAP_LEARNING:
        return f"把「{exam_point}」从 JD 关键词转成可学习、可表达、可验证的准备项。"
    return f"把「{exam_point}」从简历线索转成可连续追问的项目表达。"


def _default_follow_up_focus(category: str, exam_point: str) -> list[str]:
    if category == _JD_GAP_LEARNING:
        return [
            f"继续追问「{exam_point}」的核心原理",
            "继续追问与既有项目的可迁移经验",
            "继续追问学习补齐和验证计划",
        ]
    return [
        f"继续追问「{exam_point}」的个人负责范围",
        "继续追问关键取舍和替代方案",
        "继续追问结果验证和异常处理",
    ]


def _default_expected_answer_signals(category: str) -> list[str]:
    if category == _JD_GAP_LEARNING:
        return ["能解释原理", "能说明适用边界", "能诚实区分已实践和待补齐部分"]
    return ["能说明真实场景", "能讲清个人动作", "能提供结果或验证证据"]


def _default_common_loss_risks(category: str) -> list[str]:
    if category == _JD_GAP_LEARNING:
        return ["只背关键词", "把学习项说成已主导经验", "补齐计划不具体"]
    return ["只罗列技术栈", "个人贡献边界不清", "缺少结果验证"]


def _first_string(value: object) -> str | None:
    strings = _string_list(value, limit=1)
    return strings[0] if strings else None


_DISPLAY_FIELDS_TO_SANITIZE = (
    "title",
    "expected_capability",
    "interview_intent",
    "priority_reason",
    "display_category_title",
    "display_title",
    "exam_point",
    "resume_signal",
    "jd_basis",
    "depth_goal",
    "preparation_goal",
    "first_question",
    "follow_up_focus",
    "expected_answer_signals",
    "common_loss_risks",
    "related_job_requirements",
    "related_resume_evidence",
    "related_match_gaps",
    "missing_points",
    "red_flags",
    "recommended_first_question",
    "follow_up_directions",
)


def _sanitize_node_display_fields(node: dict[str, Any]) -> dict[str, Any]:
    sanitized = {**node}
    for field in _DISPLAY_FIELDS_TO_SANITIZE:
        value = sanitized.get(field)
        if isinstance(value, str) or value is None:
            sanitized[field] = _sanitize_optional_text(value, max_chars=600)
        elif isinstance(value, list):
            sanitized[field] = [_sanitize_display_text(item, max_chars=600) for item in value if _sanitize_display_text(item, max_chars=600)]
    sanitized["children"] = [
        _sanitize_node_display_fields(child)
        for child in sanitized.get("children", [])
        if isinstance(child, dict)
    ]
    return sanitized


def _display_text_values(node: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for field in _DISPLAY_FIELDS_TO_SANITIZE:
        value = node.get(field)
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            values.extend(item for item in value if isinstance(item, str))
    return values


def _contains_forbidden_display_terms(values: list[str]) -> bool:
    return any(term in value for value in values for term in _FORBIDDEN_DISPLAY_TERMS)


def _sanitize_optional_text(value: object, *, max_chars: int) -> str | None:
    text = _sanitize_display_text(value, max_chars=max_chars)
    return text or None


def _sanitize_display_text(value: object, *, max_chars: int) -> str:
    text = truncate_text(value, max_chars=max_chars * 2) or ""
    for term, replacement in _FORBIDDEN_DISPLAY_REPLACEMENTS:
        text = text.replace(term, replacement)
    for term in _FORBIDDEN_DISPLAY_TERMS:
        text = text.replace(term, "")
    return truncate_text(text, max_chars=max_chars) or ""


def _sanitize_string_list(value: object, *, limit: int) -> list[str]:
    result: list[str] = []
    for item in _string_list(value, limit=limit * 2):
        text = _sanitize_display_text(item, max_chars=480)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _input_refs(context: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        ref
        for ref in (
            f"polish_session:{context['session']['session_id']}",
            f"job_version:{context['job_snapshot']['job_version_id']}",
            f"resume_version:{context['resume_snapshot']['resume_version_id']}",
        )
        if ref
    )


def _flatten_v2_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in nodes:
        result.append(node)
        result.extend(_flatten_v2_nodes(node.get("children", [])))
    return result


def _string_list(value: object, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = truncate_text(item, max_chars=480)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _dedupe_strings(values: list[str], *, limit: int) -> list[str]:
    result: list[str] = []
    for value in values:
        text = truncate_text(value, max_chars=240)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _enum_value(value: object, allowed_values: set[str], fallback: str) -> str:
    text = truncate_text(value, max_chars=80)
    return text if text in allowed_values else fallback


def _bounded_int(value: object, *, lower: int, upper: int, fallback: int) -> int:
    if isinstance(value, bool):
        return fallback
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(lower, min(upper, parsed))


def _node_ref(context_digest: str, seed: str) -> str:
    return f"progress_v2_{sha256(f'{context_digest}:{seed}'.encode('utf-8')).hexdigest()[:16]}"
