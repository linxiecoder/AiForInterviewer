"""LLM-backed progress tree generation and state refresh."""

from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from app.application.llm.agent_io import (
    LegacyAgentOutputEnvelope,
)
from app.application.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.application.llm.ports import LlmTransport
from app.application.llm.structured_output import (
    filter_untrusted_structured_metadata,
    normalize_structured_status,
    structured_validation_errors_to_dicts,
)
from app.application.llm.provider_boundary import ProviderRequestValidationError, build_validated_transport_request
from app.application.polish.progress_context import has_sufficient_progress_context, truncate_text
from app.application.polish.progress_evidence import build_progress_prompt_context
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
    POLISH_PROGRESS_TREE_CONTRACT_IDS,
    POLISH_PROGRESS_TREE_STATE_CONTRACT_IDS,
    POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
    build_progress_quality_first_menu_prompt,
    build_progress_tree_state_refresh_prompt,
)


PROGRESS_TREE_STATUS_READY = "ready"
PROGRESS_TREE_STATUS_FAILED = "failed"
PROGRESS_TREE_STATUS_REFRESH_FAILED = "refresh_failed"
PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT = "insufficient_context"
PROGRESS_TREE_STATUS_PENDING = "pending"
PROGRESS_TREE_STATUS_GENERATING = "generating"
PENDING_FEEDBACK_TEXT = "本轮反馈尚未生成"

_PROGRESS_QUALITY_FIRST_PROVIDER_REQUEST_TOP_LEVEL_KEYS = frozenset(
    {
        "source_digest",
        "task_type",
        "prompt_version",
        "schema_id",
        "schema_version",
        "prompt",
        "context",
        "output_schema",
    }
)
_PROGRESS_TREE_STATE_PROVIDER_REQUEST_TOP_LEVEL_KEYS = frozenset(
    {
        "source_digest",
        "task_type",
        "prompt_version",
        "schema_id",
        "schema_version",
        "prompt",
        "context",
        "selected_evidence_chunks",
        "dropped_context_summary",
        "match_context_summary",
        "turns_summary",
        "existing_progress_tree_plan",
        "existing_progress_tree_state",
        "output_schema",
    }
)

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
_QUALITY_FIRST_COST_NODE_TERMS = (
    "成本控制",
    "成本优化",
    "成本治理",
    "降本",
    "资源优化",
    "资源利用率",
    "预算控制",
    "预算优化",
    "预算治理",
    "FinOps",
)

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
_TEXT_LIST_SEPARATOR_RE = re.compile(r"[；;，,、\n|]+")


class PolishProgressTreeLlmService:
    """Call the configured LLM transport and normalize progress tree outputs."""

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
            request = build_validated_transport_request(
                contract_ids=POLISH_PROGRESS_TREE_CONTRACT_IDS,
                task_type=POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
                input_refs=_input_refs(context),
                evidence_bundle=build_progress_quality_first_menu_prompt(context),
                required_evidence_keys=_PROGRESS_QUALITY_FIRST_PROVIDER_REQUEST_TOP_LEVEL_KEYS,
                allowed_evidence_keys=_PROGRESS_QUALITY_FIRST_PROVIDER_REQUEST_TOP_LEVEL_KEYS,
            )
        except ProviderRequestValidationError as exc:
            return _quality_first_failed_artifacts(
                context,
                reason="provider_request_validation_failed",
                validation_errors=_provider_request_validation_errors(exc),
            )

        try:
            result = self._transport.generate(request)
        except TimeoutError:
            return _quality_first_failed_artifacts(context, reason="provider_timeout")
        except LlmTransportConfigurationError:
            return _quality_first_failed_artifacts(context, reason="provider_unavailable")
        except LlmTransportUnavailableError as exc:
            return _quality_first_failed_artifacts(context, reason=_provider_unavailable_failure_reason(exc))
        except LlmTransportResponseError as exc:
            return _quality_first_failed_artifacts(context, reason=_provider_response_failure_reason(exc))

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
        nodes, low_confidence_flags, quality_summary, deferred_candidates, evidence_ref_validation = normalized
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
            "evidence_ref_validation": evidence_ref_validation,
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

    def refresh_state(
        self,
        *,
        context: dict[str, Any],
        existing_plan: dict[str, Any],
        existing_state: dict[str, Any],
    ) -> dict[str, Any]:
        if existing_plan.get("status") != PROGRESS_TREE_STATUS_READY:
            if not has_sufficient_progress_context(context):
                return _insufficient_artifacts(context)
            return {
                "status": existing_plan.get("status") or PROGRESS_TREE_STATUS_FAILED,
                "progress_tree_plan": existing_plan,
                "progress_tree_state": existing_state,
                "progress_percent": _progress_percent(existing_state),
            }
        if existing_plan.get("schema_id") == POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID:
            if _state_matches_plan(existing_state, existing_plan):
                state = {
                    **existing_state,
                    "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
                    "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
                    "prompt_version": POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
                    "status": PROGRESS_TREE_STATUS_READY,
                }
            else:
                state = _initial_state_fallback(
                    existing_plan,
                    prompt_version=POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
                    failure_reason="v2_local_state_refresh",
                )
            state = _apply_turn_progress_to_state(state, context, existing_plan=existing_plan)
            return {
                "status": PROGRESS_TREE_STATUS_READY,
                "progress_tree_plan": existing_plan,
                "progress_tree_state": state,
                "progress_percent": _progress_percent(state),
            }
        if self._transport is None:
            return _refresh_failed_artifacts(
                existing_plan,
                existing_state,
                reason="llm_transport_missing",
            )

        try:
            request = build_validated_transport_request(
                contract_ids=POLISH_PROGRESS_TREE_STATE_CONTRACT_IDS,
                task_type="polish_progress_tree_state",
                input_refs=_input_refs(context),
                evidence_bundle=build_progress_tree_state_refresh_prompt(
                    context=context,
                    existing_plan=existing_plan,
                    existing_state=existing_state,
                ),
                required_evidence_keys=_PROGRESS_TREE_STATE_PROVIDER_REQUEST_TOP_LEVEL_KEYS,
                allowed_evidence_keys=_PROGRESS_TREE_STATE_PROVIDER_REQUEST_TOP_LEVEL_KEYS,
            )
        except ProviderRequestValidationError:
            return _refresh_failed_artifacts(
                existing_plan,
                existing_state,
                reason="provider_request_validation_failed",
            )

        try:
            result = self._transport.generate(request)
        except (LlmTransportConfigurationError, LlmTransportUnavailableError, LlmTransportResponseError):
            return _refresh_failed_artifacts(
                existing_plan,
                existing_state,
                reason="llm_transport_failed",
            )

        state_payload = result.result.get("progress_tree_state") or result.result.get("state")
        if not isinstance(state_payload, dict):
            return _refresh_failed_artifacts(
                existing_plan,
                existing_state,
                reason="llm_state_invalid",
            )
        normalized_state = _normalize_state(
            state_payload,
            existing_plan=existing_plan,
            allow_refresh_failed=True,
            prompt_version=_metadata_value(
                result.result,
                state_payload,
                "prompt_version",
                POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
            ),
            schema_id=_metadata_value(
                result.result,
                state_payload,
                "schema_id",
                POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
            ),
            schema_version=_metadata_value(
                result.result,
                state_payload,
                "schema_version",
                POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
            ),
        )
        if normalized_state["status"] != PROGRESS_TREE_STATUS_READY:
            return _refresh_failed_artifacts(
                existing_plan,
                existing_state,
                reason="llm_state_invalid",
            )
        normalized_state = _apply_turn_progress_to_state(
            normalized_state,
            context,
            existing_plan=existing_plan,
        )
        return {
            "status": PROGRESS_TREE_STATUS_READY,
            "progress_tree_plan": existing_plan,
            "progress_tree_state": normalized_state,
            "progress_percent": _progress_percent(normalized_state),
        }


