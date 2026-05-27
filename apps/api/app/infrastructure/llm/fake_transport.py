"""Deterministic fake LLM transport for contract tests."""

from __future__ import annotations

import re
from json import dumps
from typing import Any

from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
)
from app.application.polish.progress_v2_prompts import (
    POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
)
from app.application.polish.question_generation_prompts import (
    QUESTION_FOLLOW_UP_PROMPT_TASK_TYPE,
    QUESTION_PROMPT_TASK_TYPE,
)
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.domain.shared.ids import stable_resource_id
from app.schemas.job_match import (
    DimensionScore,
    JobMatchResultPayload,
    JobRequirementChunk,
    MatchedRequirement,
    ResumeChunk,
    ResumeEvidence,
    SourceEvidenceRef,
)
from app.application.llm.types import LlmTransportRequest, LlmTransportResult


class FakeLlmTransport:
    """确定性 Fake LLM 传输层，用于合同测试和离线验证。所有 task_type 的分发入口。"""

    status = "deterministic_fake_only"

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        """根据 request.task_type 分发到对应的 fake 生成函数；未知 task_type 返回骨架结果。"""
        if request.task_type == "job_match_analysis":
            return _generate_fake_job_match(request)
        if request.task_type in {QUESTION_PROMPT_TASK_TYPE, QUESTION_FOLLOW_UP_PROMPT_TASK_TYPE}:
            return _generate_fake_polish_question(request)
        if request.task_type == POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE:
            return _generate_fake_progress_quality_first_menu(request)
        if request.task_type == "polish_progress_tree_state":
            return _generate_fake_progress_tree_state(request)
        seed = dumps(
            {
                "contract_ids": sorted(request.contract_ids),
                "task_type": request.task_type,
                "input_refs": sorted(request.input_refs),
                "evidence_keys": sorted(request.evidence_bundle.keys()),
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        has_evidence = bool(request.evidence_bundle)
        validation_status = ValidationStatus.VALID if has_evidence else ValidationStatus.VALID_WITH_WARNINGS
        confidence_level = ConfidenceLevel.MEDIUM if has_evidence else ConfidenceLevel.LOW
        low_confidence_flags = () if has_evidence else ("evidence_missing",)
        trace_ref = stable_resource_id("trace", f"fake-llm-trace:{seed}")
        evidence_ref = stable_resource_id("trace", f"fake-llm-evidence:{seed}")
        return LlmTransportResult(
            result={
                "transport": "fake",
                "task_type": request.task_type,
                "contract_ids": list(request.contract_ids),
                "result_ref": stable_resource_id("task", f"fake-llm-result:{seed}"),
                "summary": "deterministic skeleton result",
            },
            validation_status=validation_status,
            confidence_level=confidence_level,
            low_confidence_flags=low_confidence_flags,
            trace_refs=(trace_ref,),
            evidence_refs=(evidence_ref,),
        )


def _generate_fake_polish_question(request: LlmTransportRequest) -> LlmTransportResult:
    bundle = request.evidence_bundle if isinstance(request.evidence_bundle, dict) else {}
    input_data = bundle.get("input_data") if isinstance(bundle.get("input_data"), dict) else {}
    progress_node = input_data.get("progress_node") if isinstance(input_data.get("progress_node"), dict) else {}
    policy = input_data.get("generation_policy") if isinstance(input_data.get("generation_policy"), dict) else {}
    follow_up = input_data.get("follow_up") if isinstance(input_data.get("follow_up"), dict) else {}
    is_follow_up = request.task_type == QUESTION_FOLLOW_UP_PROMPT_TASK_TYPE or input_data.get("generation_mode") == "follow_up"
    evidence_refs = tuple(ref for ref in input_data.get("evidence_refs", []) if isinstance(ref, str) and ref.strip())
    summaries = input_data.get("evidence_summaries") if isinstance(input_data.get("evidence_summaries"), list) else []
    summary_items = [item for item in summaries if isinstance(item, dict) and item.get("excerpt")]
    title = _fake_question_excerpt(progress_node.get("title") or "当前训练节点", limit=48)
    capability = _fake_question_excerpt(
        input_data.get("skill_dimension") or progress_node.get("expected_capability") or "说明关键链路、取舍和验证方式",
        limit=80,
    )
    claim_mode = str(policy.get("claim_mode") or "")
    excerpt = _fake_question_primary_excerpt(summary_items, claim_mode=claim_mode, fallback=capability)
    if is_follow_up:
        target_dimension = _fake_question_excerpt(follow_up.get("target_dimension") or capability, limit=80)
        answer_excerpt = _fake_question_excerpt(follow_up.get("previous_answer") or "上一轮回答", limit=80)
        question_text = (
            f"你上一轮回答中提到「{answer_excerpt}」，现在围绕「{target_dimension}」继续追问："
            f"请结合上一题背景和岗位/简历证据「{excerpt}」，说明你的具体判断、边界、"
            "失败处理、验证指标和关键取舍。"
        )
        difficulty = "hard"
        missing_context = []
        confidence = "medium"
        clarification_needed = False
    elif not evidence_refs or claim_mode == "clarification_needed":
        question_text = (
            f"围绕「{title}」，当前材料不足以形成有效题干。请提供真实材料，"
            "必须包含业务入口、职责边界、失败案例和验证指标。"
        )
        difficulty = "clarification"
        missing_context = input_data.get("missing_context") if isinstance(input_data.get("missing_context"), list) else []
        confidence = "low"
        clarification_needed = True
    elif claim_mode == "job_gap_probe":
        question_text = (
            f"围绕「{title}」，岗位侧需要验证「{capability}」。"
            f"请基于主要证据「{excerpt}」，说明你会如何补齐相关能力、设计验证路径并在面试中证明该能力。"
        )
        difficulty = "medium"
        missing_context = []
        confidence = "medium"
        clarification_needed = False
    else:
        question_text = (
            f"围绕「{title}」，请只基于主要证据「{excerpt}」展开："
            f"先说明业务背景和关键技术链路，再说明异常处理或关键取舍，最后用验证指标证明你具备「{capability}」。"
        )
        difficulty = "hard"
        missing_context = []
        confidence = "high"
        clarification_needed = False
    seed = dumps(
        {
            "contract_ids": sorted(request.contract_ids),
            "task_type": request.task_type,
            "input_refs": sorted(request.input_refs),
            "evidence_refs": sorted(evidence_refs),
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    trace_ref = stable_resource_id("trace", f"fake-polish-question-trace:{seed}")
    result_payload = {
        "transport": "fake",
        "model_name": "fake_llm_polish_question_v1",
        "question_text": question_text,
        "question_kind": policy.get("question_kind") or "technical_chain_deep_dive",
        "focus_dimension": policy.get("focus_dimension") or policy.get("question_kind") or "technical_chain_deep_dive",
        "difficulty": difficulty,
        "skill_dimension": capability,
        "expected_signal": "回答应引用证据，说明边界、取舍、失败处理、验证指标和复盘信号。",
        "follow_ups": ["关键失败场景是什么？", "如何证明方案有效？"],
        "scoring_rubric": [
            {"dimension": "grounding", "signals": ["引用证据", "不编造经历"]},
            {"dimension": "reasoning", "signals": ["说明边界", "说明验证指标"]},
        ],
        "missing_context": missing_context,
        "evidence_refs": list(evidence_refs),
        "confidence": confidence,
        "clarification_needed": clarification_needed,
        "prompt_version": request.prompt_version,
    }
    if not is_follow_up:
        support_level = "unsupported" if claim_mode == "job_gap_probe" else "direct_implemented"
        turn_intent = "gap_compensation_design" if claim_mode == "job_gap_probe" else "project_implementation_deep_dive"
        question_kind = "gap_compensation_design" if claim_mode == "job_gap_probe" else "implementation_deep_dive"
        if clarification_needed:
            support_level = "unsupported"
            turn_intent = "clarification"
            question_kind = "clarification"
        result_payload = {
            "transport": "fake",
            "model_name": "fake_llm_polish_question_v1",
            "schema_id": request.schema_id,
            "prompt_version": request.prompt_version,
            "clarification_needed": clarification_needed,
            "confidence": confidence,
            "missing_context": missing_context,
            "decision": {
                "turn_intent": turn_intent,
                "intent_reason": "fake transport deterministic next question intent",
                "evidence_support_level": support_level,
                "evidence_support_reason": "fake transport uses selected prompt evidence only",
                "main_question_style": "ask_clarification" if clarification_needed else "ask_how_implemented",
                "allowed_extension_depth": "none" if clarification_needed else "main_question_allowed",
                "primary_evidence_refs": [evidence_refs[0]] if evidence_refs else [],
                "secondary_evidence_refs": list(evidence_refs[1:]),
                "unsupported_capability_claims": [],
                "risk_flags": [],
                "avoid_patterns_applied": ["unsupported_capability_as_fact"],
            },
            "question": {
                "question_text": question_text,
                "question_kind": question_kind,
                "difficulty": difficulty,
                "skill_dimension": capability,
                "expected_signal": "回答应引用证据，说明边界、取舍、失败处理、验证指标和复盘信号。",
                "follow_ups": ["关键失败场景是什么？", "如何证明方案有效？"],
                "scoring_rubric": [
                    {"dimension": "grounding", "signals": ["引用证据", "不编造经历"]},
                    {"dimension": "reasoning", "signals": ["说明边界", "说明验证指标"]},
                ],
            },
            "persistence_hints": {
                "should_persist_decision": True,
                "should_update_progress": True,
                "next_focus_candidates": [str(progress_node.get("ref") or "")],
                "trace_tags": ["fake_transport", support_level],
            },
            "evidence_refs": list(evidence_refs),
            "post_check_hints": {
                "claims_to_verify": [],
                "unsupported_terms_in_question": [],
                "question_style_check": "pass",
                "evidence_grounding_check": "pass",
            },
        }
    return LlmTransportResult(
        result=result_payload,
        validation_status=ValidationStatus.VALID,
        confidence_level=(
            ConfidenceLevel.HIGH
            if confidence == "high"
            else ConfidenceLevel.LOW
            if confidence == "low"
            else ConfidenceLevel.MEDIUM
        ),
        low_confidence_flags=tuple(missing_context) if clarification_needed else (),
        trace_refs=(trace_ref,),
        evidence_refs=evidence_refs,
    )


def _fake_question_excerpt(value: object, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def _fake_question_primary_excerpt(items: list[dict[str, Any]], *, claim_mode: str, fallback: str) -> str:
    preferred_prefixes = ("job_", "match_") if claim_mode == "job_gap_probe" else ("resume_", "match_", "job_")
    for prefix in preferred_prefixes:
        for item in items:
            source_type = str(item.get("source_type") or "").lower()
            if source_type.startswith(prefix):
                excerpt = _fake_question_excerpt(item.get("excerpt"), limit=120)
                if excerpt:
                    return excerpt
    return _fake_question_excerpt(fallback, limit=120)


def _generate_fake_progress_quality_first_menu(request: LlmTransportRequest) -> LlmTransportResult:
    """生成 fake 质量优先初始训练菜单（含深度打磨类和补齐学习类节点）。"""
    context = request.evidence_bundle.get("context") if isinstance(request.evidence_bundle, dict) else {}
    resume_text = str(context.get("resume_markdown") or "") if isinstance(context, dict) else ""
    resume_signal = _first_text(resume_text, "候选人具备可深挖的工程项目经历。")[:480]
    job_payload = context.get("job_payload", {}) if isinstance(context, dict) else {}
    job_text = "\n".join(
        str(item)
        for item in (
            *((job_payload.get("requirements") or []) if isinstance(job_payload, dict) else []),
            *((job_payload.get("responsibilities") or []) if isinstance(job_payload, dict) else []),
        )
        if str(item).strip()
    )
    job_basis = _first_text(job_text, "岗位要求服务治理、系统可靠性和工程落地能力。")[:480]
    resume_titles = _quality_first_fake_titles(
        _fake_menu_text_candidates(resume_text or resume_signal),
        category="resume_deep_dive",
        target_count=5,
        fallback_titles=(
            "项目架构与职责边界",
            "关键技术链路与方案取舍",
            "失败处理与恢复策略",
            "验证指标与上线复盘",
            "协作边界与风险沟通",
            "持续改进与经验沉淀",
        ),
    )
    jd_titles = _quality_first_fake_titles(
        _fake_menu_text_candidates(job_text or job_basis),
        category="jd_gap_learning",
        target_count=3,
        fallback_titles=(
            "岗位能力拆解",
            "服务治理与可靠性方案",
            "性能瓶颈定位与优化",
            "数据模型与持久化边界",
            "质量评估与灰度策略",
            "工程协作与风险复盘",
        ),
    )
    categories = [
        {
            "category": "resume_deep_dive",
            "display_category_title": "深度打磨类",
            "nodes": [
                _quality_first_fake_node(
                    title=title,
                    category="resume_deep_dive",
                    display_category_title="深度打磨类",
                    index=index,
                    resume_signal=resume_signal,
                    jd_basis=job_basis,
                    confidence_level="high" if index <= 2 else "medium",
                )
                for index, title in enumerate(resume_titles, start=1)
            ],
        },
        {
            "category": "jd_gap_learning",
            "display_category_title": "补齐学习类",
            "nodes": [
                _quality_first_fake_node(
                    title=title,
                    category="jd_gap_learning",
                    display_category_title="补齐学习类",
                    index=index,
                    resume_signal=resume_signal,
                    jd_basis=job_basis,
                    confidence_level="medium",
                )
                for index, title in enumerate(jd_titles, start=1)
            ],
        },
    ]
    seed = _request_seed(request)
    trace_ref = stable_resource_id("trace", f"fake-polish-progress-quality-first-trace:{seed}")
    evidence_ref = stable_resource_id("trace", f"fake-polish-progress-quality-first-evidence:{seed}")
    return LlmTransportResult(
        result={
            "transport": "fake",
            "task_type": request.task_type,
            "schema_id": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
            "status": "success",
            "planner_summary": "已按完整简历、完整 JD 和匹配分析生成初始训练菜单。",
            "menu_categories": categories,
            "low_confidence_flags": [],
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.HIGH,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


def _quality_first_fake_titles(
    candidates: list[str],
    *,
    category: str,
    fallback_titles: tuple[str, ...],
    target_count: int,
) -> list[str]:
    titles: list[str] = []
    for candidate in candidates:
        title = _fake_menu_title(candidate, category=category)
        if title and title not in titles:
            titles.append(title)
        if len(titles) >= target_count:
            return titles
    for fallback in fallback_titles:
        if fallback not in titles:
            titles.append(fallback)
        if len(titles) >= target_count:
            return titles
    return titles


def _quality_first_fake_node(
    *,
    title: str,
    category: str,
    display_category_title: str,
    index: int,
    resume_signal: str,
    jd_basis: str,
    confidence_level: str,
) -> dict[str, Any]:
    """构造单个 fake 质量优先菜单节点（含题目、追问方向、失分风险等）。"""
    prefix = "D" if category == "resume_deep_dive" else "A"
    basis_type = "resume_signal" if category == "resume_deep_dive" else "jd_requirement"
    return {
        "node_code": f"{prefix}{index}",
        "category": category,
        "display_category_title": display_category_title,
        "display_title": title,
        "exam_point": title,
        "basis_type": basis_type,
        "resume_signal": resume_signal,
        "jd_basis": jd_basis,
        "depth_goal": f"准备到能讲清「{title}」的关键原理、设计取舍、落地细节和验证方式。",
        "preparation_goal": f"把「{title}」训练成可连续追问、可举证、可说明边界的面试表达。",
        "first_question": f"请结合你的经历或岗位要求，说明你对「{title}」的设计思路、关键取舍和验证方式。",
        "follow_up_focus": [
            "继续追问核心方案和替代方案",
            "继续追问落地边界、异常处理和可验证结果",
            "继续追问与岗位要求的关联和补齐计划",
        ],
        "expected_answer_signals": [
            "能说明场景、约束、方案和结果之间的因果链路",
            "能区分已实践经验、合理推断和需要补齐的部分",
            "能给出指标、验证方式或明确的风险说明",
        ],
        "common_loss_risks": [
            "只复述技术名词，缺少场景和取舍",
            "把团队成果全部归为个人成果",
            "无法说明验证方式、异常路径或边界条件",
        ],
        "evidence_refs": [f"fake_quality_first_{prefix.lower()}_{index}"],
        "evidence_notes": ["fake transport 基于完整上下文生成的稳定考点"],
        "confidence_level": confidence_level,
        "low_confidence_flags": [],
    }


def _fake_menu_text_candidates(value: str) -> list[str]:
    """将文本按中文分隔符拆分为候选菜单文本列表。"""
    normalized = value.replace("；", "\n").replace("。", "\n")
    result = []
    for line in normalized.splitlines():
        text = line.strip(" \t-•*、，；。")
        if text:
            result.append(text)
    return result or ([value] if value else [])


def _fake_menu_title(value: str, *, category: str) -> str:
    """根据文本关键词匹配生成固定菜单标题（关键词匹配失败时从文本提取）。"""
    compact = _fake_compact_text(value)
    if (
        "专业术语" in compact
        or "单一检索" in compact
        or "检索准确率" in compact
        or "混合检索" in compact
        or "召回" in compact
    ):
        return "专业术语场景下的混合检索与召回优化"
    if "aiagent" in compact:
        if "任务规划" in compact or "工具调用" in compact or "java" not in compact:
            return "AI Agent 任务规划与工具调用机制"
    if "java" in compact and ("服务端" in compact or "后端" in compact or "高可用" in compact):
        return "Java 服务端高可用架构设计"
    if "rag" in compact:
        return "RAG 检索增强生成架构设计"
    if "rocketmq" in compact or "kafka" in compact or "消息" in compact:
        return "消息一致性与失败补偿机制"
    if "redis" in compact or "分布式锁" in compact:
        return "分布式锁与状态一致性保障"
    if "postgresql" in compact or "数据模型" in compact:
        return "数据模型与持久化边界设计"
    if "fastapi" in compact or "后端api" in compact or "接口编排" in compact or "异步任务" in compact:
        return "后端 API 编排与任务状态治理"
    if "prompt" in compact or "多模型" in compact or "结构化输出" in compact:
        return "Prompt 结构化输出与模型降级机制"
    title = _fake_clean_exam_point_phrase(value)
    if "智能辅助平台" in title:
        return "智能辅助平台架构与质量治理"
    if "设备日志" in title:
        return "设备日志采集与质量复盘"
    if title:
        return title[:32]
    return "岗位能力补齐与验证计划" if category == "jd_gap_learning" else "项目经历深挖与贡献边界验证"


def _fake_compact_text(value: str) -> str:
    """将文本压缩为纯字母数字小写字符串（用于关键词匹配）。"""
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _fake_clean_exam_point_phrase(value: str) -> str:
    """从文本中清理出干净的考点短语（去除前缀、分隔符截断等）。"""
    title = value.strip(" \t-•*、，；。")
    if "：" in title:
        title = title.split("：", 1)[1].strip()
    if ":" in title:
        title = title.split(":", 1)[1].strip()
    for prefix in (
        "面向",
        "针对",
        "负责",
        "建设",
        "保障",
        "熟悉",
        "理解",
        "了解",
        "具备",
        "掌握",
        "参与",
        "主导",
        "5年以上",
        "3年以上",
        "2年以上",
        "要求",
        "Built",
        "Build",
        "Owned",
        "Own",
        "Implemented",
        "Developed",
    ):
        if title.startswith(prefix):
            title = title[len(prefix) :].strip(" ，,.、")
    for marker in ("或者", "及以上", "以上", "经验", "要求"):
        title = title.replace(marker, " ")
    for separator in ("，", ",", "；", ";", "。", ".", "、"):
        if separator in title:
            title = title.split(separator, 1)[0].strip()
    return title


def _request_seed(request: LlmTransportRequest) -> str:
    """基于请求生成确定性种子字符串（用于稳定的 trace/evidence ID）。"""
    return dumps(
        {
            "contract_ids": sorted(request.contract_ids),
            "task_type": request.task_type,
            "input_refs": sorted(request.input_refs),
            "source_digest": request.evidence_bundle.get("source_digest"),
        },
        ensure_ascii=True,
        sort_keys=True,
    )


def _generate_fake_progress_tree_state(request: LlmTransportRequest) -> LlmTransportResult:
    """生成 fake 进度树状态刷新结果（更新节点完成状态和优先级）。"""
    existing_plan = request.evidence_bundle.get("existing_progress_tree_plan", {})
    nodes = _flatten_nodes(existing_plan.get("nodes", []) if isinstance(existing_plan, dict) else [])
    target = nodes[-1] if nodes else {"progress_node_ref": "fake_llm_progress_backend_api_fastapi"}
    node_ref = target.get("progress_node_ref", "fake_llm_progress_backend_api_fastapi")
    seed = dumps(
        {
            "contract_ids": sorted(request.contract_ids),
            "task_type": request.task_type,
            "input_refs": sorted(request.input_refs),
            "source_digest": request.evidence_bundle.get("source_digest"),
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    trace_ref = stable_resource_id("trace", f"fake-polish-progress-state-trace:{seed}")
    evidence_ref = stable_resource_id("trace", f"fake-polish-progress-state-evidence:{seed}")
    return LlmTransportResult(
        result={
            "transport": "fake",
            "task_type": request.task_type,
            "contract_ids": list(request.contract_ids),
            "result_ref": stable_resource_id("task", f"fake-polish-progress-state-result:{seed}"),
            "model_name": "fake_llm_polish_progress_v1",
            "prompt_version": POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
            "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
            "progress_tree_state": {
                "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
                "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
                "prompt_version": POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
                "status": "ready",
                "node_states": [
                    {
                        "progress_node_ref": item.get("progress_node_ref"),
                        "status": "completed" if item.get("progress_node_ref") == node_ref else "pending",
                        "completed_questions_count": 1 if item.get("progress_node_ref") == node_ref else 0,
                        "latest_feedback_summary": "Fake LLM 状态刷新：回答已覆盖该节点，但仍需补指标。",
                    }
                    for item in nodes
                    if item.get("progress_node_ref")
                ],
                "current_priority": {
                    "progress_node_ref": node_ref,
                    "title": target.get("title", "Fake LLM 当前优先级"),
                    "expected_capability": target.get("expected_capability", "Fake LLM 当前能力要求"),
                },
                "updated_from_turns_count": _turns_count(request.evidence_bundle),
                "progress": {"progress_percent": 135},
            },
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.MEDIUM,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


def _flatten_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """递归展开进度树节点列表（含所有子节点）。"""
    result: list[dict[str, Any]] = []
    for node in nodes:
        result.append(node)
        result.extend(_flatten_nodes(node.get("children", [])))
    return result


def _turns_count(evidence_bundle: dict[str, Any]) -> int:
    """从 evidence_bundle 中提取已完成的轮次数量。"""
    context = evidence_bundle.get("context", {})
    if not isinstance(context, dict):
        return 0
    turns_summary = context.get("turns_summary")
    if isinstance(turns_summary, list):
        return len(turns_summary)
    turns = context.get("turns")
    if isinstance(turns, list):
        return len(turns)
    return 0


def _first_text(*values: object | None) -> str:
    """返回第一个非空字符串；全部为空时返回默认降级文本。"""
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Fake LLM 输入证据不足"


def _generate_fake_job_match(request: LlmTransportRequest) -> LlmTransportResult:
    """生成 fake 岗位匹配分析结果（基于 token 重叠率计算各维度分数）。"""
    resume_chunks = _resume_chunks(request.evidence_bundle)
    job_chunks = _job_requirement_chunks(request.evidence_bundle)
    seed = dumps(
        {
            "contract_ids": sorted(request.contract_ids),
            "task_type": request.task_type,
            "input_refs": sorted(request.input_refs),
            "source_digest": request.evidence_bundle.get("source_digest"),
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    trace_ref = stable_resource_id("trace", f"fake-job-match-trace:{seed}")
    evidence_ref = stable_resource_id("trace", f"fake-job-match-evidence:{seed}")
    payload = _fake_job_match_payload(resume_chunks, job_chunks)
    return LlmTransportResult(
        result={
            "transport": "fake",
            "task_type": request.task_type,
            "contract_ids": list(request.contract_ids),
            "result_ref": stable_resource_id("task", f"fake-job-match-result:{seed}"),
            "model_name": "fake_llm_job_match_v1",
            "prompt_version": "P-JOBMATCH-001+P-JOBMATCH-002+P-JOBMATCH-003.v1",
            "job_match_result_payload": payload.model_dump(mode="json"),
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.MEDIUM,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


def _fake_job_match_payload(
    resume_chunks: list[ResumeChunk],
    job_chunks: list[JobRequirementChunk],
) -> JobMatchResultPayload:
    """基于 token 重叠率计算 fake 岗位匹配分数并构造结果载荷。"""
    resume_text = "\n".join(chunk.text for chunk in resume_chunks)
    job_text = "\n".join(chunk.text for chunk in job_chunks)
    resume_tokens = _tokens(resume_text)
    job_tokens = _tokens(job_text)
    overlap = resume_tokens & job_tokens
    overlap_ratio = len(overlap) / max(1, min(len(resume_tokens), len(job_tokens)))
    has_overlap = bool(overlap)
    resume_chunk_id = resume_chunks[0].chunk_id
    job_chunk_id = job_chunks[0].chunk_id
    evidence = [SourceEvidenceRef(chunk_id=resume_chunk_id)]

    requirement_alignment = _bounded_score(15 + round(15 * overlap_ratio), 8, 30)
    experience_evidence = _bounded_score(14 + min(len(resume_chunks), 3) * 2 + (3 if has_overlap else 0), 8, 25)
    skill_coverage = _bounded_score(9 + round(10 * overlap_ratio), 5, 20)
    gap_risk = 13 if has_overlap else 8
    readiness_actions = 8 if has_overlap else 5
    overall_score = (
        requirement_alignment
        + experience_evidence
        + skill_coverage
        + gap_risk
        + readiness_actions
    )
    overall_level = (
        "strong_match"
        if overall_score >= 80
        else "medium_match"
        if overall_score >= 60
        else "weak_match"
    )
    confidence = "medium" if has_overlap else "low"

    return JobMatchResultPayload(
        overall_score=overall_score,
        overall_level=overall_level,
        confidence=confidence,
        summary=f"基于 LLM 分析链路读取到的岗位与简历证据，当前匹配分为 {overall_score} / 100。",
        dimension_scores=[
            DimensionScore(
                key="requirement_alignment",
                score=requirement_alignment,
                max_score=30,
                rationale="LLM 分析链路识别出岗位关键要求与简历证据之间的直接重合点。",
                supporting_evidence=evidence,
                gaps=[] if has_overlap else ["岗位关键要求与简历证据的直接重合不足。"],
                confidence=confidence,
            ),
            DimensionScore(
                key="experience_evidence",
                score=experience_evidence,
                max_score=25,
                rationale="简历片段提供了可追问的经历、项目或工作流证据。",
                supporting_evidence=evidence,
                gaps=[],
                confidence=confidence,
            ),
            DimensionScore(
                key="skill_coverage",
                score=skill_coverage,
                max_score=20,
                rationale="技能覆盖分来自岗位文本与简历文本中的技能证据交集。",
                supporting_evidence=evidence,
                gaps=[] if overlap else ["需要补充更明确的技能证据。"],
                confidence=confidence,
            ),
            DimensionScore(
                key="gap_risk",
                score=gap_risk,
                max_score=15,
                rationale="缺口风险根据未覆盖要求和可追问证据完整度进行降级。",
                supporting_evidence=evidence,
                gaps=["面试中继续确认经验深度。"],
                confidence="medium",
            ),
            DimensionScore(
                key="readiness_actions",
                score=readiness_actions,
                max_score=10,
                rationale="后续准备动作可基于当前证据形成聚焦追问。",
                supporting_evidence=evidence,
                gaps=[],
                confidence="medium",
            ),
        ],
        matched_requirements=[
            MatchedRequirement(
                requirement_chunk_id=job_chunk_id,
                resume_evidence_chunk_ids=[resume_chunk_id],
                rationale="LLM 分析链路将岗位要求与最相关的简历证据建立了引用关系。",
                confidence=confidence,
            )
        ],
        missing_requirements=[],
        resume_evidence=[
            ResumeEvidence(
                chunk_id=resume_chunk_id,
                summary="用于岗位匹配分析的主要简历证据。",
                confidence=confidence,
            )
        ],
        risk_flags=[],
        interview_focus=["围绕匹配度最高的证据追问候选人的真实参与深度。"],
        suggested_questions=["请结合岗位要求说明这段经历中最能证明匹配度的具体产出。"],
        markdown_report="# 岗位匹配分析\n\n本结果由 LLM 分析链路基于当前岗位与简历证据生成。",
    )


def _resume_chunks(evidence_bundle: dict[str, Any]) -> list[ResumeChunk]:
    """从 evidence_bundle 中提取并解析简历块列表。"""
    return [
        ResumeChunk.model_validate(chunk)
        for chunk in evidence_bundle.get("resume_chunks", [])
    ]


def _job_requirement_chunks(evidence_bundle: dict[str, Any]) -> list[JobRequirementChunk]:
    """从 evidence_bundle 中提取并解析岗位要求块列表。"""
    return [
        JobRequirementChunk.model_validate(chunk)
        for chunk in evidence_bundle.get("job_requirement_chunks", [])
    ]


def _tokens(text: str) -> set[str]:
    """将文本拆分为 token 集合（英文词块 + 中文二元组），用于文本匹配。"""
    lowered = text.lower()
    ascii_tokens = set(re.findall(r"[a-z0-9]{2,}", lowered))
    cjk_tokens: set[str] = set()
    for segment in re.findall(r"[\u4e00-\u9fff]+", lowered):
        if len(segment) == 1:
            cjk_tokens.add(segment)
        else:
            cjk_tokens.update(segment[index : index + 2] for index in range(len(segment) - 1))
    return ascii_tokens | cjk_tokens


def _bounded_score(value: int, lower: int, upper: int) -> int:
    """将分数限制在 [lower, upper] 范围内。"""
    return max(lower, min(upper, value))
