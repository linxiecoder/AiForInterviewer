"""Progress Tree v2 initial generation pipeline."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from app.application.polish.progress_context import has_sufficient_progress_context, truncate_text
from app.application.polish.progress_evidence import build_progress_prompt_context
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
)
from app.application.polish.progress_v2_prompts import (
    POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
    POLISH_PROGRESS_GLOBAL_UNDERSTANDING_PROMPT_VERSION,
    POLISH_PROGRESS_GLOBAL_UNDERSTANDING_SCHEMA_ID,
    POLISH_PROGRESS_GLOBAL_UNDERSTANDING_TASK_TYPE,
    POLISH_PROGRESS_TREE_CRITIC_REFINER_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_CRITIC_REFINER_SCHEMA_ID,
    POLISH_PROGRESS_TREE_CRITIC_REFINER_TASK_TYPE,
    POLISH_PROGRESS_TREE_DRAFT_PLAN_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_DRAFT_PLAN_SCHEMA_ID,
    POLISH_PROGRESS_TREE_DRAFT_PLAN_TASK_TYPE,
    POLISH_PROGRESS_TREE_GROUNDED_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_ID,
    POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
    POLISH_PROGRESS_TREE_GROUNDING_TASK_TYPE,
    POLISH_PROGRESS_TREE_V2_CONTRACT_IDS,
    build_progress_quality_first_menu_prompt,
    build_progress_global_understanding_prompt,
    build_progress_tree_critic_refiner_prompt,
    build_progress_tree_draft_plan_prompt,
    build_progress_tree_grounding_prompt,
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
PROGRESS_TREE_V2_PIPELINE_PROMPT_VERSION = "polish_progress_tree_v2_pipeline"

_RESUME_DEEP_DIVE = "resume_deep_dive"
_JD_GAP_LEARNING = "jd_gap_learning"
_DISPLAY_CATEGORY_TITLES = {
    _RESUME_DEEP_DIVE: "深度打磨类",
    _JD_GAP_LEARNING: "补齐学习类",
}
_ALLOWED_CATEGORIES = set(_DISPLAY_CATEGORY_TITLES)
_ALLOWED_BASIS_TYPES = {"resume_signal", "jd_requirement", "match_gap", "mixed"}
_UNTRUSTED_LLM_METADATA_KEYS = {"generated_at", "model_name", "session_id", "job_id", "resume_id"}
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
_DEEP_DIVE_SOURCE_TYPES = {
    "resume_project",
    "resume_skill",
    "resume_work_experience",
    "matched_points",
    "match_focus",
    "interview_focus",
    "turn_feedback",
    "asset_summary",
    "resume_summary",
}
_GAP_LEARNING_SOURCE_TYPES = {
    "job_requirement",
    "job_responsibility",
    "match_gap",
    "match_focus",
    "match_suggested_question",
}

_ALLOWED_DIFFICULTY_LEVELS = {"basic", "intermediate", "advanced"}
_ALLOWED_CONFIDENCE_LEVELS = {"high", "medium", "low"}
_ALLOWED_GROUNDING_STATUSES = {
    "strongly_grounded",
    "partially_grounded",
    "weakly_grounded",
    "ungrounded",
}
_ALLOWED_NODE_TYPES = {
    "project_deep_dive",
    "technical_depth",
    "system_design",
    "architecture_tradeoff",
    "production_engineering",
    "business_understanding",
    "behavioral_scenario",
    "communication_structure",
    "job_gap",
    "resume_claim_validation",
}
_ALLOWED_INTERVIEW_METHODS = {
    "experience_probe",
    "contribution_clarification",
    "technical_deep_dive",
    "architecture_tradeoff_discussion",
    "failure_recovery_review",
    "metric_validation",
    "business_impact_review",
    "scenario_walkthrough",
    "gap_explanation",
    "communication_structuring",
    "learning_plan",
}
_LEGACY_METHOD_MAP = {
    "authenticity_probe": "experience_probe",
    "contribution_boundary_probe": "contribution_clarification",
    "technical_principle_probe": "technical_deep_dive",
    "architecture_tradeoff_probe": "architecture_tradeoff_discussion",
    "failure_recovery_probe": "failure_recovery_review",
    "metric_validation_probe": "metric_validation",
    "business_impact_probe": "business_impact_review",
    "scenario_roleplay_probe": "scenario_walkthrough",
    "risk_defense_probe": "gap_explanation",
    "communication_clarity_probe": "communication_structuring",
}
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
_SOURCE_SENTENCE_PREFIXES = (
    "面向",
    "针对",
    "负责",
    "具备",
    "熟悉",
    "了解",
    "理解",
    "掌握",
    "参与",
    "主导",
    "5年以上",
    "3年以上",
    "2年以上",
    "要求",
    "任职要求",
    "岗位要求",
)
_SOURCE_SENTENCE_MARKERS = (
    "年经验",
    "研发经验",
    "工作经验",
    "准确率不足",
    "问题",
)
_SOURCE_SENTENCE_PREFIX_EXCEPTIONS = (
    "面向对象",
)
_SOURCE_SENTENCE_MARKER_EXCEPTIONS = (
    "问题定位",
)
_SOURCE_EXCERPT_LABEL_MARKERS = (
    "领域",
    "部门",
    "业务",
    "专业术语",
    "准确率",
    "不足",
    "故障模式",
    "任职要求",
    "岗位要求",
    "研发经验",
    "工作经验",
)
_SOURCE_EXCERPT_SOURCE_MARKERS = (
    "面向",
    "针对",
    "负责",
    "具备",
    "熟悉",
    "要求",
    "问题",
    "需要",
    "结合",
    "职责",
    "经验",
    "任职",
    "岗位",
)
_SOURCE_EXCERPT_MIN_LABEL_CHARS = 10
_SOURCE_EXCERPT_MIN_SOURCE_COVERAGE = 0.2
_EXAM_POINT_DERIVATION_LOW_CONFIDENCE = "exam_point_derivation_low_confidence"
_PIPELINE_TASK_TYPES = [
    POLISH_PROGRESS_GLOBAL_UNDERSTANDING_TASK_TYPE,
    POLISH_PROGRESS_TREE_DRAFT_PLAN_TASK_TYPE,
    POLISH_PROGRESS_TREE_CRITIC_REFINER_TASK_TYPE,
    POLISH_PROGRESS_TREE_GROUNDING_TASK_TYPE,
]
_PIPELINE_PROMPT_VERSIONS = [
    POLISH_PROGRESS_GLOBAL_UNDERSTANDING_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_DRAFT_PLAN_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_CRITIC_REFINER_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_GROUNDED_PROMPT_VERSION,
]


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
                    contract_ids=POLISH_PROGRESS_TREE_V2_CONTRACT_IDS,
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
            return _quality_first_failed_artifacts(
                context,
                reason="quality_first_no_usable_nodes",
                validation_errors=[
                    {
                        "field": "menu_categories.nodes",
                        "code": "empty",
                        "reason": "Quality-first planner returned no usable nodes.",
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


class PolishProgressTreeV2Pipeline:
    """Deprecated four-task v2 chain kept temporarily for explicit test-only cleanup."""

    def __init__(self, transport: LlmTransport | None) -> None:
        self._transport = transport

    def generate_initial(self, context: dict[str, Any]) -> dict[str, Any]:
        if not has_sufficient_progress_context(context):
            return _insufficient_artifacts(context)
        if self._transport is None:
            return _failed_artifacts(context, reason="llm_transport_missing")

        prompt_context = build_progress_prompt_context(context, purpose="initial_plan")
        selected_chunks = prompt_context["selected_evidence_chunks"]
        allowed_chunk_ids = _selected_chunk_ids(selected_chunks)
        pipeline_status = "success"
        failure_reason = None
        local_fallback_only = False

        try:
            global_payload = self._call(
                task_type=POLISH_PROGRESS_GLOBAL_UNDERSTANDING_TASK_TYPE,
                context=context,
                evidence_bundle=build_progress_global_understanding_prompt(context),
            )
        except _LLM_ERRORS:
            global_payload = _fallback_global_understanding_payload(context, selected_chunks)
            pipeline_status = "partial"
            failure_reason = "global_understanding_failed"
            local_fallback_only = True

        global_understanding = _normalize_global_understanding(global_payload)
        if global_understanding is None:
            global_payload = _fallback_global_understanding_payload(context, selected_chunks)
            global_understanding = _normalize_global_understanding(global_payload)
            pipeline_status = "partial"
            failure_reason = "global_understanding_failed"
            local_fallback_only = True

        if local_fallback_only:
            draft_payload = _fallback_draft_plan_payload(context, selected_chunks, allowed_chunk_ids)
        else:
            try:
                draft_payload = self._call(
                    task_type=POLISH_PROGRESS_TREE_DRAFT_PLAN_TASK_TYPE,
                    context=context,
                    evidence_bundle=build_progress_tree_draft_plan_prompt(context, global_understanding),
                )
            except _LLM_ERRORS:
                draft_payload = _fallback_draft_plan_payload(context, selected_chunks, allowed_chunk_ids)
                pipeline_status = "partial"
                failure_reason = "draft_plan_failed"
                local_fallback_only = True

        draft_nodes = _normalize_draft_plan(
            draft_payload,
            context=context,
            allowed_chunk_ids=allowed_chunk_ids,
            selected_chunks=selected_chunks,
        )
        draft_quality_failure = _quality_gate_failure_reason(draft_nodes, selected_chunks)
        if not draft_nodes or draft_quality_failure:
            draft_payload = _fallback_draft_plan_payload(context, selected_chunks, allowed_chunk_ids)
            draft_nodes = _normalize_draft_plan(
                draft_payload,
                context=context,
                allowed_chunk_ids=allowed_chunk_ids,
                selected_chunks=selected_chunks,
            )
            pipeline_status = "partial"
            failure_reason = failure_reason or draft_quality_failure or "draft_plan_failed"
            local_fallback_only = True
        if not draft_nodes:
            return _failed_artifacts(context, reason="draft_plan_failed")

        low_confidence_flags = _low_confidence_flags(global_payload) + _low_confidence_flags(draft_payload)

        try:
            if local_fallback_only:
                raise LlmTransportResponseError("skip critic/refiner after local fallback")
            critic_payload = self._call(
                task_type=POLISH_PROGRESS_TREE_CRITIC_REFINER_TASK_TYPE,
                context=context,
                evidence_bundle=build_progress_tree_critic_refiner_prompt(
                    context,
                    global_understanding,
                    {"status": "ready", "nodes": draft_nodes},
                ),
            )
            refined_nodes = _normalize_refined_plan(
                critic_payload,
                context=context,
                allowed_chunk_ids=allowed_chunk_ids,
                selected_chunks=selected_chunks,
            )
            refined_quality_failure = _quality_gate_failure_reason(refined_nodes, selected_chunks)
            if not refined_nodes or refined_quality_failure:
                raise LlmTransportResponseError(refined_quality_failure or "critic returned no usable nodes")
            quality_review = _quality_review_summary(critic_payload.get("quality_review"))
            low_confidence_flags.extend(_low_confidence_flags(critic_payload))
        except _LLM_ERRORS:
            refined_nodes = draft_nodes
            quality_review = {"status": "fallback_to_draft"}
            pipeline_status = "partial"
            failure_reason = failure_reason or "critic_refiner_failed"
            low_confidence_flags.append("critic_refiner_failed")

        try:
            if local_fallback_only:
                raise LlmTransportResponseError("skip grounding after local fallback")
            grounding_payload = self._call(
                task_type=POLISH_PROGRESS_TREE_GROUNDING_TASK_TYPE,
                context=context,
                evidence_bundle=build_progress_tree_grounding_prompt(
                    context,
                    global_understanding,
                    {"status": "ready", "nodes": refined_nodes},
                ),
            )
            grounded_nodes = _normalize_grounded_plan(
                grounding_payload,
                context=context,
                allowed_chunk_ids=allowed_chunk_ids,
                selected_chunks=selected_chunks,
            )
            grounded_quality_failure = _quality_gate_failure_reason(grounded_nodes, selected_chunks)
            if not grounded_nodes or grounded_quality_failure:
                raise LlmTransportResponseError(grounded_quality_failure or "grounding returned no usable nodes")
            grounding_summary = _grounding_summary(grounding_payload.get("grounding_summary"))
            initial_state = _initial_state_from_nodes(
                grounded_nodes,
                raw_state=grounding_payload.get("initial_progress_tree_state"),
            )
            low_confidence_flags.extend(_low_confidence_flags(grounding_payload))
        except _LLM_ERRORS:
            grounded_nodes = _fallback_grounded_nodes(refined_nodes)
            grounding_summary = {"status": "fallback", "evidence_gaps": ["grounding_failed"]}
            initial_state = _initial_state_from_nodes(grounded_nodes, raw_state=None)
            pipeline_status = "partial"
            failure_reason = failure_reason or "grounding_failed"
            low_confidence_flags.append("grounding_failed")

        final_quality_failure = _quality_gate_failure_reason(grounded_nodes, selected_chunks)
        if final_quality_failure:
            grounded_nodes = _normalize_draft_plan(
                _fallback_draft_plan_payload(context, selected_chunks, allowed_chunk_ids),
                context=context,
                allowed_chunk_ids=allowed_chunk_ids,
                selected_chunks=selected_chunks,
            )
            grounding_summary = {"status": "fallback", "evidence_gaps": [final_quality_failure]}
            initial_state = _initial_state_from_nodes(grounded_nodes, raw_state=None)
            pipeline_status = "partial"
            failure_reason = failure_reason or final_quality_failure
            low_confidence_flags.append(final_quality_failure)

        if not grounded_nodes:
            return _failed_artifacts(context, reason="grounded_plan_failed")

        metadata = {
            "pipeline_status": pipeline_status,
            "global_understanding_summary": _global_understanding_summary(global_understanding),
            "quality_review_summary": quality_review,
            "grounding_summary": grounding_summary,
            "task_types": list(_PIPELINE_TASK_TYPES),
            "prompt_versions": list(_PIPELINE_PROMPT_VERSIONS),
            "low_confidence_flags": _dedupe_strings(low_confidence_flags, limit=20),
            "failure_reason": failure_reason,
        }
        plan = {
            "schema_id": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
            "prompt_version": PROGRESS_TREE_V2_PIPELINE_PROMPT_VERSION,
            "status": PROGRESS_TREE_STATUS_READY,
            "context_digest": context["content_digest"],
            "nodes": grounded_nodes[:10],
            "v2_metadata": metadata,
        }
        return {
            "status": PROGRESS_TREE_STATUS_READY,
            "progress_tree_plan": plan,
            "progress_tree_state": initial_state,
            "progress_percent": 0,
        }

    def _call(
        self,
        *,
        task_type: str,
        context: dict[str, Any],
        evidence_bundle: dict[str, Any],
    ) -> dict[str, Any]:
        if self._transport is None:
            raise LlmTransportUnavailableError("transport missing")
        result = self._transport.generate(
            LlmTransportRequest(
                contract_ids=POLISH_PROGRESS_TREE_V2_CONTRACT_IDS,
                task_type=task_type,
                input_refs=_input_refs(context),
                evidence_bundle=evidence_bundle,
            )
        )
        return result.result


_LLM_ERRORS = (
    LlmTransportConfigurationError,
    LlmTransportUnavailableError,
    LlmTransportResponseError,
)


def _normalize_global_understanding(payload: object) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    if payload.get("status") not in {None, "success", "partial"}:
        return None
    return {
        "schema_id": _metadata_value(payload, "schema_id", POLISH_PROGRESS_GLOBAL_UNDERSTANDING_SCHEMA_ID),
        "schema_version": _metadata_value(payload, "schema_version", POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION),
        "prompt_version": _metadata_value(
            payload,
            "prompt_version",
            POLISH_PROGRESS_GLOBAL_UNDERSTANDING_PROMPT_VERSION,
        ),
        "status": payload.get("status") or "success",
        "candidate_profile_summary": _dict_value(payload.get("candidate_profile_summary")),
        "target_role_competency_map": _list_value(payload.get("target_role_competency_map"), limit=20),
        "resume_evidence_map": _list_value(payload.get("resume_evidence_map"), limit=30),
        "role_gap_risk_map": _list_value(payload.get("role_gap_risk_map"), limit=20),
        "interview_strategy": _dict_value(payload.get("interview_strategy")),
        "recommended_progress_axes": _list_value(payload.get("recommended_progress_axes"), limit=12),
        "low_confidence_flags": _string_list(payload.get("low_confidence_flags"), limit=20),
    }


def _fallback_global_understanding_payload(
    context: dict[str, Any],
    selected_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    job_requirement = _first_chunk_text(selected_chunks, {"job_requirement", "job_responsibility"})
    resume_evidence = _first_chunk_text(
        selected_chunks,
        {"resume_project", "resume_skill", "resume_work_experience", "resume_summary"},
    )
    match_gap = _first_chunk_text(selected_chunks, {"match_gap", "match_focus"})
    job = context.get("job_snapshot", {})
    resume = context.get("resume_snapshot", {})
    positioning = "候选人具备可追问的岗位/简历交集，但全局理解模型调用失败，当前使用低置信本地摘要。"
    if resume_evidence or job_requirement:
        positioning = (
            f"候选人围绕岗位「{truncate_text(job.get('title'), max_chars=80) or '目标岗位'}」"
            f"具备初步可追问证据：{truncate_text(resume_evidence or job_requirement, max_chars=180)}"
        )
    return {
        "schema_id": POLISH_PROGRESS_GLOBAL_UNDERSTANDING_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_GLOBAL_UNDERSTANDING_PROMPT_VERSION,
        "status": "partial",
        "candidate_profile_summary": {
            "one_sentence_positioning": positioning,
            "experience_level_assessment": "全局理解 LLM 调用失败，经验层级暂按低置信处理。",
            "core_strengths": _dedupe_strings([resume_evidence, job_requirement], limit=4),
            "core_risks": _dedupe_strings([match_gap, "全局理解模型调用失败，需在后续节点保持低置信标记"], limit=4),
            "most_interviewable_projects": _dedupe_strings([resume_evidence], limit=3),
            "least_supported_claims": ["业务结果、指标和贡献边界需继续追问"],
            "communication_risk_notes": ["避免把本地摘要当作完整候选人画像。"],
        },
        "target_role_competency_map": [
            {
                "competency_id": "fallback_target_role_competency",
                "title": truncate_text(job_requirement, max_chars=160) or "岗位核心能力",
                "importance": "high",
                "job_requirement_refs": _dedupe_strings([job_requirement], limit=3),
                "why_it_matters": "该能力来自 selected evidence chunks，是打磨进展树的最低可用岗位锚点。",
                "expected_interview_depth": "intermediate",
            }
        ],
        "resume_evidence_map": [
            {
                "evidence_id": "fallback_resume_evidence",
                "source_area": "project",
                "title": truncate_text(resume.get("title"), max_chars=120) or "简历证据",
                "evidence_summary": resume_evidence,
                "explicit_evidence": _dedupe_strings([resume_evidence], limit=3),
                "reasonable_inferences": [],
                "unsupported_or_weak_parts": ["全局理解模型调用失败，证据地图未完整展开"],
                "interview_value": "medium",
            }
        ],
        "role_gap_risk_map": [
            {
                "risk_id": "fallback_global_understanding_risk",
                "risk_title": "全局理解结果低置信",
                "risk_type": "other",
                "severity": "medium",
                "evidence_summary": match_gap,
                "likely_interviewer_attack": "候选人能否用真实项目证明岗位要求。",
                "defense_strategy_hint": "后续节点必须继续绑定简历和岗位证据，不做无证据扩写。",
            }
        ],
        "interview_strategy": {
            "overall_strategy": "先用 selected evidence chunks 生成低置信但可用的进展树，再通过 critic/grounding 标记风险。",
            "recommended_sequence": ["项目真实性", "技术深度", "岗位缺口说明", "表达结构"],
            "high_value_attack_points": ["贡献边界", "指标验证"],
            "avoid_overfitting_notes": ["当前 global understanding 为 fallback，不应过度推断。"],
            "suggested_difficulty_curve": "先 intermediate，再 advanced。",
        },
        "recommended_progress_axes": [
            {
                "axis_id": "fallback_axis_authenticity",
                "title": "项目真实性与岗位证据锚定",
                "reason": "全局理解失败时仍可用 selected evidence chunks 形成最低可用节点。",
                "related_competency_ids": ["fallback_target_role_competency"],
                "related_evidence_ids": ["fallback_resume_evidence"],
                "related_risk_ids": ["fallback_global_understanding_risk"],
                "priority": 1,
            }
        ],
        "low_confidence_flags": ["global_understanding_failed", "global_understanding_fallback"],
    }


def _fallback_draft_plan_payload(
    context: dict[str, Any],
    selected_chunks: list[dict[str, Any]],
    allowed_chunk_ids: set[str],
) -> dict[str, Any]:
    nodes = _fallback_menu_nodes(context, selected_chunks, allowed_chunk_ids)
    resume_count = sum(1 for node in nodes if node.get("category") == _RESUME_DEEP_DIVE)
    gap_count = sum(1 for node in nodes if node.get("category") == _JD_GAP_LEARNING)
    low_confidence_flags = ["draft_plan_failed", "draft_plan_fallback"]
    if resume_count < 3:
        low_confidence_flags.append("insufficient_resume_evidence")
    if gap_count < 3:
        low_confidence_flags.append("insufficient_job_evidence")
    return {
        "schema_id": "polish_progress_tree_draft_plan_v2",
        "schema_version": "v2",
        "prompt_version": "polish_progress_tree_draft_plan_prompt_v2",
        "task_type": "polish_progress_tree_draft_plan",
        "status": "partial",
        "plan_quality_intent": {
            "tree_positioning": "LLM draft plan 失败后的本地面试菜单。",
            "target_interview_level": "intermediate",
            "planning_rationale": "优先从 selected evidence chunks 提取简历深度打磨项和 JD 补齐学习项。",
        },
        "progress_tree_plan": {"status": "partial", "nodes": nodes},
        "coverage_summary": {
            "covered_competencies": _dedupe_strings(
                [node.get("display_title", "") for node in nodes if node.get("category") == _JD_GAP_LEARNING],
                limit=6,
            ),
            "covered_projects": _dedupe_strings(
                [node.get("display_title", "") for node in nodes if node.get("category") == _RESUME_DEEP_DIVE],
                limit=6,
            ),
            "covered_job_gaps": _dedupe_strings(
                [gap for node in nodes for gap in node.get("related_match_gaps", [])],
                limit=6,
            ),
            "covered_risks": ["LLM draft plan failed"],
            "missing_but_important": [],
        },
        "critic_notes_for_next_task": ["draft_plan_fallback"],
        "low_confidence_flags": low_confidence_flags,
    }


def _fallback_menu_nodes(
    context: dict[str, Any],
    selected_chunks: list[dict[str, Any]],
    allowed_chunk_ids: set[str],
) -> list[dict[str, Any]]:
    resume_sources = _menu_sources(selected_chunks, _DEEP_DIVE_SOURCE_TYPES, allowed_chunk_ids=allowed_chunk_ids)
    gap_sources = _menu_sources(selected_chunks, _GAP_LEARNING_SOURCE_TYPES, allowed_chunk_ids=allowed_chunk_ids)
    job_basis = _first_chunk_text(selected_chunks, {"job_requirement", "job_responsibility"})
    resume_basis = _first_chunk_text(
        selected_chunks,
        {"resume_project", "resume_skill", "resume_work_experience", "resume_summary"},
    )
    match_gap = _first_chunk_text(selected_chunks, {"match_gap", "match_focus", "match_suggested_question"})

    nodes: list[dict[str, Any]] = []
    for index, source in enumerate(resume_sources[:3], start=1):
        display_title = _menu_title_from_text(source["text"], _RESUME_DEEP_DIVE)
        evidence_ids = _dedupe_strings([source["chunk_id"]], limit=3)
        related_resume_evidence = _dedupe_strings([source["text"], resume_basis], limit=3)
        nodes.append(
            {
                "progress_node_ref": _node_ref(context["content_digest"], f"fallback:D{index}:{source['text']}"),
                "node_code": f"D{index}",
                "category": _RESUME_DEEP_DIVE,
                "display_category_title": _DISPLAY_CATEGORY_TITLES[_RESUME_DEEP_DIVE],
                "display_title": display_title,
                "exam_point": display_title,
                "basis_type": "resume_signal",
                "resume_signal": source["text"],
                "jd_basis": job_basis or None,
                "depth_goal": f"准备到能讲清「{display_title}」的业务场景、个人负责范围、关键取舍、异常处理和可验证结果。",
                "preparation_goal": f"训练用户把「{display_title}」从简历线索讲成可追问、可评分的项目经历。",
                "first_question": f"请结合简历中的这条线索，说明你在「{display_title}」中具体负责什么、为什么这样设计，以及如何验证结果。",
                "follow_up_focus": [
                    "继续追问个人负责范围和协作边界",
                    "继续追问关键方案的取舍依据和替代方案",
                    "继续追问上线验证、指标变化或异常恢复过程",
                ],
                "expected_answer_signals": [
                    "能把场景、动作、技术取舍和结果按顺序讲清楚",
                    "能区分个人贡献、团队协作和外部依赖",
                    "能给出可验证证据或明确说明证据边界",
                ],
                "common_loss_risks": [
                    "只复述技术名词，缺少具体场景和个人动作",
                    "把团队成果全部归为个人成果",
                    "对异常场景、指标或验证方式准备不足",
                ],
                "related_job_requirements": _dedupe_strings([job_basis], limit=3),
                "related_resume_evidence": related_resume_evidence,
                "related_match_gaps": _dedupe_strings([match_gap], limit=3),
                "evidence_chunk_ids": evidence_ids,
                "evidence_bindings": _fallback_evidence_bindings(selected_chunks, evidence_ids),
                "grounding_status": "partially_grounded" if evidence_ids else "weakly_grounded",
                "confidence_level": "medium" if evidence_ids else "low",
                "children": [],
            }
        )

    for index, source in enumerate(gap_sources[:3], start=1):
        display_title = _menu_title_from_text(source["text"], _JD_GAP_LEARNING)
        evidence_ids = _dedupe_strings([source["chunk_id"]], limit=3)
        related_job_requirements = _dedupe_strings([source["text"], job_basis], limit=3)
        nodes.append(
            {
                "progress_node_ref": _node_ref(context["content_digest"], f"fallback:A{index}:{source['text']}"),
                "node_code": f"A{index}",
                "category": _JD_GAP_LEARNING,
                "display_category_title": _DISPLAY_CATEGORY_TITLES[_JD_GAP_LEARNING],
                "display_title": display_title,
                "exam_point": display_title,
                "basis_type": "jd_requirement" if source["source_type"].startswith("job_") else "match_gap",
                "resume_signal": resume_basis or None,
                "jd_basis": source["text"],
                "depth_goal": f"准备到能说明「{display_title}」的核心原理、常见方案、适用边界，并诚实区分已实践经验与学习补齐部分。",
                "preparation_goal": f"训练用户把 JD 中的「{display_title}」讲成原理、方案和补齐计划，而不是伪装成已做经验。",
                "first_question": f"JD 提到「{display_title}」时，你会如何说明它的原理、适用场景和你当前的补齐计划？",
                "follow_up_focus": [
                    "继续追问核心概念、典型架构和适用边界",
                    "继续追问与简历已有项目的可迁移经验",
                    "继续追问短期学习计划和可验证练习方式",
                ],
                "expected_answer_signals": [
                    "能解释基础原理和常见实践，不把学习项说成已主导经验",
                    "能连接到简历中相邻的工程经验",
                    "能给出明确的补齐路径和验证方式",
                ],
                "common_loss_risks": [
                    "把 JD 关键词泛化成口号，无法解释原理",
                    "强行声称做过但缺少简历证据",
                    "只说会学习，缺少具体补齐路径",
                ],
                "related_job_requirements": related_job_requirements,
                "related_resume_evidence": _dedupe_strings([resume_basis], limit=3),
                "related_match_gaps": _dedupe_strings([match_gap], limit=3),
                "evidence_chunk_ids": evidence_ids,
                "evidence_bindings": _fallback_evidence_bindings(selected_chunks, evidence_ids),
                "grounding_status": "partially_grounded" if evidence_ids else "weakly_grounded",
                "confidence_level": "medium" if evidence_ids else "low",
                "children": [],
            }
        )
    return [_sanitize_node_display_fields(node) for node in nodes]


def _normalize_quality_first_menu_payload(
    payload: dict[str, Any],
    *,
    context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any], list[dict[str, Any]]] | None:
    status = str(payload.get("status") or "").strip().lower()
    if status not in {"ready", "success", "partial"}:
        return None
    categories = payload.get("menu_categories")
    if not isinstance(categories, list):
        return None

    nodes: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    low_confidence_flags = _sanitize_string_list(payload.get("low_confidence_flags"), limit=20)
    deferred_candidates = _normalize_quality_first_deferred_candidates(
        payload.get("deferred_candidates"),
        context_digest=context["content_digest"],
    )
    metadata = payload.get("metadata")
    if isinstance(metadata, dict) and _UNTRUSTED_LLM_METADATA_KEYS.intersection(metadata):
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
        "status": "ready",
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
    if text == "explicit_evidence":
        return fallback, ["legacy_basis_type_normalized"]
    if text == "reasonable_inference":
        return ("match_gap" if category == _JD_GAP_LEARNING else "mixed"), ["legacy_basis_type_normalized"]
    if text == "unsupported":
        return fallback, ["unsupported_basis_type_normalized"]
    return fallback, []


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
    if "unsupported_basis_type_normalized" in _string_list(node.get("low_confidence_flags"), limit=8):
        if _quality_first_node_low_support(node):
            return "模型将节点标成 unsupported 且缺少证据，延后作为候选项。", "quality_first_unsupported_node_deferred"
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
        return "quality_first_menu_categories_missing"

    has_raw_nodes = any(isinstance(item.get("nodes"), list) and item.get("nodes") for item in valid_categories)
    if not has_raw_nodes:
        return "quality_first_no_usable_nodes"
    return "quality_first_schema_invalid"


def _quality_first_validation_errors(payload: dict[str, Any], *, reason: str) -> list[dict[str, str]]:
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


def _normalize_draft_plan(
    payload: object,
    *,
    context: dict[str, Any],
    allowed_chunk_ids: set[str],
    selected_chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plan_payload = _plan_payload(payload, "progress_tree_plan")
    return _normalize_nodes(
        plan_payload.get("nodes"),
        context=context,
        allowed_chunk_ids=allowed_chunk_ids,
        selected_chunks=selected_chunks,
    )


def _normalize_refined_plan(
    payload: object,
    *,
    context: dict[str, Any],
    allowed_chunk_ids: set[str],
    selected_chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plan_payload = _plan_payload(payload, "refined_progress_tree_plan")
    return _normalize_nodes(
        plan_payload.get("nodes"),
        context=context,
        allowed_chunk_ids=allowed_chunk_ids,
        selected_chunks=selected_chunks,
    )


def _normalize_grounded_plan(
    payload: object,
    *,
    context: dict[str, Any],
    allowed_chunk_ids: set[str],
    selected_chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plan_payload = _plan_payload(payload, "progress_tree_plan")
    return _normalize_nodes(
        plan_payload.get("nodes"),
        context=context,
        allowed_chunk_ids=allowed_chunk_ids,
        selected_chunks=selected_chunks,
        default_grounding_status="partially_grounded",
    )


def _normalize_nodes(
    raw_nodes: object,
    *,
    context: dict[str, Any],
    allowed_chunk_ids: set[str],
    selected_chunks: list[dict[str, Any]],
    default_grounding_status: str = "partially_grounded",
) -> list[dict[str, Any]]:
    if not isinstance(raw_nodes, list):
        return []
    nodes = [
        node
        for index, raw_node in enumerate(raw_nodes[:10], start=1)
        if (
            node := _normalize_v2_node(
                raw_node,
                index=index,
                context_digest=context["content_digest"],
                allowed_chunk_ids=allowed_chunk_ids,
                selected_chunks=selected_chunks,
                default_grounding_status=default_grounding_status,
            )
        )
        is not None
    ]
    return nodes


def _normalize_v2_node(
    item: object,
    *,
    index: int,
    context_digest: str,
    allowed_chunk_ids: set[str],
    selected_chunks: list[dict[str, Any]],
    default_grounding_status: str,
) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    raw_title = item.get("display_title") or item.get("exam_point") or item.get("title")
    display_title = _sanitize_display_text(raw_title, max_chars=120)
    expected_capability = _sanitize_display_text(item.get("expected_capability"), max_chars=600)

    category = _category_value(item)
    display_category_title = _sanitize_display_text(
        item.get("display_category_title") or _DISPLAY_CATEGORY_TITLES[category],
        max_chars=80,
    )
    exam_point = _sanitize_display_text(item.get("exam_point") or display_title, max_chars=160)
    resume_signal = _sanitize_optional_text(
        item.get("resume_signal") or _first_string(item.get("related_resume_evidence")),
        max_chars=480,
    )
    jd_basis = _sanitize_optional_text(
        item.get("jd_basis") or _first_string(item.get("related_job_requirements")),
        max_chars=480,
    )
    display_title, display_low_confidence = _exam_point_label(
        display_title or item.get("title") or item.get("exam_point"),
        category=category,
        item=item,
        selected_chunks=selected_chunks,
    )
    exam_point, exam_low_confidence = _exam_point_label(
        exam_point or display_title,
        category=category,
        item=item,
        selected_chunks=selected_chunks,
    )
    if not display_title:
        return None
    if not exam_point:
        exam_point = display_title
    label_low_confidence = display_low_confidence or exam_low_confidence
    basis_type = _basis_type_value(item, category, resume_signal=resume_signal, jd_basis=jd_basis)
    depth_goal = _sanitize_display_text(
        item.get("depth_goal")
        or expected_capability
        or _default_depth_goal(category, exam_point),
        max_chars=600,
    )
    preparation_goal = _sanitize_display_text(
        item.get("preparation_goal")
        or item.get("interview_intent")
        or _default_preparation_goal(category, exam_point),
        max_chars=600,
    )
    first_question = _sanitize_display_text(
        item.get("first_question")
        or item.get("recommended_first_question")
        or _default_first_question(category, exam_point),
        max_chars=600,
    )

    node_ref = truncate_text(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
    evidence_bindings = _evidence_bindings(item.get("evidence_bindings"), allowed_chunk_ids)
    evidence_chunk_ids = _evidence_chunk_ids(item.get("evidence_chunk_ids"), allowed_chunk_ids)
    children = [
        child
        for child_index, child_item in enumerate(_list_value(item.get("children"), limit=10), start=1)
        if (
            child := _normalize_v2_node(
                child_item,
                index=(index * 100) + child_index,
                context_digest=context_digest,
                allowed_chunk_ids=allowed_chunk_ids,
                selected_chunks=selected_chunks,
                default_grounding_status=default_grounding_status,
            )
        )
        is not None
    ]
    related_job_requirements = _sanitize_string_list(item.get("related_job_requirements"), limit=6)
    related_resume_evidence = _sanitize_string_list(item.get("related_resume_evidence"), limit=6)
    related_match_gaps = _sanitize_string_list(item.get("related_match_gaps"), limit=6)
    if not related_match_gaps:
        related_match_gaps = _sanitize_string_list(item.get("missing_points"), limit=6)
    follow_up_focus = _sanitize_string_list(item.get("follow_up_focus"), limit=8)
    if not follow_up_focus:
        follow_up_focus = _sanitize_string_list(item.get("follow_up_directions"), limit=8)
    if not follow_up_focus:
        follow_up_focus = _default_follow_up_focus(category, exam_point)
    expected_answer_signals = _sanitize_string_list(item.get("expected_answer_signals"), limit=8)
    if not expected_answer_signals:
        expected_answer_signals = _default_expected_answer_signals(category)
    common_loss_risks = _sanitize_string_list(item.get("common_loss_risks"), limit=8)
    if not common_loss_risks:
        common_loss_risks = _sanitize_string_list(item.get("red_flags"), limit=8)
    if not common_loss_risks:
        common_loss_risks = _default_common_loss_risks(category)
    interview_method = _interview_method_value(item, category)
    low_confidence_flags = _sanitize_string_list(item.get("low_confidence_flags"), limit=8)
    if label_low_confidence:
        low_confidence_flags = _dedupe_strings(
            [*low_confidence_flags, _EXAM_POINT_DERIVATION_LOW_CONFIDENCE],
            limit=8,
        )
    grounding_status = _enum_value(
        item.get("grounding_status"),
        _ALLOWED_GROUNDING_STATUSES,
        default_grounding_status,
    )
    confidence_level = _enum_value(item.get("confidence_level"), _ALLOWED_CONFIDENCE_LEVELS, "medium")
    if label_low_confidence:
        confidence_level = "low"
        if grounding_status in {"strongly_grounded", "partially_grounded"}:
            grounding_status = "weakly_grounded"
    node = {
        "progress_node_ref": node_ref or _node_ref(context_digest, f"{index}:{display_title}"),
        "node_code": _sanitize_display_text(item.get("node_code"), max_chars=20) or _default_node_code(category, index),
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
        "common_loss_risks": common_loss_risks,
        "title": display_title,
        "node_type": _enum_value(item.get("node_type"), _ALLOWED_NODE_TYPES, "resume_claim_validation"),
        "interview_intent": preparation_goal,
        "expected_capability": depth_goal,
        "interview_method": interview_method,
        "follow_up_method": interview_method,
        "attack_style": interview_method,
        "difficulty_level": _enum_value(item.get("difficulty_level"), _ALLOWED_DIFFICULTY_LEVELS, "intermediate"),
        "priority": _bounded_int(item.get("priority"), lower=1, upper=999, fallback=index),
        "priority_reason": _sanitize_display_text(item.get("priority_reason"), max_chars=600)
        or "该节点具备岗位贴合和面试追问价值。",
        "related_job_requirements": related_job_requirements,
        "related_resume_evidence": related_resume_evidence,
        "related_match_gaps": related_match_gaps,
        "missing_points": related_match_gaps,
        "expected_answer_signals": expected_answer_signals,
        "red_flags": common_loss_risks,
        "recommended_first_question": first_question,
        "follow_up_directions": follow_up_focus,
        "evidence_chunk_ids": evidence_chunk_ids,
        "evidence_bindings": evidence_bindings,
        "grounding_status": grounding_status,
        "confidence_level": confidence_level,
        "low_confidence_flags": low_confidence_flags,
        "children": children[:10],
    }
    return _sanitize_node_display_fields(node)


def _fallback_grounded_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in nodes[:10]:
        copied = {**node}
        copied["grounding_status"] = "weakly_grounded"
        copied["confidence_level"] = "low"
        copied.setdefault("evidence_bindings", [])
        copied["low_confidence_flags"] = _dedupe_strings(
            [*copied.get("low_confidence_flags", []), "grounding_failed"],
            limit=8,
        )
        copied["children"] = _fallback_grounded_nodes(copied.get("children", []))
        result.append(copied)
    return result


def _initial_state_from_nodes(
    nodes: list[dict[str, Any]],
    *,
    raw_state: object,
) -> dict[str, Any]:
    flat_nodes = _flatten_v2_nodes(nodes)
    node_by_ref = {node["progress_node_ref"]: node for node in flat_nodes}
    node_states = []
    if isinstance(raw_state, dict):
        for item in raw_state.get("node_states", []):
            if not isinstance(item, dict):
                continue
            node_ref = truncate_text(item.get("progress_node_ref"), max_chars=120)
            if not node_ref or node_ref not in node_by_ref:
                continue
            node_states.append(
                {
                    "progress_node_ref": node_ref,
                    "status": _state_status(item.get("status")),
                    "completed_questions_count": _bounded_int(
                        item.get("completed_questions_count"),
                        lower=0,
                        upper=999,
                        fallback=0,
                    ),
                    "latest_feedback_summary": truncate_text(item.get("latest_feedback_summary"), max_chars=480),
                }
            )
    if not node_states:
        node_states = [
            {
                "progress_node_ref": node["progress_node_ref"],
                "status": "pending",
                "completed_questions_count": 0,
                "latest_feedback_summary": None,
            }
            for node in flat_nodes
        ]

    current_priority = _priority_from_state(raw_state, node_by_ref) or _fallback_priority(flat_nodes)
    state = {
        "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_READY if flat_nodes and current_priority else PROGRESS_TREE_STATUS_FAILED,
        "node_states": node_states,
        "current_priority": current_priority,
        "updated_from_turns_count": 0,
        "progress": {"progress_percent": 0},
    }
    if isinstance(raw_state, dict) and "initial_state_missing" in _string_list(
        raw_state.get("low_confidence_flags"),
        limit=10,
    ):
        state["failure_reason"] = "llm_state_invalid_state_fallback"
    if not isinstance(raw_state, dict):
        state["failure_reason"] = "llm_state_invalid_state_fallback"
    return state


def _priority_from_state(raw_state: object, node_by_ref: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if not isinstance(raw_state, dict):
        return None
    value = raw_state.get("current_priority")
    if not isinstance(value, dict):
        return None
    node_ref = truncate_text(value.get("progress_node_ref"), max_chars=120)
    if not node_ref or node_ref not in node_by_ref:
        return None
    node = node_by_ref[node_ref]
    return {
        "progress_node_ref": node_ref,
        "title": node["title"],
        "expected_capability": node["expected_capability"],
        "priority_reason": node.get("priority_reason"),
    }


def _fallback_priority(flat_nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not flat_nodes:
        return None
    risk_types = {"resume_claim_validation", "risk_defense", "job_gap", "project_deep_dive"}
    sorted_nodes = sorted(
        flat_nodes,
        key=lambda node: (
            0 if node.get("node_type") in risk_types else 1,
            _bounded_int(node.get("priority"), lower=1, upper=999, fallback=999),
        ),
    )
    node = sorted_nodes[0]
    return {
        "progress_node_ref": node["progress_node_ref"],
        "title": node["title"],
        "expected_capability": node["expected_capability"],
        "priority_reason": node.get("priority_reason"),
    }


def _insufficient_artifacts(context: dict[str, Any]) -> dict[str, Any]:
    plan = {
        "schema_id": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
        "prompt_version": PROGRESS_TREE_V2_PIPELINE_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "context_digest": context["content_digest"],
        "nodes": [],
        "v2_metadata": {
            "pipeline_status": "partial",
            "global_understanding_summary": {},
            "quality_review_summary": {},
            "grounding_summary": {},
            "task_types": [],
            "prompt_versions": [],
            "low_confidence_flags": ["insufficient_context"],
            "failure_reason": "insufficient_context",
        },
    }
    return {
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "progress_tree_plan": plan,
        "progress_tree_state": _empty_state(PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT),
        "progress_percent": 0,
    }


def _failed_artifacts(context: dict[str, Any], *, reason: str) -> dict[str, Any]:
    plan = {
        "schema_id": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
        "prompt_version": PROGRESS_TREE_V2_PIPELINE_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_FAILED,
        "context_digest": context["content_digest"],
        "nodes": [],
        "failure_reason": reason,
        "v2_metadata": {
            "pipeline_status": "partial",
            "global_understanding_summary": {},
            "quality_review_summary": {},
            "grounding_summary": {},
            "task_types": list(_PIPELINE_TASK_TYPES),
            "prompt_versions": list(_PIPELINE_PROMPT_VERSIONS),
            "low_confidence_flags": [reason],
            "failure_reason": reason,
        },
    }
    return {
        "status": PROGRESS_TREE_STATUS_FAILED,
        "progress_tree_plan": plan,
        "progress_tree_state": _empty_state(PROGRESS_TREE_STATUS_FAILED),
        "progress_percent": 0,
    }


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


def _plan_payload(payload: object, field_name: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    nested = payload.get(field_name)
    if isinstance(nested, dict):
        return nested
    plan = payload.get("plan")
    if isinstance(plan, dict):
        return plan
    return payload


def _global_understanding_summary(global_understanding: dict[str, Any]) -> dict[str, Any]:
    profile = _dict_value(global_understanding.get("candidate_profile_summary"))
    return {
        "one_sentence_positioning": _sanitize_optional_text(profile.get("one_sentence_positioning"), max_chars=240),
        "core_strengths": _sanitize_string_list(profile.get("core_strengths"), limit=5),
        "core_risks": _sanitize_string_list(profile.get("core_risks"), limit=5),
        "recommended_axes_count": len(_list_value(global_understanding.get("recommended_progress_axes"), limit=50)),
    }


def _quality_review_summary(value: object) -> dict[str, Any]:
    review = _dict_value(value)
    return {
        "personalization_score": _bounded_int(review.get("personalization_score"), lower=0, upper=100, fallback=0),
        "job_alignment_score": _bounded_int(review.get("job_alignment_score"), lower=0, upper=100, fallback=0),
        "interview_value_score": _bounded_int(review.get("interview_value_score"), lower=0, upper=100, fallback=0),
        "evidence_groundability_score": _bounded_int(
            review.get("evidence_groundability_score"),
            lower=0,
            upper=100,
            fallback=0,
        ),
        "structure_quality_score": _bounded_int(review.get("structure_quality_score"), lower=0, upper=100, fallback=0),
        "non_generic_score": _bounded_int(review.get("non_generic_score"), lower=0, upper=100, fallback=0),
        "overall_quality_score": _bounded_int(review.get("overall_quality_score"), lower=0, upper=100, fallback=0),
        "major_findings": _sanitize_string_list(review.get("major_findings"), limit=8),
    }


def _grounding_summary(value: object) -> dict[str, Any]:
    summary = _dict_value(value)
    return {
        "strongly_grounded_nodes_count": _bounded_int(
            summary.get("strongly_grounded_nodes_count"),
            lower=0,
            upper=999,
            fallback=0,
        ),
        "partially_grounded_nodes_count": _bounded_int(
            summary.get("partially_grounded_nodes_count"),
            lower=0,
            upper=999,
            fallback=0,
        ),
        "weakly_grounded_nodes_count": _bounded_int(
            summary.get("weakly_grounded_nodes_count"),
            lower=0,
            upper=999,
            fallback=0,
        ),
        "ungrounded_nodes_count": _bounded_int(
            summary.get("ungrounded_nodes_count"),
            lower=0,
            upper=999,
            fallback=0,
        ),
        "unsupported_claims": _sanitize_string_list(summary.get("unsupported_claims"), limit=8),
        "evidence_gaps": _sanitize_string_list(summary.get("evidence_gaps"), limit=8),
    }


def _evidence_bindings(value: object, allowed_chunk_ids: set[str]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        chunk_id = truncate_text(item.get("evidence_chunk_id"), max_chars=120)
        if not chunk_id or (allowed_chunk_ids and chunk_id not in allowed_chunk_ids):
            continue
        result.append(
            {
                "evidence_chunk_id": chunk_id,
                "source_type": truncate_text(item.get("source_type"), max_chars=80) or "other",
                "binding_reason": _sanitize_display_text(item.get("binding_reason"), max_chars=360)
                or "该证据支撑当前节点。",
                "supports_field": truncate_text(item.get("supports_field"), max_chars=80) or "interview_intent",
            }
        )
        if len(result) >= 12:
            break
    return result


def _evidence_chunk_ids(value: object, allowed_chunk_ids: set[str]) -> list[str]:
    return [
        item
        for item in _string_list(value, limit=20)
        if not allowed_chunk_ids or item in allowed_chunk_ids
    ]


def _selected_chunk_ids(selected_chunks: object) -> set[str]:
    if not isinstance(selected_chunks, list):
        return set()
    return {
        chunk["chunk_id"]
        for chunk in selected_chunks
        if isinstance(chunk, dict) and isinstance(chunk.get("chunk_id"), str)
    }


def _first_chunk_text(selected_chunks: list[dict[str, Any]], source_types: set[str]) -> str:
    for chunk in selected_chunks:
        if not isinstance(chunk, dict) or chunk.get("source_type") not in source_types:
            continue
        text = truncate_text(chunk.get("text") or chunk.get("title"), max_chars=480)
        if text:
            return text
    return ""


def _chunk_ids_for_types(
    selected_chunks: list[dict[str, Any]],
    source_types: set[str],
    *,
    allowed_chunk_ids: set[str],
    limit: int,
) -> list[str]:
    result: list[str] = []
    for chunk in selected_chunks:
        if not isinstance(chunk, dict) or chunk.get("source_type") not in source_types:
            continue
        chunk_id = chunk.get("chunk_id")
        if not isinstance(chunk_id, str) or chunk_id not in allowed_chunk_ids or chunk_id in result:
            continue
        result.append(chunk_id)
        if len(result) >= limit:
            break
    return result


def _fallback_evidence_bindings(
    selected_chunks: list[dict[str, Any]],
    evidence_chunk_ids: list[str],
) -> list[dict[str, str]]:
    evidence_id_set = set(evidence_chunk_ids)
    bindings: list[dict[str, str]] = []
    for chunk in selected_chunks:
        if not isinstance(chunk, dict):
            continue
        chunk_id = chunk.get("chunk_id")
        source_type = chunk.get("source_type")
        if not isinstance(chunk_id, str) or chunk_id not in evidence_id_set or not isinstance(source_type, str):
            continue
        if source_type in {"job_requirement", "job_responsibility"}:
            supports_field = "related_job_requirements"
            binding_reason = "岗位证据支撑该节点的追问方向。"
        elif source_type in {"match_gap", "match_focus"}:
            supports_field = "related_match_gaps"
            binding_reason = "匹配分析证据支撑该节点的失分风险说明。"
        else:
            supports_field = "related_resume_evidence"
            binding_reason = "简历证据支撑该节点的真实性和贡献边界验证。"
        bindings.append(
            {
                "evidence_chunk_id": chunk_id,
                "source_type": source_type,
                "binding_reason": binding_reason,
                "supports_field": supports_field,
            }
        )
    return bindings[:8]


def _exam_point_label(
    raw_label: object,
    *,
    category: str,
    item: dict[str, Any],
    selected_chunks: list[dict[str, Any]],
) -> tuple[str, bool]:
    label = _sanitize_display_text(raw_label, max_chars=120)
    if label and not _label_needs_rewrite(label, selected_chunks):
        return _sanitize_display_text(label, max_chars=32), False

    for source_text in _exam_point_source_texts(item, category, selected_chunks):
        derived = _derive_exam_point_from_text(source_text, category=category)
        if derived and not _label_needs_rewrite(derived, selected_chunks):
            return derived, False

    fallback = "岗位能力补齐与验证计划" if category == _JD_GAP_LEARNING else "项目经历深挖与贡献边界验证"
    return fallback, True


def _exam_point_source_texts(
    item: dict[str, Any],
    category: str,
    selected_chunks: list[dict[str, Any]],
) -> list[str]:
    values: list[str] = []
    preferred_fields = (
        "resume_signal",
        "jd_basis",
        "display_title",
        "exam_point",
        "title",
        "expected_capability",
        "interview_intent",
        "preparation_goal",
    )
    for field in preferred_fields:
        value = item.get(field)
        if isinstance(value, str):
            values.append(value)
    for field in ("related_resume_evidence", "related_job_requirements", "related_match_gaps", "missing_points"):
        values.extend(_string_list(item.get(field), limit=6))

    source_types = _GAP_LEARNING_SOURCE_TYPES if category == _JD_GAP_LEARNING else _DEEP_DIVE_SOURCE_TYPES
    for chunk in selected_chunks:
        if not isinstance(chunk, dict) or chunk.get("source_type") not in source_types:
            continue
        for field in ("text", "title"):
            value = chunk.get(field)
            if isinstance(value, str):
                values.append(value)
    return _dedupe_strings(
        [_sanitize_display_text(value, max_chars=360) for value in values],
        limit=20,
    )


def _derive_exam_point_from_text(value: object, *, category: str) -> str:
    text = _sanitize_display_text(value, max_chars=360)
    compact = _normalize_label_for_compare(text)
    if not compact:
        return ""
    if "平台" in compact and ("服务端" in compact or "架构" in compact or "辅助" in compact):
        return "项目平台服务端架构设计"
    if (
        "专业术语" in compact
        or "单一检索" in compact
        or "检索准确率" in compact
        or "混合检索" in compact
        or "召回" in compact
    ):
        return "领域术语检索与召回优化"
    if "a i agent".replace(" ", "") in compact or "aiagent" in compact:
        if "任务规划" in compact or "工具调用" in compact:
            return "AI Agent 任务规划与工具调用机制"
        if "java" not in compact:
            return "AI Agent 任务规划与工具调用机制"
    if "java" in compact and ("服务端" in compact or "后端" in compact or "高可用" in compact):
        return "Java 服务端高可用架构设计"
    if "高可用" in compact:
        return "服务端高可用架构设计"
    if "rag" in compact:
        return "检索增强生成架构设计"
    if "rocketmq" in compact or "kafka" in compact or "消息" in compact:
        return "消息一致性与失败补偿机制"
    if "redis" in compact or "分布式锁" in compact:
        return "分布式锁与状态一致性保障"
    if "postgresql" in compact or "数据模型" in compact:
        return "数据模型与持久化边界设计"
    if "fastapi" in compact or "后端api" in compact or "接口编排" in compact or "异步任务" in compact:
        return "后端 API 编排与任务状态治理"
    if "服务治理" in compact or "异常恢复" in compact or "失败恢复" in compact:
        return "服务治理与异常恢复机制"
    if "prompt" in compact or "多模型" in compact or "结构化输出" in compact:
        return "Prompt 结构化输出与模型降级机制"
    if "elasticsearch" in compact or "知识图谱" in compact or "搜索" in compact:
        return "搜索召回与知识检索建模"

    phrase = _clean_exam_point_phrase(text)
    if not phrase:
        return ""
    suffix = "能力补齐" if category == _JD_GAP_LEARNING else "项目深挖"
    if any(term in phrase for term in ("设计", "优化", "机制", "架构", "治理", "调用")):
        return _sanitize_display_text(phrase, max_chars=32)
    return _sanitize_display_text(f"{phrase}{suffix}", max_chars=32)


def _clean_exam_point_phrase(value: str) -> str:
    text = value.strip(" \t-•*、，；。")
    if "：" in text:
        text = text.split("：", 1)[1].strip()
    if ":" in text:
        text = text.split(":", 1)[1].strip()
    for prefix in _SOURCE_SENTENCE_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :].strip(" ，,.、")
    for marker in ("或者", "及以上", "以上", "经验", "要求"):
        text = text.replace(marker, " ")
    for separator in ("，", ",", "；", ";", "。", ".", "、"):
        if separator in text:
            text = text.split(separator, 1)[0].strip()
    return _sanitize_display_text(text, max_chars=24)


def _label_needs_rewrite(label: str, selected_chunks: list[dict[str, Any]]) -> bool:
    if not label:
        return True
    if _looks_source_sentence_label(label):
        return True
    if _matches_source_snippet(label, selected_chunks):
        return True
    return False


def _looks_source_sentence_label(label: str) -> bool:
    text = label.strip()
    if _is_allowed_exam_point_label(text):
        return False
    if any(text.startswith(prefix) for prefix in _SOURCE_SENTENCE_PREFIXES):
        return True
    if len(text) > 40:
        return True
    if any(separator in text for separator in ("。", "；", ";")):
        return True
    compact = _normalize_label_for_compare(text)
    if "年" in compact and any(marker in compact for marker in ("经验", "要求")):
        return True
    for marker in _SOURCE_SENTENCE_MARKERS:
        normalized_marker = _normalize_label_for_compare(marker)
        if not normalized_marker or normalized_marker == _normalize_label_for_compare("问题"):
            continue
        if normalized_marker in compact:
            return True
    if _normalize_label_for_compare("问题") in compact:
        return _looks_like_business_problem_excerpt(compact)
    return False


def _matches_source_snippet(label: str, selected_chunks: list[dict[str, Any]]) -> bool:
    normalized_label = _normalize_label_for_compare(label)
    if len(normalized_label) < _SOURCE_EXCERPT_MIN_LABEL_CHARS:
        return False
    if _is_allowed_exam_point_label(label):
        return False
    for chunk in selected_chunks:
        if not isinstance(chunk, dict):
            continue
        for field in ("text", "title"):
            normalized_source = _normalize_label_for_compare(str(chunk.get(field) or ""))
            if len(normalized_source) < 12:
                continue
            if normalized_label == normalized_source or normalized_source in normalized_label:
                return True
            if normalized_label in normalized_source and _looks_like_source_excerpt(
                normalized_label,
                normalized_source,
            ):
                return True
    return False


def _normalize_label_for_compare(value: object) -> str:
    text = truncate_text(value, max_chars=1000) or ""
    return "".join(ch.lower() for ch in text if ch.isalnum())


def _is_allowed_exam_point_label(label: str) -> bool:
    text = label.strip()
    compact = _normalize_label_for_compare(text)
    return any(text.startswith(prefix) for prefix in _SOURCE_SENTENCE_PREFIX_EXCEPTIONS) or any(
        compact.startswith(_normalize_label_for_compare(marker))
        for marker in _SOURCE_SENTENCE_MARKER_EXCEPTIONS
    )


def _looks_like_business_problem_excerpt(compact: str) -> bool:
    if any(compact.startswith(_normalize_label_for_compare(marker)) for marker in _SOURCE_SENTENCE_MARKER_EXCEPTIONS):
        return False
    problem_marker = _normalize_label_for_compare("问题")
    if problem_marker not in compact:
        return False
    return any(
        marker in compact
        for marker in _normalized_markers(
            (
                "领域",
                "部门",
                "业务",
                "场景",
                "流程",
                "故障模式",
                "复杂",
                "需要",
                "结合",
                "分析",
                "专业术语",
                "准确率",
                "不足",
            )
        )
    )


def _looks_like_source_excerpt(normalized_label: str, normalized_source: str) -> bool:
    if len(normalized_label) < _SOURCE_EXCERPT_MIN_LABEL_CHARS:
        return False
    source_coverage = len(normalized_label) / max(len(normalized_source), 1)
    if source_coverage < _SOURCE_EXCERPT_MIN_SOURCE_COVERAGE and len(normalized_label) < 16:
        return False
    label_has_excerpt_marker = any(marker in normalized_label for marker in _normalized_markers(_SOURCE_EXCERPT_LABEL_MARKERS))
    source_has_context_marker = any(marker in normalized_source for marker in _normalized_markers(_SOURCE_EXCERPT_SOURCE_MARKERS))
    return label_has_excerpt_marker and source_has_context_marker


def _normalized_markers(markers: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(marker for marker in (_normalize_label_for_compare(value) for value in markers) if marker)


def _quality_gate_failure_reason(nodes: list[dict[str, Any]], selected_chunks: list[dict[str, Any]]) -> str | None:
    if not nodes:
        return "quality_gate_no_nodes"
    leaves = _leaf_nodes(nodes)
    if not leaves:
        return "quality_gate_no_leaf_nodes"

    input_sufficient = _input_material_sufficient(selected_chunks)
    if input_sufficient and len(leaves) < 6:
        return "quality_gate_too_few_menu_nodes"

    categories = {node.get("category") for node in leaves}
    if _has_source_type(selected_chunks, _DEEP_DIVE_SOURCE_TYPES) and _RESUME_DEEP_DIVE not in categories:
        return "quality_gate_missing_resume_deep_dive"
    if _has_source_type(selected_chunks, _GAP_LEARNING_SOURCE_TYPES) and _JD_GAP_LEARNING not in categories:
        return "quality_gate_missing_jd_gap_learning"

    for node in leaves:
        for field in (
            "depth_goal",
            "first_question",
            "follow_up_focus",
            "expected_answer_signals",
            "common_loss_risks",
        ):
            if not node.get(field):
                return f"quality_gate_missing_{field}"
        title = str(node.get("display_title") or node.get("title") or "")
        if _looks_abstract_title(title):
            return "quality_gate_abstract_tree"
        for field in ("display_title", "exam_point", "title"):
            label = str(node.get(field) or "")
            if _label_needs_rewrite(label, selected_chunks):
                return "quality_gate_source_sentence_label"
        if _contains_forbidden_display_terms(_display_text_values(node)):
            return "quality_gate_forbidden_display_terms"
        if "项自" in str(node) or "责献" in str(node):
            return "quality_gate_mojibake_or_typo"
        if not _node_has_grounding(node):
            return "quality_gate_ungrounded_node"
    return None


def _input_material_sufficient(selected_chunks: list[dict[str, Any]]) -> bool:
    resume_count = sum(1 for chunk in selected_chunks if chunk.get("source_type") in _DEEP_DIVE_SOURCE_TYPES)
    gap_count = sum(1 for chunk in selected_chunks if chunk.get("source_type") in _GAP_LEARNING_SOURCE_TYPES)
    return resume_count >= 2 and gap_count >= 2


def _has_source_type(selected_chunks: list[dict[str, Any]], source_types: set[str]) -> bool:
    return any(isinstance(chunk, dict) and chunk.get("source_type") in source_types for chunk in selected_chunks)


def _leaf_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    leaves: list[dict[str, Any]] = []
    for node in nodes:
        children = [child for child in node.get("children", []) if isinstance(child, dict)]
        if children:
            leaves.extend(_leaf_nodes(children))
        else:
            leaves.append(node)
    return leaves


def _looks_abstract_title(title: str) -> bool:
    sanitized = _sanitize_display_text(title, max_chars=160)
    return any(fragment == sanitized or fragment in sanitized for fragment in _ABSTRACT_TITLE_FRAGMENTS)


def _node_has_grounding(node: dict[str, Any]) -> bool:
    return any(
        node.get(field)
        for field in (
            "resume_signal",
            "jd_basis",
            "related_job_requirements",
            "related_resume_evidence",
            "related_match_gaps",
            "evidence_chunk_ids",
            "evidence_bindings",
        )
    )


def _menu_sources(
    selected_chunks: list[dict[str, Any]],
    source_types: set[str],
    *,
    allowed_chunk_ids: set[str],
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for chunk in selected_chunks:
        if not isinstance(chunk, dict) or chunk.get("source_type") not in source_types:
            continue
        chunk_id = chunk.get("chunk_id")
        if not isinstance(chunk_id, str) or (allowed_chunk_ids and chunk_id not in allowed_chunk_ids):
            continue
        for text in _menu_text_candidates(chunk):
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(
                {
                    "chunk_id": chunk_id,
                    "source_type": str(chunk.get("source_type") or "other"),
                    "text": text,
                }
            )
            if len(result) >= 12:
                return result
    return result


def _menu_text_candidates(chunk: dict[str, Any]) -> list[str]:
    text = _sanitize_display_text(chunk.get("text") or chunk.get("title"), max_chars=900)
    if not text:
        return []
    normalized = text.replace("\r\n", "\n").replace("；", "\n").replace("。", "\n")
    parts = []
    for raw_part in normalized.splitlines():
        part = raw_part.strip(" \t-•*、，；。")
        if not part:
            continue
        parts.append(part)
    return parts or [text]


def _menu_title_from_text(value: object, category: str = _RESUME_DEEP_DIVE) -> str:
    title = _derive_exam_point_from_text(value, category=category)
    if title and not _looks_source_sentence_label(title):
        return title
    return "岗位能力补齐与验证计划" if category == _JD_GAP_LEARNING else "项目经历深挖与贡献边界验证"


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


def _basis_type_value(
    item: dict[str, Any],
    category: str,
    *,
    resume_signal: str | None,
    jd_basis: str | None,
) -> str:
    basis_type = truncate_text(item.get("basis_type"), max_chars=80)
    if basis_type in _ALLOWED_BASIS_TYPES:
        return basis_type
    if resume_signal and jd_basis:
        return "mixed"
    if category == _JD_GAP_LEARNING:
        return "jd_requirement" if jd_basis else "match_gap"
    return "resume_signal"


def _interview_method_value(item: dict[str, Any], category: str) -> str:
    raw_value = truncate_text(
        item.get("interview_method") or item.get("follow_up_method") or item.get("attack_style"),
        max_chars=80,
    )
    mapped = _LEGACY_METHOD_MAP.get(raw_value or "", raw_value)
    if mapped in _ALLOWED_INTERVIEW_METHODS:
        return mapped
    return "learning_plan" if category == _JD_GAP_LEARNING else "technical_deep_dive"


def _default_node_code(category: str, index: int) -> str:
    prefix = "A" if category == _JD_GAP_LEARNING else "D"
    return f"{prefix}{index}"


def _default_depth_goal(category: str, exam_point: str) -> str:
    if category == _JD_GAP_LEARNING:
        return f"准备到能说明「{exam_point}」的核心原理、常见方案、适用边界和补齐计划。"
    return f"准备到能讲清「{exam_point}」的具体场景、个人贡献、关键取舍和验证结果。"


def _default_preparation_goal(category: str, exam_point: str) -> str:
    if category == _JD_GAP_LEARNING:
        return f"把「{exam_point}」从 JD 关键词转成可学习、可表达、可验证的准备项。"
    return f"把「{exam_point}」从简历线索转成可连续追问的项目表达。"


def _default_first_question(category: str, exam_point: str) -> str:
    if category == _JD_GAP_LEARNING:
        return f"请说明你会如何补齐并表达「{exam_point}」这一 JD 要求。"
    return f"请结合简历经历说明你在「{exam_point}」中的具体做法和结果。"


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


def _low_confidence_flags(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    return _string_list(payload.get("low_confidence_flags"), limit=20)


def _flatten_v2_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in nodes:
        result.append(node)
        result.extend(_flatten_v2_nodes(node.get("children", [])))
    return result


def _dict_value(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_value(value: object, *, limit: int) -> list[Any]:
    return value[:limit] if isinstance(value, list) else []


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


def _state_status(value: object) -> str:
    text = truncate_text(value, max_chars=80)
    if text in {"completed", "in_progress", "pending"}:
        return text
    return "pending"


def _metadata_value(payload: dict[str, Any], key: str, fallback: str) -> str:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _node_ref(context_digest: str, seed: str) -> str:
    return f"progress_v2_{sha256(f'{context_digest}:{seed}'.encode('utf-8')).hexdigest()[:16]}"