# Quality-first initial generation helpers. These live beside PolishProgressTreeLlmService so
# initial generation and state refresh share one canonical progress-tree implementation.


def _normalize_quality_first_menu_payload(
    payload: dict[str, Any],
    *,
    context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any], list[dict[str, Any]], dict[str, Any]] | None:
    envelope = _quality_first_menu_payload_envelope(payload, context=context)
    if not envelope.succeeded:
        return None
    normalized = envelope.payload
    return (
        normalized["nodes"],
        normalized["low_confidence_flags"],
        normalized["quality_summary"],
        normalized["deferred_candidates"],
        normalized["evidence_ref_validation"],
    )


def _quality_first_menu_payload_envelope(
    payload: dict[str, Any],
    *,
    context: dict[str, Any],
) -> LegacyAgentOutputEnvelope:
    def failed(*validation_errors: str) -> LegacyAgentOutputEnvelope:
        return LegacyAgentOutputEnvelope(
            task_type=POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
            schema_id=POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
            schema_version=POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
            prompt_version=POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
            status=PROGRESS_TREE_STATUS_FAILED,
            validation_errors=validation_errors or ("quality_first_payload_invalid",),
        )

    canonical_status, status_warnings, status_errors = normalize_structured_status(payload.get("status"))
    if status_errors or canonical_status not in {"success", "partial"}:
        return failed(*(f"{error.field}_{error.code}" for error in status_errors))
    categories = payload.get("menu_categories")
    if not isinstance(categories, list):
        return failed("menu_categories_invalid")

    nodes: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    evidence_chunks_by_ref = _quality_first_evidence_chunks_by_ref(context)
    allowed_evidence_refs = set(evidence_chunks_by_ref)
    low_confidence_flags = _normalize_text_list(payload.get("low_confidence_flags"), limit=20)
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
        display_category_title = _DISPLAY_CATEGORY_TITLES[category]
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
                allowed_evidence_refs=allowed_evidence_refs,
                evidence_chunks_by_ref=evidence_chunks_by_ref,
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
        return failed("menu_categories_no_valid_category")
    if raw_node_count >= 10:
        low_confidence_flags.append("quota_filling_risk")

    nodes, gate_deferred_candidates, gate_flags = _quality_first_apply_quality_gates(nodes, context=context)
    gate_deferred_count = len(gate_deferred_candidates)
    deferred_candidates.extend(gate_deferred_candidates)
    low_confidence_flags.extend(gate_flags)
    if gate_deferred_count:
        low_confidence_flags.append("deferred_main_quota_candidate_count")
    nodes = sorted(nodes, key=lambda node: _quality_first_node_sort_key(node, context=context))

    category_counts = {
        _RESUME_DEEP_DIVE: sum(1 for node in nodes if node.get("category") == _RESUME_DEEP_DIVE),
        _JD_GAP_LEARNING: sum(1 for node in nodes if node.get("category") == _JD_GAP_LEARNING),
    }
    if nodes and len(nodes) < _QUALITY_FIRST_LOW_NODE_COUNT:
        low_confidence_flags.append("quality_first_low_primary_node_count")
        low_confidence_flags.append("primary_node_count_after_defer_below_target")
    elif nodes and len(nodes) < _QUALITY_FIRST_TARGET_MIN_PRIMARY_NODES:
        low_confidence_flags.append("quality_first_primary_nodes_below_target")
        low_confidence_flags.append("primary_node_count_after_defer_below_target")
    if nodes and category_counts[_RESUME_DEEP_DIVE] == 0:
        low_confidence_flags.append("quality_first_resume_deep_dive_missing")
    if nodes and category_counts[_JD_GAP_LEARNING] == 0:
        low_confidence_flags.append("quality_first_jd_gap_learning_missing")
    deferred_candidates = _dedupe_quality_first_deferred_candidates(
        deferred_candidates,
        main_titles={_normalize_label_for_compare(node["display_title"]) for node in nodes},
    )

    planner_summary = _sanitize_display_text(payload.get("planner_summary"), max_chars=120)
    below_target_after_defer = bool(nodes and len(nodes) < _QUALITY_FIRST_TARGET_MIN_PRIMARY_NODES)
    quality_summary = {
        "status": "partial" if canonical_status == "partial" or below_target_after_defer else "ready",
        "planner_summary": planner_summary,
        "leaf_count": len(nodes),
        "deferred_count": len(deferred_candidates),
        "primary_node_count_after_defer": len(nodes),
        "target_primary_node_count_min": _QUALITY_FIRST_TARGET_MIN_PRIMARY_NODES,
        "deferred_main_quota_candidate_count": gate_deferred_count,
        "category_counts": category_counts,
        "validation": "quality_gate",
    }
    evidence_ref_validation = _quality_first_evidence_ref_validation_summary(nodes, allowed_evidence_refs)
    return LegacyAgentOutputEnvelope(
        task_type=POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
        schema_id=POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
        schema_version=POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
        prompt_version=POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
        status=quality_summary["status"],
        payload={
            "nodes": nodes,
            "low_confidence_flags": low_confidence_flags,
            "quality_summary": quality_summary,
            "deferred_candidates": deferred_candidates,
            "evidence_ref_validation": evidence_ref_validation,
        },
        evidence_refs=tuple(
            _dedupe_strings(
                [
                    evidence_ref
                    for node in _flatten_progress_nodes(nodes)
                    for evidence_ref in _quality_first_evidence_chunk_ids(node)
                ],
                limit=50,
            )
        ),
    )


def _normalize_quality_first_node(
    item: object,
    *,
    category: str,
    display_category_title: str,
    index: int,
    category_node_index: int,
    context_digest: str,
    allowed_evidence_refs: set[str],
    evidence_chunks_by_ref: dict[str, dict[str, Any]],
    depth: int = 0,
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
    raw_jd_basis = item.get("jd_basis")
    if isinstance(raw_jd_basis, list):
        jd_basis_items = _sanitize_string_list(raw_jd_basis, limit=6)
        jd_basis = _sanitize_display_text("；".join(jd_basis_items), max_chars=240) or None
    else:
        jd_basis = _sanitize_optional_text(raw_jd_basis, max_chars=240)
        jd_basis_items = [jd_basis] if jd_basis else []
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
    follow_up_focus = _normalize_text_list(item.get("follow_up_focus"), limit=3)
    if not follow_up_focus:
        follow_up_focus = _default_follow_up_focus(category, exam_point)
    expected_answer_signals = _normalize_text_list(item.get("expected_answer_signals"), limit=5)
    if not expected_answer_signals:
        expected_answer_signals = _default_expected_answer_signals(category)
    common_loss_risks = _normalize_text_list(item.get("common_loss_risks"), limit=5)
    if not common_loss_risks:
        common_loss_risks = _default_common_loss_risks(category)
    evidence_refs = _dedupe_strings(
        _sanitize_string_list(item.get("evidence_refs"), limit=8)
        + _sanitize_string_list(item.get("evidence_chunk_ids"), limit=8),
        limit=8,
    )
    stable_evidence_refs = [ref for ref in evidence_refs if ref in allowed_evidence_refs]
    augmented_evidence_refs, evidence_bindings = _quality_first_resume_evidence_augmentations(
        item,
        category=category,
        display_title=display_title,
        exam_point=exam_point,
        resume_signal=resume_signal,
        follow_up_focus=follow_up_focus,
        stable_evidence_refs=stable_evidence_refs,
        evidence_chunks_by_ref=evidence_chunks_by_ref,
    )
    stable_evidence_refs = _dedupe_strings(stable_evidence_refs + augmented_evidence_refs, limit=8)
    source_hints = [ref for ref in evidence_refs if ref not in allowed_evidence_refs]
    evidence_notes = _normalize_text_list(item.get("evidence_notes"), limit=8)
    evidence_notes = _dedupe_strings(evidence_notes + source_hints, limit=8)
    low_confidence_flags = _normalize_text_list(item.get("low_confidence_flags"), limit=8)
    low_confidence_flags.extend(basis_flags)
    if source_hints:
        low_confidence_flags.append("quality_first_evidence_ref_not_allowed")
    low_confidence_flags = _dedupe_strings(low_confidence_flags, limit=8)
    node_code = _sanitize_display_text(item.get("node_code"), max_chars=20) or _default_node_code(
        category,
        category_node_index,
    )
    confidence_level = _enum_value(item.get("confidence_level"), _ALLOWED_CONFIDENCE_LEVELS, "medium")
    node_ref = truncate_text(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
    related_match_gaps = _normalize_text_list(item.get("related_match_gaps"), limit=6)
    progress_node_ref = node_ref or _node_ref(
        context_digest,
        f"quality:{category}:{node_code}:{display_title}",
        prefix="progress_v2",
    )
    children = _normalize_quality_first_children(
        item.get("children"),
        category=category,
        display_category_title=display_category_title,
        parent_node_ref=progress_node_ref,
        parent_index=index,
        context_digest=context_digest,
        allowed_evidence_refs=allowed_evidence_refs,
        evidence_chunks_by_ref=evidence_chunks_by_ref,
        depth=depth,
    )
    if not children:
        children = _quality_first_repair_resume_deep_dive_children(
            category=category,
            display_category_title=display_category_title,
            parent_node_ref=progress_node_ref,
            parent_node_code=node_code,
            parent_index=index,
            parent_display_title=display_title,
            parent_confidence_level=confidence_level,
            parent_evidence_refs=stable_evidence_refs + evidence_refs,
            context_digest=context_digest,
            allowed_evidence_refs=allowed_evidence_refs,
            evidence_chunks_by_ref=evidence_chunks_by_ref,
            depth=depth,
        )
    coverage_points = _quality_first_normalize_coverage_points(
        _normalize_text_list(item.get("coverage_points"), limit=8),
        evidence_refs=stable_evidence_refs,
        evidence_chunks_by_ref=evidence_chunks_by_ref,
        follow_up_focus=follow_up_focus,
    )
    sub_points = _normalize_text_list(item.get("sub_points"), limit=8)
    if not children and not coverage_points and not sub_points:
        coverage_points = _quality_first_coverage_points_from_evidence(
            stable_evidence_refs,
            evidence_chunks_by_ref=evidence_chunks_by_ref,
        )
    node = {
        "progress_node_ref": progress_node_ref,
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
        "coverage_points": coverage_points,
        "sub_points": sub_points,
        "title": display_title,
        "expected_capability": depth_goal,
        "children": children,
        "node_type": "project_deep_dive" if category == _RESUME_DEEP_DIVE else "job_gap",
        "interview_intent": preparation_goal,
        "interview_method": "technical_deep_dive" if category == _RESUME_DEEP_DIVE else "learning_plan",
        "follow_up_method": "technical_deep_dive" if category == _RESUME_DEEP_DIVE else "learning_plan",
        "attack_style": "technical_deep_dive" if category == _RESUME_DEEP_DIVE else "learning_plan",
        "difficulty_level": "advanced" if confidence_level == "high" else "intermediate",
        "priority": _bounded_int(item.get("priority"), lower=1, upper=999, fallback=index),
        "priority_reason": _sanitize_display_text(item.get("priority_reason"), max_chars=120)
        or "该节点具备岗位贴合和面试追问价值。",
        "related_job_requirements": _dedupe_strings(jd_basis_items, limit=6),
        "related_resume_evidence": _dedupe_strings([resume_signal], limit=3),
        "related_match_gaps": related_match_gaps,
        "missing_points": related_match_gaps,
        "recommended_first_question": first_question,
        "follow_up_directions": follow_up_focus,
        "red_flags": common_loss_risks,
        "evidence_chunk_ids": stable_evidence_refs,
        "evidence_bindings": evidence_bindings,
        "grounding_status": "partially_grounded" if evidence_refs else "weakly_grounded",
    }
    return _sanitize_node_display_fields(node)


def _normalize_quality_first_children(
    raw_children: object,
    *,
    category: str,
    display_category_title: str,
    parent_node_ref: str,
    parent_index: int,
    context_digest: str,
    allowed_evidence_refs: set[str],
    evidence_chunks_by_ref: dict[str, dict[str, Any]],
    depth: int,
) -> list[dict[str, Any]]:
    if depth >= 2 or not isinstance(raw_children, list):
        return []

    children: list[dict[str, Any]] = []
    seen_refs = {parent_node_ref}
    seen_titles: set[str] = set()
    for child_index, child_item in enumerate(raw_children, start=1):
        child = _normalize_quality_first_node(
            child_item,
            category=category,
            display_category_title=display_category_title,
            index=(parent_index * 100) + child_index,
            category_node_index=child_index,
            context_digest=context_digest,
            allowed_evidence_refs=allowed_evidence_refs,
            evidence_chunks_by_ref=evidence_chunks_by_ref,
            depth=depth + 1,
        )
        if child is None:
            continue
        if child["progress_node_ref"] in seen_refs:
            child = {
                **child,
                "progress_node_ref": _node_ref(
                    context_digest,
                    f"quality:{category}:child:{parent_node_ref}:{child_index}:{child['display_title']}",
                    prefix="progress_v2",
                ),
            }
        normalized_title = _normalize_label_for_compare(child["display_title"])
        if normalized_title in seen_titles:
            continue
        seen_refs.add(child["progress_node_ref"])
        seen_titles.add(normalized_title)
        children.append(child)
    return children


def _quality_first_repair_resume_deep_dive_children(
    *,
    category: str,
    display_category_title: str,
    parent_node_ref: str,
    parent_node_code: str,
    parent_index: int,
    parent_display_title: str,
    parent_confidence_level: str,
    parent_evidence_refs: list[str],
    context_digest: str,
    allowed_evidence_refs: set[str],
    evidence_chunks_by_ref: dict[str, dict[str, Any]],
    depth: int,
) -> list[dict[str, Any]]:
    if category != _RESUME_DEEP_DIVE or depth >= 1:
        return []

    project_keys = {
        _quality_first_project_key(chunk)
        for ref in _dedupe_strings(parent_evidence_refs, limit=12)
        if (chunk := evidence_chunks_by_ref.get(ref))
        and _quality_first_chunk_source_type(chunk) == "resume_project"
    }
    project_keys.discard(("", ""))
    if not project_keys:
        return []

    children: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for contribution_ref, contribution_chunk in evidence_chunks_by_ref.items():
        if contribution_ref not in allowed_evidence_refs:
            continue
        if _quality_first_chunk_source_type(contribution_chunk) != "resume_project_contribution":
            continue
        if _quality_first_project_key(contribution_chunk) not in project_keys:
            continue
        contribution_title = _sanitize_display_text(contribution_chunk.get("title"), max_chars=120)
        if not contribution_title:
            contribution_title = _sanitize_display_text(
                contribution_chunk.get("text") or contribution_chunk.get("excerpt"),
                max_chars=80,
            )
        if not contribution_title:
            continue
        normalized_title = _normalize_label_for_compare(contribution_title)
        if normalized_title in seen_titles:
            continue
        seen_titles.add(normalized_title)
        child_index = len(children) + 1
        contribution_text = _sanitize_display_text(
            contribution_chunk.get("text") or contribution_chunk.get("excerpt"),
            max_chars=240,
        )
        child = _normalize_quality_first_node(
            {
                "progress_node_ref": _node_ref(
                    context_digest,
                    f"quality:{category}:repaired-child:{parent_node_ref}:{contribution_ref}",
                    prefix="progress_v2",
                ),
                "node_code": f"{parent_node_code}.{child_index}",
                "category": category,
                "display_category_title": display_category_title,
                "display_title": contribution_title,
                "exam_point": contribution_title,
                "basis_type": "resume_signal",
                "resume_signal": contribution_text,
                "jd_basis": None,
                "priority_reason": "该贡献项来自同项目简历证据，可支撑项目内连续追问。",
                "depth_goal": f"围绕「{contribution_title}」讲清个人贡献、技术方案和验证结果。",
                "first_question": (
                    f"请结合「{parent_display_title}」说明「{contribution_title}」的具体做法、取舍和结果。"
                ),
                "follow_up_focus": ["个人贡献边界", "技术方案取舍", "验证结果"],
                "evidence_refs": [contribution_ref],
                "confidence_level": parent_confidence_level,
                "low_confidence_flags": [],
            },
            category=category,
            display_category_title=display_category_title,
            index=(parent_index * 100) + child_index,
            category_node_index=child_index,
            context_digest=context_digest,
            allowed_evidence_refs=allowed_evidence_refs,
            evidence_chunks_by_ref=evidence_chunks_by_ref,
            depth=depth + 1,
        )
        if child is not None:
            children.append(child)
        if len(children) >= 4:
            break
    return children


def _quality_first_project_key(chunk: dict[str, Any]) -> tuple[str, str]:
    source_ref = chunk.get("source_ref") if isinstance(chunk.get("source_ref"), dict) else {}
    project_title = str(source_ref.get("project_title") or chunk.get("title") or "").strip()
    project_sequence = str(source_ref.get("project_sequence") or "").strip()
    return (project_sequence, project_title)


def _quality_first_coverage_points_from_evidence(
    evidence_refs: list[str],
    *,
    evidence_chunks_by_ref: dict[str, dict[str, Any]],
) -> list[str]:
    points: list[str] = []
    for evidence_ref in evidence_refs:
        chunk = evidence_chunks_by_ref.get(evidence_ref)
        if not isinstance(chunk, dict):
            continue
        source_type = chunk.get("source_type")
        if source_type not in {"resume_project", "resume_project_contribution"}:
            continue
        title = _quality_first_clean_coverage_point(chunk.get("title"))
        if source_type == "resume_project_contribution" and title:
            points.append(title)
            continue
        text = str(chunk.get("text") or chunk.get("excerpt") or "")
        if source_type == "resume_project":
            points.extend(_quality_first_project_contribution_points(text))
    return _dedupe_strings(
        [_sanitize_display_text(point, max_chars=80) for point in points if point],
        limit=8,
    )


def _quality_first_normalize_coverage_points(
    raw_points: list[str],
    *,
    evidence_refs: list[str],
    evidence_chunks_by_ref: dict[str, dict[str, Any]],
    follow_up_focus: list[str],
) -> list[str]:
    project_titles = _quality_first_project_titles(evidence_chunks_by_ref)
    evidence_points = _quality_first_filter_coverage_points(
        _quality_first_coverage_points_from_evidence(
            evidence_refs,
            evidence_chunks_by_ref=evidence_chunks_by_ref,
        ),
        project_titles=project_titles,
    )
    cleaned_points = _quality_first_filter_coverage_points(
        raw_points,
        project_titles=project_titles,
    )
    if evidence_points:
        return _dedupe_by_label(evidence_points + cleaned_points, limit=8)
    if cleaned_points:
        return _dedupe_by_label(cleaned_points, limit=8)
    focus_points = _quality_first_filter_coverage_points(
        follow_up_focus,
        project_titles=project_titles,
    )
    if focus_points:
        return _dedupe_by_label(focus_points, limit=8)
    return []


def _quality_first_filter_coverage_points(
    points: list[str],
    *,
    project_titles: set[str],
) -> list[str]:
    result: list[str] = []
    project_title_keys = {_normalize_label_for_compare(title) for title in project_titles if title}
    for point in points:
        cleaned = _quality_first_clean_coverage_point(point)
        if not cleaned:
            continue
        normalized = _normalize_label_for_compare(cleaned)
        if not normalized or normalized in project_title_keys:
            continue
        if _quality_first_looks_non_technical_coverage_point(cleaned):
            continue
        result.append(cleaned)
    return _dedupe_by_label(result, limit=8)


def _quality_first_clean_coverage_point(value: object) -> str:
    text = _sanitize_display_text(value, max_chars=80).strip()
    text = re.sub(r"^(?:[-*+]|\d+[.)]|[（(]?\d+[）)])\s+", "", text)
    text = re.sub(r"^(?:\*\*|__)(.+?)(?:\*\*|__)\s*([：:|｜].*)$", r"\1\2", text).strip()
    text = re.sub(r"^(?:\*\*|__)(.+?)(?:\*\*|__)$", r"\1", text).strip()
    text = text.strip("*_`# ")
    delimiter_match = re.match(r"^(.{2,80}?)[：:|｜]\s*(.+)$", text)
    if delimiter_match and len(delimiter_match.group(1).strip()) <= 40:
        text = delimiter_match.group(1).strip("*_` ")
    return text


def _quality_first_project_titles(evidence_chunks_by_ref: dict[str, dict[str, Any]]) -> set[str]:
    titles: set[str] = set()
    for chunk in evidence_chunks_by_ref.values():
        if not isinstance(chunk, dict):
            continue
        source_ref = chunk.get("source_ref")
        if isinstance(source_ref, dict):
            project_title = _quality_first_clean_coverage_point(source_ref.get("project_title"))
            if project_title:
                titles.add(project_title)
        if chunk.get("source_type") == "resume_project":
            title = _quality_first_clean_coverage_point(chunk.get("title"))
            if title:
                titles.add(title)
    return titles


def _quality_first_looks_non_technical_coverage_point(text: str) -> bool:
    if re.search(r"\d{4}\s*[./年-]\s*\d{1,2}|\d{4}\s*[./年-]\s*(?:至今|present)", text, flags=re.IGNORECASE):
        return True
    if any(marker in text for marker in ("有限公司", "公司", "部门", "岗位", "职位", "工程师")) and not any(
        signal in text for signal in ("设计", "实现", "优化", "架构", "治理", "一致性", "检索", "管道", "模型", "API")
    ):
        return True
    return False


def _dedupe_by_label(values: list[object], *, limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = truncate_text(value, max_chars=480)
        label = _normalize_label_for_compare(text)
        if text and label and label not in seen:
            result.append(text)
            seen.add(label)
        if len(result) >= limit:
            break
    return result


def _quality_first_project_contribution_points(text: str) -> list[str]:
    if not text:
        return []
    result: list[str] = []
    bullet_pattern = re.compile(
        r"(?:^|\s)(?:[-*+]|\d+[.)]|[（(]?\d+[）)])\s+(.+?)"
        r"(?=(?:\s(?:[-*+]|\d+[.)]|[（(]?\d+[）)])\s+)|$)"
    )
    for match in bullet_pattern.finditer(text):
        item = _quality_first_clean_coverage_point(match.group(1))
        if item and not _quality_first_looks_project_level_coverage_text(item):
            result.append(item)
    return _dedupe_strings(result, limit=8)


def _quality_first_looks_project_level_coverage_text(text: str) -> bool:
    normalized = text.strip()
    return bool(
        re.match(r"^.{0,40}(?:项目|project).{0,40}[：:|｜]", normalized, flags=re.IGNORECASE)
    )


def _quality_first_looks_project_contribution(text: str) -> bool:
    normalized = text.strip()
    if not normalized or normalized.startswith(":::"):
        return False
    return any(
        marker in normalized
        for marker in ("贡献", "负责", "完成", "实现", "设计", "优化", "验证", "落地")
    )


def _quality_first_resume_evidence_augmentations(
    item: dict[str, Any],
    *,
    category: str,
    display_title: str,
    exam_point: str,
    resume_signal: str | None,
    follow_up_focus: list[str],
    stable_evidence_refs: list[str],
    evidence_chunks_by_ref: dict[str, dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    if category != _RESUME_DEEP_DIVE:
        return [], []

    existing_refs = set(stable_evidence_refs)
    if not existing_refs:
        return [], []
    if any(
        _quality_first_chunk_source_type(evidence_chunks_by_ref.get(ref))
        in {"resume_project", "resume_project_contribution"}
        for ref in existing_refs
    ):
        return [], []

    query = " ".join(
        [
            display_title,
            exam_point,
            resume_signal or "",
            " ".join(follow_up_focus),
            _sanitize_display_text(item.get("depth_goal"), max_chars=160),
        ]
    )
    candidates: list[tuple[int, int, str, dict[str, Any]]] = []
    for ref, chunk in evidence_chunks_by_ref.items():
        if ref in existing_refs or not isinstance(chunk, dict):
            continue
        source_type = _quality_first_chunk_source_type(chunk)
        if source_type not in {"resume_project_contribution", "resume_project"}:
            continue
        score = _quality_first_resume_evidence_match_score(query, chunk)
        if score < 4:
            continue
        source_rank = 0 if source_type == "resume_project_contribution" else 1
        candidates.append((-score, source_rank, ref, chunk))

    candidates.sort()
    refs: list[str] = []
    bindings: list[dict[str, Any]] = []
    for _score, _source_rank, ref, chunk in candidates[:2]:
        source_type = _quality_first_chunk_source_type(chunk)
        refs.append(ref)
        bindings.append(
            {
                "ref": ref,
                "source_type": source_type,
                "binding_type": "resume_signal_match",
                "title": _sanitize_display_text(chunk.get("title"), max_chars=120),
            }
        )
    return refs, bindings


def _quality_first_chunk_source_type(chunk: object) -> str:
    if not isinstance(chunk, dict):
        return ""
    return str(chunk.get("source_type") or "")


def _quality_first_resume_evidence_match_score(query: str, chunk: dict[str, Any]) -> int:
    query_key = _normalize_label_for_compare(query)
    chunk_text = " ".join(
        str(chunk.get(field) or "")
        for field in ("title", "text", "excerpt")
    )
    source_ref = chunk.get("source_ref")
    if isinstance(source_ref, dict):
        chunk_text = f"{source_ref.get('project_title') or ''} {chunk_text}"
    chunk_key = _normalize_label_for_compare(chunk_text)
    if not query_key or not chunk_key:
        return 0

    score = 0
    title_key = _normalize_label_for_compare(chunk.get("title"))
    if title_key and title_key in query_key:
        score += 8
    if len(query_key) >= 6 and query_key in chunk_key:
        score += 10
    if len(title_key) >= 4 and title_key in chunk_key and title_key in query_key:
        score += 6
    score += len(_quality_first_bigrams(query_key) & _quality_first_bigrams(chunk_key))
    return score


def _quality_first_bigrams(text: str) -> set[str]:
    if len(text) < 2:
        return set()
    return {text[index : index + 2] for index in range(len(text) - 1)}


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
    node_text = _quality_first_cost_gate_text(node)
    if not any(_quality_first_contains(node_text, term) for term in _QUALITY_FIRST_COST_NODE_TERMS):
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
    for item in value[:5]:
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
                "reason": _sanitize_display_text(item.get("reason"), max_chars=120)
                or "低优先级候选项，暂不进入主训练路径。",
                "basis_type": basis_type,
                "evidence_refs": _sanitize_string_list(item.get("evidence_refs") or item.get("evidence_chunk_ids"), limit=8),
                "confidence_level": _enum_value(item.get("confidence_level"), _ALLOWED_CONFIDENCE_LEVELS, "low"),
                "suggested_trigger": _sanitize_display_text(item.get("suggested_trigger"), max_chars=120)
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
        if len(result) >= 5:
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


def _quality_first_cost_gate_text(node: dict[str, Any]) -> str:
    return " ".join(str(node.get(field) or "") for field in ("display_title", "title", "exam_point"))


def _quality_first_context_text(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(_quality_first_context_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_quality_first_context_text(item) for item in value)
    return str(value or "")


def _quality_first_allowed_evidence_refs(context: dict[str, Any]) -> set[str]:
    return set(_quality_first_evidence_chunks_by_ref(context))


def _quality_first_evidence_chunks_by_ref(context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    prompt_context = context.get("prompt_context")
    selected_chunks = []
    if isinstance(prompt_context, dict):
        prompt_chunks = prompt_context.get("selected_evidence_chunks")
        if isinstance(prompt_chunks, list):
            selected_chunks = prompt_chunks
    if not selected_chunks:
        selected_chunks = build_progress_prompt_context(context, purpose="initial_plan").get(
            "selected_evidence_chunks",
            [],
        )

    chunks_by_ref: dict[str, dict[str, Any]] = {}
    for chunk in selected_chunks:
        if not isinstance(chunk, dict):
            continue
        ref = chunk.get("ref") or chunk.get("chunk_id")
        if isinstance(ref, str) and ref.strip():
            chunks_by_ref[ref.strip()] = chunk
    return chunks_by_ref


def _quality_first_evidence_ref_validation_summary(
    nodes: list[dict[str, Any]],
    allowed_evidence_refs: set[str],
) -> dict[str, Any]:
    invalid_ref_count = 0
    invalid_ref_samples: list[str] = []
    nodes_with_invalid_refs_count = 0
    for node in _flatten_progress_nodes(nodes):
        invalid_refs = [ref for ref in _quality_first_evidence_refs(node) if ref not in allowed_evidence_refs]
        if not invalid_refs:
            continue
        nodes_with_invalid_refs_count += 1
        invalid_ref_count += len(invalid_refs)
        invalid_ref_samples.extend(invalid_refs)
    return {
        "allowed_ref_count": len(allowed_evidence_refs),
        "invalid_ref_count": invalid_ref_count,
        "invalid_ref_samples": _dedupe_strings(invalid_ref_samples, limit=5),
        "nodes_with_invalid_refs_count": nodes_with_invalid_refs_count,
    }


def _quality_first_evidence_refs(node: dict[str, Any]) -> list[str]:
    return _dedupe_strings(_string_list(node.get("evidence_refs"), limit=8), limit=8)


def _quality_first_evidence_chunk_ids(node: dict[str, Any]) -> list[str]:
    return _dedupe_strings(_string_list(node.get("evidence_chunk_ids"), limit=8), limit=8)


def _quality_first_contains(text: str, term: str) -> bool:
    if term.isascii():
        return term.lower() in text.lower()
    return term in text


def _quality_first_initial_state_from_nodes(
    nodes: list[dict[str, Any]],
    *,
    context: dict[str, Any],
) -> dict[str, Any]:
    flat_nodes = _flatten_progress_nodes(nodes)
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


def _provider_response_failure_reason(exc: LlmTransportResponseError) -> str:
    error_type = getattr(exc, "error_type", None)
    if error_type == "provider_output_truncated":
        return "provider_output_truncated"
    message = str(exc)
    if "输出被截断" in message or "JSON 不完整" in message:
        return "provider_output_truncated"
    return "provider_response_invalid"


def _provider_unavailable_failure_reason(exc: LlmTransportUnavailableError) -> str:
    message = str(exc).lower()
    if "timeout" in message or "超时" in message:
        return "provider_timeout"
    return "provider_unavailable"


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


def _provider_request_validation_errors(exc: ProviderRequestValidationError) -> list[dict[str, str]]:
    return [
        {
            "field": "provider_request",
            "code": "validation_failed",
            "reason": error,
        }
        for error in exc.errors[:8]
    ]


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
        "progress_tree_state": _empty_state(
            PROGRESS_TREE_STATUS_FAILED,
            prompt_version=POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
        ),
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
        "progress_tree_state": _empty_state(
            PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
            prompt_version=POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
        ),
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
    "coverage_points",
    "related_job_requirements",
    "related_resume_evidence",
    "related_match_gaps",
    "missing_points",
    "sub_points",
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
            sanitized[field] = [
                sanitized_item
                for item in value
                if (sanitized_item := _sanitize_display_text(item, max_chars=600))
            ]
    sanitized["children"] = [
        _sanitize_node_display_fields(child)
        for child in sanitized.get("children", [])
        if isinstance(child, dict)
    ]
    return sanitized


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


def _normalize_text_list(value: object, *, limit: int) -> list[str]:
    if isinstance(value, str):
        raw_items = _TEXT_LIST_SEPARATOR_RE.split(value)
    elif isinstance(value, list):
        raw_items = _string_list(value, limit=limit * 2)
    else:
        return []

    result: list[str] = []
    for item in raw_items:
        text = _sanitize_display_text(item, max_chars=480)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _dedupe_strings(values: list[object], *, limit: int) -> list[str]:
    result: list[str] = []
    for value in values:
        text = truncate_text(value, max_chars=480)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _enum_value(value: object, allowed_values: set[str], fallback: str) -> str:
    text = truncate_text(value, max_chars=80)
    return text if text in allowed_values else fallback


# Shared state refresh / progress tree helpers.


def resolve_progress_node(
    *,
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str | None,
) -> dict[str, Any] | None:
    if plan.get("status") != PROGRESS_TREE_STATUS_READY:
        return None
    nodes = plan.get("nodes", [])
    if requested_ref:
        requested = _find_progress_node(nodes, requested_ref)
        if requested is not None:
            return requested
    current_priority = state.get("current_priority") or {}
    priority_ref = current_priority.get("progress_node_ref")
    if priority_ref:
        priority = _find_progress_node(nodes, priority_ref)
        if priority is not None:
            return priority
    leaves = _flatten_leaf_nodes(nodes)
    return leaves[0] if leaves else None


def _normalize_state(
    state_payload: dict[str, Any],
    *,
    existing_plan: dict[str, Any],
    allow_refresh_failed: bool,
    prompt_version: str,
    schema_id: str,
    schema_version: str,
) -> dict[str, Any]:
    envelope = _progress_tree_state_payload_envelope(
        state_payload,
        existing_plan=existing_plan,
        allow_refresh_failed=allow_refresh_failed,
        prompt_version=prompt_version,
        schema_id=schema_id,
        schema_version=schema_version,
    )
    normalized_state = envelope.payload.get("progress_tree_state")
    if isinstance(normalized_state, dict):
        return normalized_state
    return _empty_state(PROGRESS_TREE_STATUS_FAILED, prompt_version=prompt_version)


def _progress_tree_state_payload_envelope(
    state_payload: dict[str, Any],
    *,
    existing_plan: dict[str, Any],
    allow_refresh_failed: bool,
    prompt_version: str,
    schema_id: str,
    schema_version: str,
) -> LegacyAgentOutputEnvelope:
    def enveloped(state: dict[str, Any]) -> LegacyAgentOutputEnvelope:
        return LegacyAgentOutputEnvelope(
            task_type="polish_progress_tree_state",
            schema_id=schema_id,
            schema_version=schema_version,
            prompt_version=prompt_version,
            status=state.get("status"),
            payload={"progress_tree_state": state},
        )

    if state_payload.get("status") == PROGRESS_TREE_STATUS_REFRESH_FAILED and allow_refresh_failed:
        return enveloped(
            _empty_state(PROGRESS_TREE_STATUS_REFRESH_FAILED, prompt_version=prompt_version)
        )

    plan_nodes = _flatten_progress_nodes(existing_plan.get("nodes", []))
    if not plan_nodes:
        return enveloped(_empty_state(PROGRESS_TREE_STATUS_FAILED, prompt_version=prompt_version))
    plan_by_ref = {node["progress_node_ref"]: node for node in plan_nodes}
    node_states = _complete_node_states_for_plan(
        existing_plan.get("nodes", []),
        state_payload.get("node_states", []),
    )
    node_states = _rollup_node_states(existing_plan.get("nodes", []), node_states)

    current_priority = _normalize_priority(state_payload.get("current_priority"), plan_by_ref)
    if current_priority is None:
        current_priority = _first_non_completed_priority(
            node_states,
            _flatten_leaf_nodes(existing_plan.get("nodes", [])) or plan_nodes,
        )
    if current_priority is None:
        return enveloped(_empty_state(PROGRESS_TREE_STATUS_FAILED, prompt_version=prompt_version))

    return enveloped({
        "schema_id": schema_id,
        "schema_version": schema_version,
        "prompt_version": prompt_version,
        "status": PROGRESS_TREE_STATUS_READY,
        "node_states": node_states,
        "current_priority": current_priority,
        "updated_from_turns_count": _bounded_int(state_payload.get("updated_from_turns_count"), 0, 999),
        "progress": {
            "progress_percent": _progress_percent_from_leaf_nodes(
                _flatten_leaf_nodes(existing_plan.get("nodes", [])) or plan_nodes,
                node_states,
            )
        },
    })


def _normalize_priority(value: object, plan_by_ref: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    node_ref = truncate_text(value.get("progress_node_ref") or value.get("node_ref"), max_chars=120)
    if not node_ref or node_ref not in plan_by_ref:
        return None
    node = plan_by_ref[node_ref]
    return {
        "progress_node_ref": node_ref,
        "title": truncate_text(value.get("title"), max_chars=120) or node["title"],
        "expected_capability": truncate_text(value.get("expected_capability"), max_chars=480)
        or node["expected_capability"],
    }


def _first_non_completed_priority(
    node_states: list[dict[str, Any]],
    plan_nodes: list[dict[str, Any]],
) -> dict[str, Any] | None:
    status_by_ref = {state["progress_node_ref"]: state["status"] for state in node_states}
    for node in plan_nodes:
        if status_by_ref.get(node["progress_node_ref"]) != "completed":
            return {
                "progress_node_ref": node["progress_node_ref"],
                "title": node["title"],
                "expected_capability": node["expected_capability"],
            }
    if plan_nodes:
        node = plan_nodes[-1]
        return {
            "progress_node_ref": node["progress_node_ref"],
            "title": node["title"],
            "expected_capability": node["expected_capability"],
        }
    return None


def _insufficient_artifacts(context: dict[str, Any]) -> dict[str, Any]:
    plan = {
        "schema_id": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "context_digest": context["content_digest"],
        "nodes": [],
    }
    return {
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "progress_tree_plan": plan,
        "progress_tree_state": _empty_state(
            PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
            prompt_version=POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
        ),
        "progress_percent": 0,
    }


def _refresh_failed_artifacts(
    existing_plan: dict[str, Any],
    existing_state: dict[str, Any],
    *,
    reason: str,
) -> dict[str, Any]:
    if _state_matches_plan(existing_state, existing_plan):
        state = {**existing_state, "status": PROGRESS_TREE_STATUS_REFRESH_FAILED}
    else:
        state = _initial_state_fallback(
            existing_plan,
            status=PROGRESS_TREE_STATUS_REFRESH_FAILED,
            prompt_version=POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
            failure_reason=reason,
        )
    state.setdefault("schema_id", POLISH_PROGRESS_TREE_STATE_SCHEMA_ID)
    state.setdefault("schema_version", POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION)
    state.setdefault("prompt_version", POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION)
    state.setdefault("progress", {"progress_percent": _progress_percent(existing_state)})
    state["failure_reason"] = reason
    return {
        "status": PROGRESS_TREE_STATUS_REFRESH_FAILED,
        "progress_tree_plan": existing_plan,
        "progress_tree_state": state,
        "progress_percent": _progress_percent(state),
    }


def _empty_state(status: str, *, prompt_version: str = POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION) -> dict[str, Any]:
    return {
        "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
        "prompt_version": prompt_version,
        "status": status,
        "node_states": [],
        "current_priority": None,
        "updated_from_turns_count": 0,
        "progress": {"progress_percent": 0},
    }


def _initial_state_fallback(
    plan: dict[str, Any],
    *,
    status: str = PROGRESS_TREE_STATUS_READY,
    prompt_version: str,
    failure_reason: str,
) -> dict[str, Any]:
    plan_nodes = _flatten_progress_nodes(plan.get("nodes", []))
    current_priority = _fallback_priority(_flatten_leaf_nodes(plan.get("nodes", [])) or plan_nodes)
    return {
        "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
        "prompt_version": prompt_version,
        "status": status,
        "node_states": [
            {
                "progress_node_ref": node["progress_node_ref"],
                "status": "pending",
                "completed_questions_count": 0,
                "latest_feedback_summary": None,
            }
            for node in plan_nodes
        ],
        "current_priority": current_priority,
        "updated_from_turns_count": 0,
        "progress": {"progress_percent": 0},
        "summary": "进展树已生成，等待首次问答后刷新进度",
        "failure_reason": failure_reason,
    }


def _apply_turn_progress_to_state(
    state: dict[str, Any],
    context: dict[str, Any],
    *,
    existing_plan: dict[str, Any],
) -> dict[str, Any]:
    plan_nodes = existing_plan.get("nodes", [])
    flat_plan_nodes = _flatten_progress_nodes(plan_nodes)
    if not flat_plan_nodes:
        return state
    node_states = _complete_node_states_for_plan(plan_nodes, state.get("node_states", []))
    if not node_states:
        return state
    plan_ref_set = {node["progress_node_ref"] for node in flat_plan_nodes}
    turn_updates = _turn_progress_updates(context, node_states, plan_ref_set)
    if not turn_updates:
        rolled_node_states = _rollup_node_states(plan_nodes, node_states)
        return {
            **state,
            "node_states": rolled_node_states,
            "summary": "v2_local_state_refresh",
            "progress": {
                "progress_percent": _progress_percent_from_leaf_nodes(
                    _flatten_leaf_nodes(plan_nodes) or flat_plan_nodes,
                    rolled_node_states,
                )
            },
        }

    completed_counts_by_ref: dict[str, int] = {}
    latest_feedback_by_ref: dict[str, str] = {}
    in_progress_refs: set[str] = set()
    completed_refs: set[str] = set()
    latest_turn_ref: str | None = None
    for update in turn_updates:
        node_ref = update["progress_node_ref"]
        latest_turn_ref = node_ref
        if update["status"] == "completed":
            completed_refs.add(node_ref)
            in_progress_refs.discard(node_ref)
            completed_counts_by_ref[node_ref] = completed_counts_by_ref.get(node_ref, 0) + 1
        elif node_ref not in completed_refs:
            in_progress_refs.add(node_ref)
        feedback_summary = update.get("latest_feedback_summary")
        if feedback_summary:
            latest_feedback_by_ref[node_ref] = feedback_summary

    updated_node_states = []
    for item in node_states:
        updated = {**item}
        node_ref = str(updated.get("progress_node_ref") or "")
        if node_ref in completed_refs:
            updated["status"] = "completed"
            updated["completed_questions_count"] = max(
                _bounded_int(updated.get("completed_questions_count"), 0, 999),
                completed_counts_by_ref.get(node_ref, 1),
            )
        elif node_ref in in_progress_refs:
            updated["status"] = "in_progress"
        if node_ref in latest_feedback_by_ref:
            updated["latest_feedback_summary"] = latest_feedback_by_ref[node_ref]
        updated_node_states.append(updated)

    rolled_node_states = _rollup_node_states(plan_nodes, updated_node_states)
    current_priority = _current_priority_from_turns(
        latest_turn_ref=latest_turn_ref,
        updated_node_states=rolled_node_states,
        existing_state=state,
        existing_plan=existing_plan,
    )
    return {
        **state,
        "node_states": rolled_node_states,
        "current_priority": current_priority,
        "updated_from_turns_count": len(turn_updates),
        "summary": "v2_local_state_refresh",
        "progress": {
            "progress_percent": _progress_percent_from_leaf_nodes(
                _flatten_leaf_nodes(plan_nodes) or flat_plan_nodes,
                rolled_node_states,
            )
        },
    }


def _complete_node_states_for_plan(
    plan_nodes: list[dict[str, Any]],
    raw_node_states: object,
) -> list[dict[str, Any]]:
    flat_plan_nodes = _flatten_progress_nodes(plan_nodes)
    plan_ref_set = {node["progress_node_ref"] for node in flat_plan_nodes}
    raw_by_ref: dict[str, dict[str, Any]] = {}
    if isinstance(raw_node_states, list):
        for item in raw_node_states:
            if not isinstance(item, dict):
                continue
            node_ref = truncate_text(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
            if node_ref and node_ref in plan_ref_set:
                raw_by_ref[node_ref] = item
    return [
        {
            "progress_node_ref": node["progress_node_ref"],
            "status": _normalize_status(raw_by_ref.get(node["progress_node_ref"], {}).get("status")),
            "completed_questions_count": _bounded_int(
                raw_by_ref.get(node["progress_node_ref"], {}).get("completed_questions_count"),
                0,
                999,
            ),
            "latest_feedback_summary": truncate_text(
                raw_by_ref.get(node["progress_node_ref"], {}).get("latest_feedback_summary"),
                max_chars=480,
            ),
        }
        for node in flat_plan_nodes
    ]


def _rollup_node_states(
    plan_nodes: list[dict[str, Any]],
    node_states: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    state_by_ref = {
        str(item.get("progress_node_ref")): {**item}
        for item in node_states
        if item.get("progress_node_ref")
    }

    def rollup(node: dict[str, Any]) -> dict[str, Any]:
        node_ref = node["progress_node_ref"]
        current = state_by_ref.setdefault(
            node_ref,
            {
                "progress_node_ref": node_ref,
                "status": "pending",
                "completed_questions_count": 0,
                "latest_feedback_summary": None,
            },
        )
        children = [child for child in node.get("children", []) if isinstance(child, dict)]
        if not children:
            current["status"] = _normalize_status(current.get("status"))
            current["completed_questions_count"] = _bounded_int(current.get("completed_questions_count"), 0, 999)
            current["latest_feedback_summary"] = truncate_text(current.get("latest_feedback_summary"), max_chars=480)
            return current

        child_states = [rollup(child) for child in children]
        child_statuses = [_normalize_status(child.get("status")) for child in child_states]
        own_status = _normalize_status(current.get("status"))
        has_started = own_status in {"completed", "in_progress"} or any(status != "pending" for status in child_statuses)
        if child_statuses and all(status == "completed" for status in child_statuses) and own_status != "in_progress":
            current["status"] = "completed"
        elif has_started:
            current["status"] = "in_progress"
        else:
            current["status"] = "pending"
        current["completed_questions_count"] = max(
            _bounded_int(current.get("completed_questions_count"), 0, 999),
            sum(_bounded_int(child.get("completed_questions_count"), 0, 999) for child in child_states),
        )
        latest_child_feedback = next(
            (
                truncate_text(child.get("latest_feedback_summary"), max_chars=480)
                for child in reversed(child_states)
                if truncate_text(child.get("latest_feedback_summary"), max_chars=480)
            ),
            None,
        )
        current["latest_feedback_summary"] = latest_child_feedback or truncate_text(
            current.get("latest_feedback_summary"),
            max_chars=480,
        )
        return current

    for node in plan_nodes:
        rollup(node)
    return [
        state_by_ref[node["progress_node_ref"]]
        for node in _flatten_progress_nodes(plan_nodes)
        if node.get("progress_node_ref") in state_by_ref
    ]


def _progress_percent_from_leaf_nodes(
    leaf_nodes: list[dict[str, Any]],
    node_states: list[dict[str, Any]],
) -> int:
    if not leaf_nodes:
        return 0
    status_by_ref = {
        str(item.get("progress_node_ref")): _normalize_status(item.get("status"))
        for item in node_states
        if item.get("progress_node_ref")
    }
    completed_leaf_count = sum(
        1 for node in leaf_nodes if status_by_ref.get(node["progress_node_ref"]) == "completed"
    )
    return _bounded_int(round(completed_leaf_count * 100 / len(leaf_nodes)), 0, 100)


def _turn_progress_updates(
    context: dict[str, Any],
    node_states: list[dict[str, Any]],
    plan_ref_set: set[str],
) -> list[dict[str, str]]:
    turns = context.get("turns")
    if not isinstance(turns, list):
        return []
    existing_refs = {
        str(item.get("progress_node_ref"))
        for item in node_states
        if isinstance(item.get("progress_node_ref"), str) and item.get("progress_node_ref")
    }
    updates: list[dict[str, str]] = []
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        node_ref = truncate_text(turn.get("progress_node_ref"), max_chars=120)
        if not node_ref or node_ref not in existing_refs or node_ref not in plan_ref_set:
            continue
        status = "completed" if _turn_has_feedback(turn) else "in_progress"
        feedback_summary = _latest_turn_feedback(turn) if status == "completed" else None
        update: dict[str, str] = {
            "progress_node_ref": node_ref,
            "status": status,
        }
        if feedback_summary:
            update["latest_feedback_summary"] = truncate_text(feedback_summary, max_chars=480) or feedback_summary
        updates.append(update)
    return updates


def _turn_has_feedback(turn: dict[str, Any]) -> bool:
    if turn.get("feedback_id") or turn.get("feedback_created_at") or turn.get("score_result_id"):
        return True
    feedback_text = truncate_text(turn.get("feedback_text"), max_chars=640)
    if feedback_text and feedback_text != PENDING_FEEDBACK_TEXT:
        return True
    answers = turn.get("answers")
    if not isinstance(answers, list):
        return False
    return any(isinstance(answer, dict) and _answer_has_feedback(answer) for answer in answers)


def _answer_has_feedback(answer: dict[str, Any]) -> bool:
    if answer.get("feedback_id") or answer.get("feedback_created_at") or answer.get("score_result_id"):
        return True
    feedback_text = truncate_text(answer.get("feedback_text"), max_chars=640)
    return bool(feedback_text and feedback_text != PENDING_FEEDBACK_TEXT)


def _current_priority_from_turns(
    *,
    latest_turn_ref: str | None,
    updated_node_states: list[dict[str, Any]],
    existing_state: dict[str, Any],
    existing_plan: dict[str, Any],
) -> dict[str, Any] | None:
    plan_nodes = _flatten_progress_nodes(existing_plan.get("nodes", []))
    leaf_plan_nodes = _flatten_leaf_nodes(existing_plan.get("nodes", [])) or plan_nodes
    plan_by_ref = {node["progress_node_ref"]: node for node in plan_nodes}
    if latest_turn_ref:
        priority = _priority_for_ref(latest_turn_ref, plan_by_ref, existing_state)
        if priority is not None:
            return priority
    return _first_non_completed_priority(updated_node_states, leaf_plan_nodes)


def _priority_for_ref(
    node_ref: str,
    plan_by_ref: dict[str, dict[str, Any]],
    existing_state: dict[str, Any],
) -> dict[str, Any] | None:
    node = plan_by_ref.get(node_ref)
    if node is None:
        return None
    current_priority = existing_state.get("current_priority")
    if isinstance(current_priority, dict) and current_priority.get("progress_node_ref") == node_ref:
        return {
            "progress_node_ref": node_ref,
            "title": truncate_text(current_priority.get("title"), max_chars=120) or node["title"],
            "expected_capability": truncate_text(current_priority.get("expected_capability"), max_chars=480)
            or node["expected_capability"],
        }
    return {
        "progress_node_ref": node_ref,
        "title": node["title"],
        "expected_capability": node["expected_capability"],
    }


def _fallback_priority(plan_nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not plan_nodes:
        return None
    node = plan_nodes[0]
    return {
        "progress_node_ref": node["progress_node_ref"],
        "title": node["title"],
        "expected_capability": node["expected_capability"],
    }


def _state_matches_plan(state: dict[str, Any], plan: dict[str, Any]) -> bool:
    if not isinstance(state, dict):
        return False
    plan_refs = {node["progress_node_ref"] for node in _flatten_progress_nodes(plan.get("nodes", []))}
    node_states = state.get("node_states")
    if not plan_refs or not isinstance(node_states, list) or not node_states:
        return False
    state_refs = {
        item.get("progress_node_ref")
        for item in node_states
        if isinstance(item, dict) and item.get("progress_node_ref")
    }
    return bool(state_refs) and state_refs.issubset(plan_refs)


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


def _metadata_value(
    root_payload: dict[str, Any],
    nested_payload: dict[str, Any],
    key: str,
    fallback: str,
) -> str:
    for payload in (nested_payload, root_payload):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


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


def _bounded_int(value: object, lower: int, upper: int, fallback: int | None = None) -> int:
    fallback_value = lower if fallback is None else fallback
    if isinstance(value, bool):
        return fallback_value
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback_value
    return max(lower, min(upper, parsed))


def _normalize_status(value: object) -> str:
    if value in {"completed", "mastered"}:
        return "completed"
    if value in {"in_progress", "active", "current"}:
        return "in_progress"
    return "pending"


def _node_ref(context_digest: str, seed: str, *, prefix: str = "progress") -> str:
    return f"{prefix}_{sha256(f'{context_digest}:{seed}'.encode('utf-8')).hexdigest()[:16]}"


def _progress_percent(state: dict[str, Any]) -> int:
    progress = state.get("progress")
    if isinstance(progress, dict):
        return _bounded_int(progress.get("progress_percent"), 0, 100)
    return _bounded_int(state.get("progress_percent"), 0, 100)


def _flatten_progress_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in nodes:
        result.append(node)
        result.extend(_flatten_progress_nodes(node.get("children", [])))
    return result


def _flatten_leaf_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in nodes:
        children = node.get("children", [])
        if children:
            result.extend(_flatten_leaf_nodes(children))
        else:
            result.append(node)
    return result


def _find_progress_node(nodes: list[dict[str, Any]], progress_node_ref: str) -> dict[str, Any] | None:
    for node in _flatten_progress_nodes(nodes):
        if node.get("progress_node_ref") == progress_node_ref:
            return node
    return None


def _first_text(*values: object | None) -> str:
    for value in values:
        if isinstance(value, (list, tuple)):
            nested = _first_text(*value)
            if nested:
                return nested
            continue
        text = truncate_text(value, max_chars=320)
        if text:
            return text
    return "内容待补充"


def _latest_turn_feedback(turns: list[dict[str, Any]] | dict[str, Any]) -> str | None:
    turn_list = [turns] if isinstance(turns, dict) else turns
    for turn in reversed(turn_list):
        if not isinstance(turn, dict):
            continue
        feedback_text = truncate_text(turn.get("feedback_text"), max_chars=640)
        if feedback_text and feedback_text != PENDING_FEEDBACK_TEXT:
            return feedback_text
        answers = turn.get("answers")
        if not isinstance(answers, list):
            continue
        for answer in reversed(answers):
            if not isinstance(answer, dict):
                continue
            answer_feedback = truncate_text(answer.get("feedback_text"), max_chars=640)
            if answer_feedback and answer_feedback != PENDING_FEEDBACK_TEXT:
                return answer_feedback
    return None
