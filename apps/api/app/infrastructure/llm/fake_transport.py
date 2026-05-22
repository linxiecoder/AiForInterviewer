"""Deterministic fake LLM transport for contract tests."""

from __future__ import annotations

import re
from json import dumps
from typing import Any

from app.application.polish.feedback_prompts import (
    POLISH_ANSWER_FEEDBACK_SCHEMA_ID,
    POLISH_ANSWER_FEEDBACK_SCHEMA_VERSION,
    POLISH_ANSWER_FEEDBACK_TASK_TYPE,
)
from app.application.polish.candidate_llm import (
    POLISH_CANDIDATE_MEMORY_REVIEW_SCHEMA_ID,
    POLISH_CANDIDATE_MEMORY_REVIEW_SCHEMA_VERSION,
    POLISH_CANDIDATE_MEMORY_REVIEW_TASK_TYPE,
)
from app.application.polish.question_prompts import (
    POLISH_QUESTION_GENERATION_PROMPT_VERSION,
    POLISH_QUESTION_GENERATION_SCHEMA_ID,
    POLISH_QUESTION_GENERATION_SCHEMA_VERSION,
    POLISH_QUESTION_GENERATION_TASK_TYPE,
)
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
    POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
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
from app.infrastructure.llm.errors import LlmTransportUnavailableError
from app.infrastructure.llm.types import LlmTransportRequest, LlmTransportResult


class FakeLlmTransport:
    status = "deterministic_fake_only"

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        if request.task_type == "job_match_analysis":
            return _generate_fake_job_match(request)
        if request.task_type == POLISH_QUESTION_GENERATION_TASK_TYPE:
            return _generate_fake_polish_question(request)
        if request.task_type == POLISH_ANSWER_FEEDBACK_TASK_TYPE:
            return _generate_fake_polish_feedback(request)
        if request.task_type == POLISH_CANDIDATE_MEMORY_REVIEW_TASK_TYPE:
            return _generate_fake_candidate_memory_review(request)
        if request.task_type == POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE:
            return _generate_fake_progress_quality_first_menu(request)
        if request.task_type == POLISH_PROGRESS_GLOBAL_UNDERSTANDING_TASK_TYPE:
            return _generate_fake_progress_global_understanding(request)
        if request.task_type == POLISH_PROGRESS_TREE_DRAFT_PLAN_TASK_TYPE:
            return _generate_fake_progress_tree_draft_plan_v2(request)
        if request.task_type == POLISH_PROGRESS_TREE_CRITIC_REFINER_TASK_TYPE:
            return _generate_fake_progress_tree_critic_refiner(request)
        if request.task_type == POLISH_PROGRESS_TREE_GROUNDING_TASK_TYPE:
            return _generate_fake_progress_tree_grounding(request)
        if request.task_type == "polish_progress_tree_plan":
            return _generate_fake_progress_tree_plan(request)
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


def _generate_fake_polish_feedback(request: LlmTransportRequest) -> LlmTransportResult:
    evidence_bundle = request.evidence_bundle.get("evidence_bundle", {}) if isinstance(request.evidence_bundle, dict) else {}
    answer_round = int(evidence_bundle.get("answer_round") or 1)
    marker = str(evidence_bundle.get("fixture_marker") or ("valid_retry" if answer_round > 1 else "valid_first"))
    if marker == "provider_unavailable":
        raise LlmTransportUnavailableError("fake feedback provider unavailable")
    if marker == "timeout":
        raise TimeoutError("fake feedback provider timeout")
    if marker == "schema_invalid":
        payload = {
            "schema_id": "unexpected_feedback_schema",
            "schema_version": 999,
            "feedback_summary": "schema invalid",
        }
    else:
        payload = _fake_polish_feedback_payload(evidence_bundle, answer_round=answer_round)
        if marker == "valid_first":
            payload["feedback_summary"] = "LLM fake first feedback: accepted"
            payload["feedback_text"] = payload["feedback_summary"]
        elif marker == "valid_retry":
            payload["feedback_summary"] = "LLM fake retry feedback: accepted"
            payload["feedback_text"] = payload["feedback_summary"]
            payload.update(_fake_retry_delta(evidence_bundle))
        elif marker == "invalid_retry_unknown_improved_point":
            payload["feedback_summary"] = "LLM fake retry feedback: invalid unknown improved point"
            payload["feedback_text"] = payload["feedback_summary"]
            payload.update(
                _fake_retry_delta(
                    evidence_bundle,
                    improved_loss_point_id="fake_unknown_previous_loss_point",
                )
            )
        elif marker == "missing_critical_loss_coverage":
            payload["p7_reference_answer"] = "回答可以先说明背景和职责，但这里故意不覆盖关键术语。"
        elif marker == "oral_script_ignores_loss":
            payload["oral_script"] = "我先说明背景，再介绍自己负责的模块。"
        elif marker == "score_dimension_mismatch":
            payload["score_result"]["score_value"] = 41
        elif marker == "raw_prompt_leak":
            payload["raw_prompt"] = "RAW_PROMPT_SHOULD_NOT_ESCAPE"
        elif marker == "raw_prompt_value_leak":
            payload["feedback_summary"] = "raw_prompt=RAW_PROMPT_SHOULD_NOT_ESCAPE"
            payload["feedback_text"] = payload["feedback_summary"]
        elif marker == "metadata_full_evidence_leak":
            payload["feedback_metadata"]["full_evidence_text"] = "FULL_EVIDENCE_TEXT_SHOULD_NOT_ESCAPE"
        elif marker == "unsupported_user_fact":
            payload["feedback_metadata"]["unsupported_user_facts"] = ["候选人负责了未出现在输入中的支付清算平台"]
        elif marker == "low_confidence_valid":
            payload["low_confidence_flags"] = [
                {
                    "flag_id": "feedback_low_confidence_fake",
                    "reason": "fake low confidence branch",
                    "impact_scope": "feedback_payload",
                    "recommended_action": "manual_review",
                }
            ]
            payload["score_result"]["confidence_level"] = "low"
        elif marker == "repair_then_valid":
            payload["score_result"]["score_value"] = 41
        elif marker == "repair_then_fallback":
            payload["score_result"]["score_value"] = 41
            payload["p7_reference_answer"] = "回答可以先说明背景和职责，但这里故意不覆盖关键术语。"
        else:
            payload["feedback_summary"] = "LLM fake first feedback: accepted"
            payload["feedback_text"] = payload["feedback_summary"]
    validation_status = ValidationStatus.VALID
    confidence_level = ConfidenceLevel.LOW if marker == "low_confidence_valid" else ConfidenceLevel.MEDIUM
    seed = dumps(
        {
            "task_type": request.task_type,
            "marker": marker,
            "input_refs": sorted(request.input_refs),
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    return LlmTransportResult(
        result=payload,
        validation_status=validation_status,
        confidence_level=confidence_level,
        low_confidence_flags=("feedback_low_confidence_fake",) if marker == "low_confidence_valid" else (),
        trace_refs=(stable_resource_id("trace", f"fake-feedback-trace:{seed}"),),
        evidence_refs=(stable_resource_id("trace", f"fake-feedback-evidence:{seed}"),),
    )


def _generate_fake_candidate_memory_review(request: LlmTransportRequest) -> LlmTransportResult:
    candidate_ids = [
        str(candidate_id)
        for candidate_id in request.evidence_bundle.get("candidate_ids", [])
        if str(candidate_id).strip()
    ]
    candidates = request.evidence_bundle.get("candidates", [])
    evidence_refs = request.evidence_bundle.get("evidence_refs", [])
    seed = dumps(
        {
            "task_type": request.task_type,
            "candidate_ids": candidate_ids,
            "input_refs": sorted(request.input_refs),
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    enhancements = []
    for candidate in candidates if isinstance(candidates, list) else []:
        if not isinstance(candidate, dict):
            continue
        candidate_id = str(candidate.get("candidate_id") or "").strip()
        if not candidate_id:
            continue
        enhancements.append(
            {
                "candidate_id": candidate_id,
                "summary_hint": "Fake LLM 候选增强：保留候选态，等待用户确认。",
                "review_focus": str(candidate.get("candidate_type") or "candidate"),
            }
        )
    first_candidate_id = candidate_ids[0] if candidate_ids else "cand_fake_missing"
    return LlmTransportResult(
        result={
            "schema_id": POLISH_CANDIDATE_MEMORY_REVIEW_SCHEMA_ID,
            "schema_version": POLISH_CANDIDATE_MEMORY_REVIEW_SCHEMA_VERSION,
            "status": "generated",
            "candidate_enhancements": enhancements,
            "review_recommendation_candidates": [
                {
                    "recommendation_id": stable_resource_id("task", f"fake-review-rec:{seed}"),
                    "title": "Fake LLM 候选复盘建议",
                    "summary": "建议用户基于候选对象完成一次可解释复盘；不自动写正式对象。",
                    "candidate_refs": [{"resource_type": "polish_candidate", "resource_id": first_candidate_id}],
                    "evidence_refs": evidence_refs[:3] if isinstance(evidence_refs, list) else [],
                }
            ],
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.MEDIUM,
        low_confidence_flags=(),
        trace_refs=(stable_resource_id("trace", f"fake-candidate-review-trace:{seed}"),),
        evidence_refs=(stable_resource_id("trace", f"fake-candidate-review-evidence:{seed}"),),
    )


def _fake_polish_feedback_payload(evidence_bundle: dict[str, Any], *, answer_round: int) -> dict[str, Any]:
    dimensions = [
        {"dimension_id": "technical_depth", "score_value": 80, "max_score": 100, "weight": 1.0},
        {"dimension_id": "answer_structure", "score_value": 70, "max_score": 100, "weight": 1.0},
        {"dimension_id": "evidence_alignment", "score_value": 60, "max_score": 100, "weight": 1.0},
    ]
    payload: dict[str, Any] = {
        "schema_id": POLISH_ANSWER_FEEDBACK_SCHEMA_ID,
        "schema_version": POLISH_ANSWER_FEEDBACK_SCHEMA_VERSION,
        "status": "generated",
        "feedback_summary": "LLM fake first feedback: accepted",
        "feedback_text": "LLM fake first feedback: accepted",
        "answer_diagnosis": {
            "strengths": ["回答开始覆盖背景和关键链路。"],
            "weaknesses": ["失败路径和验证指标仍需展开。"],
            "risks": ["critical loss_points 未修复前，不应进入正式对象写入。"],
            "recommendations": ["下一轮优先补失败路径、补偿机制和验证指标。"],
        },
        "scoring_dimensions": dimensions,
        "score_result": {
            "score_result_id": "fake_feedback_score",
            "score_type": "polish_answer",
            "score_value": 70,
            "score_version": POLISH_ANSWER_FEEDBACK_SCHEMA_VERSION,
            "rubric_version": "polish_round_score.fake_feedback.v1",
            "confidence_level": "medium",
        },
        "positive_evidence_points": [
            {
                "point_id": "fake_positive_metrics",
                "title": "保留验证指标",
                "evidence_excerpt": "验证指标",
                "dimension_id": "evidence_alignment",
                "location": "both",
            }
        ],
        "loss_points": [
            {
                "loss_point_id": "fake_loss_failure_path",
                "title": "失败路径仍需展开",
                "deducted_points": 12,
                "reason": "需要补充失败路径、补偿机制和验证指标。",
                "critical": True,
                "dimension_id": "technical_depth",
                "required_reference_terms": ["失败路径", "验证指标"],
                "required_oral_terms": ["失败路径", "验证指标"],
            }
        ],
        "missing_answer_dimensions": [
            {"dimension": "technical_depth", "reason": "失败路径和补偿机制需要更具体。"}
        ],
        "p7_reference_answer": "参考回答应覆盖失败路径、补偿机制和验证指标，并保留验证指标作为证据。",
        "reference_answer_requirements": [
            {
                "requirement_id": "fake_reference_requirement",
                "requirement": "覆盖失败路径和验证指标。",
                "required_coverage_terms": ["失败路径", "验证指标"],
            }
        ],
        "oral_script": "我先说明业务背景，再讲失败路径、补偿机制、验证指标和技术取舍。",
        "oral_script_requirements": [
            {
                "requirement_id": "fake_oral_requirement",
                "requirement": "口述覆盖失败路径和验证指标。",
                "required_coverage_terms": ["失败路径", "验证指标"],
            }
        ],
        "knowledge_points": [{"title": "幂等与补偿", "explanation": "用状态机和补偿任务收敛异常链路。"}],
        "technical_principles": [{"title": "可观测验证", "explanation": "用指标、日志和告警验证方案有效性。"}],
        "technical_gaps": ["失败路径仍需展开"],
        "communication_gaps": ["结论可以更前置"],
        "next_recommended_actions": ["continue_same_question"],
        "low_confidence_flags": [],
        "feedback_metadata": {
            "fake_feedback_marker": str(evidence_bundle.get("fixture_marker") or ""),
            "prompt_answer_round": answer_round,
        },
        "score_delta": 0,
        "dimension_delta": {},
        "improved_points": [],
        "remaining_gaps": ["fake_loss_failure_path"],
        "repeated_loss_points": [],
        "regressed_points": [],
        "mastery_status": "stuck" if answer_round > 1 else None,
        "should_continue_same_question": True,
        "should_generate_next_question": False,
        "next_retry_focus": [{"focus_area": "fake_loss_failure_path", "priority": 1}],
        "updated_reference_answer": None,
        "updated_oral_script": None,
        "weakness_candidates": [],
        "asset_candidates": [],
        "validation_result_ref": None,
        "trace_refs": [],
    }
    if answer_round > 1:
        payload.update(_fake_retry_delta(evidence_bundle))
    return payload


def _fake_retry_delta(
    evidence_bundle: dict[str, Any] | None = None,
    *,
    improved_loss_point_id: str | None = None,
) -> dict[str, Any]:
    loss_point_id = improved_loss_point_id or _first_previous_loss_point_id(evidence_bundle)
    improved_points = [loss_point_id] if loss_point_id else ["fake_missing_previous_loss_point"]
    return {
        "score_delta": 8,
        "dimension_delta": {
            "technical_depth": 10,
            "answer_structure": 4,
            "evidence_alignment": 8,
        },
        "improved_points": improved_points,
        "remaining_gaps": ["fake_loss_failure_path"],
        "repeated_loss_points": [],
        "regressed_points": [],
        "mastery_status": "improving",
        "should_continue_same_question": True,
        "should_generate_next_question": False,
        "next_retry_focus": [{"focus_area": "fake_loss_failure_path", "priority": 1}],
        "updated_reference_answer": "参考回答应覆盖失败路径、补偿机制和验证指标，并保留验证指标作为证据。",
        "updated_oral_script": "我先说明业务背景，再讲失败路径、补偿机制、验证指标和技术取舍。",
    }


def _first_previous_loss_point_id(evidence_bundle: dict[str, Any] | None) -> str | None:
    if not isinstance(evidence_bundle, dict):
        return None
    for summary in _dict_items(evidence_bundle.get("previous_feedback_compact_summaries")):
        for point in _dict_items(summary.get("loss_points")):
            loss_point_id = str(point.get("loss_point_id") or "").strip()
            if loss_point_id:
                return loss_point_id
    return None


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _generate_fake_polish_question(request: LlmTransportRequest) -> LlmTransportResult:
    evidence_bundle = request.evidence_bundle.get("evidence_bundle", {}) if isinstance(request.evidence_bundle, dict) else {}
    marker = str(evidence_bundle.get("fixture_marker") or "valid_high_quality")
    evidence_refs = [str(ref) for ref in evidence_bundle.get("input_evidence_refs", []) if str(ref)]
    if marker == "provider_unavailable":
        raise LlmTransportUnavailableError("fake question provider unavailable")
    if marker == "timeout_or_transport_error":
        raise TimeoutError("fake question provider timeout")
    if marker == "schema_invalid":
        payload = {"schema_id": "unexpected_schema", "schema_version": 999, "question_text": "schema invalid"}
    else:
        payload = _fake_polish_question_payload(evidence_bundle, evidence_refs=evidence_refs)
        if marker == "semantic_invalid":
            payload["question_text"] = "请简单聊聊这个项目。"
        elif marker == "fabricated_entity":
            payload["question_text"] = (
                "LLM 合同测试题：围绕「支付链路一致性」，请从 Owner 视角先限定业务约束，"
                "再说明 Kafka 和 RocketMQ 同时失败时的失败路径、性能或成本约束、验证指标、可观测指标和核心 trade-off；"
                "如何让状态收敛？回答重点：业务边界、核心链路、失败路径、资源约束、验证指标、后续补材料。[1][2]"
            )
        elif marker == "answer_leak":
            payload["question_text"] = "参考答案：可以这样回答：先做幂等，再做补偿。"
        elif marker == "evidence_refs_invalid":
            payload["evidence_refs"] = [*evidence_refs, "fabricated_evidence_ref"]
        elif marker == "low_confidence_valid":
            payload["confidence_level"] = "low"
            payload["low_confidence_flags"] = ["llm_low_confidence"]
        elif marker == "repair_then_valid":
            payload["question_text"] = payload["question_text"].replace("回答重点", "请按回答重点")
            payload["requires_repair"] = True
        elif marker == "repair_then_fallback":
            payload["question_text"] = "；".join([payload["question_text"]] * 10)
            payload["requires_repair"] = True
    confidence_level = ConfidenceLevel.LOW if payload.get("confidence_level") == "low" else ConfidenceLevel.MEDIUM
    low_flags = tuple(payload.get("low_confidence_flags") or ())
    return LlmTransportResult(
        result=payload,
        validation_status=ValidationStatus.VALID,
        confidence_level=confidence_level,
        low_confidence_flags=low_flags,
        trace_refs=(stable_resource_id("trace", f"fake-question-trace:{marker}:{','.join(evidence_refs)}"),),
        evidence_refs=tuple(evidence_refs),
    )


def _fake_polish_question_payload(evidence_bundle: dict[str, Any], *, evidence_refs: list[str]) -> dict[str, Any]:
    node = evidence_bundle.get("progress_node_summary", {}) if isinstance(evidence_bundle, dict) else {}
    pattern = evidence_bundle.get("question_pattern", {}) if isinstance(evidence_bundle, dict) else {}
    focus = node.get("title") or "当前进展节点"
    pattern_id = pattern.get("pattern_id") or "owner_tradeoff_system_design"
    dimensions = [str(item) for item in (pattern.get("expected_answer_dimensions") or []) if str(item)]
    if not dimensions:
        dimensions = ["业务边界", "核心链路", "失败路径", "资源约束", "验证指标", "后续补材料"]
    selected_refs = evidence_refs[:]
    if pattern_id == "mixed_technical_expression":
        question_text = (
            f"LLM 合同测试题：本题权重比例为显性技术 60%、隐性表达 40%。围绕「{focus}」，"
            "请先说明业务约束，再展开技术深度：选择一个失败路径说明方案链路、失败兜底、"
            "验证指标、可观测指标、成本控制和核心 trade-off；同时请按背景、约束、方案、结果、复盘的表达结构回答。"
            f"回答重点：{'、'.join(dimensions[:6])}。[1][2]"
        )
    elif pattern_id == "star_communication_refactor":
        question_text = (
            f"LLM 合同测试题：围绕「{focus}」，请用 STAR 结构重讲一遍：先做背景压缩，"
            "明确个人职责边界，按逻辑顺序说明关键动作、失败处理和取舍表达，最后用结果指标、复盘总结和面试口语化表达收束。"
            f"回答重点：{'、'.join(dimensions[:6])}。[1][2]"
        )
    elif pattern_id == "partial_success_failure_recovery":
        question_text = (
            f"LLM 合同测试题：围绕「{focus}」，请从 Owner 视角先限定业务约束，"
            "再说明部分成功 / 部分失败时的状态机、重试收敛、断点续跑、幂等保护、成本上限、验证指标和可观测指标；"
            "如果恢复链路失败，如何让状态收敛并解释核心 trade-off？"
            f"回答重点：{'、'.join(dimensions[:6])}。[1][2]"
        )
    else:
        question_text = (
            f"LLM 合同测试题：围绕「{focus}」，请从 Owner 视角先限定业务约束，"
            "再选择一个失败路径说明性能或成本约束、验证指标、可观测指标和核心 trade-off；"
            "如果接口幂等、补偿或重试失败，如何让状态收敛？"
            f"回答重点：{'、'.join(dimensions[:6])}。[1][2]"
        )
    return {
        "schema_id": POLISH_QUESTION_GENERATION_SCHEMA_ID,
        "schema_version": POLISH_QUESTION_GENERATION_SCHEMA_VERSION,
        "prompt_version": POLISH_QUESTION_GENERATION_PROMPT_VERSION,
        "status": "generated",
        "question_text": question_text,
        "question_pattern": pattern_id,
        "interview_intent": "验证候选人能否把当前节点的异常收敛讲清楚。",
        "scenario_constraint_summary": "基于 compact evidence 的题目生成。",
        "expected_answer_dimensions": dimensions,
        "evidence_refs": selected_refs,
        "source_availability": "available" if selected_refs else "partial",
        "confidence_level": "medium",
        "low_confidence_flags": [],
        "quality_hints": ["绑定 progress_node_ref", "不得泄露参考答案"],
        "requires_repair": False,
        "redaction_boundary": "no_raw_prompt_completion_provider_payload",
    }


def _generate_fake_progress_quality_first_menu(request: LlmTransportRequest) -> LlmTransportResult:
    context = request.evidence_bundle.get("context") if isinstance(request.evidence_bundle, dict) else {}
    context_text = dumps(context, ensure_ascii=False, sort_keys=True) if isinstance(context, dict) else ""
    hardware_mode = "硬件测试" in context_text
    resume_signal = _first_text(
        context.get("resume_markdown") if isinstance(context, dict) else None,
        "候选人具备可深挖的后端与 AI 工程项目经历。",
    )[:480]
    job_payload = context.get("job_payload", {}) if isinstance(context, dict) else {}
    job_basis = _first_text(
        *((job_payload.get("requirements") or []) if isinstance(job_payload, dict) else []),
        *((job_payload.get("responsibilities") or []) if isinstance(job_payload, dict) else []),
        "岗位要求后端服务治理、AI Agent、RAG 和工程落地能力。",
    )[:480]
    if hardware_mode:
        resume_titles = [
            "硬件测试智能辅助平台的服务端架构设计",
            "专业术语场景下的混合检索与召回优化",
            "硬件测试知识库的切片与索引设计",
            "RAG 问答准确率评估与阈值控制",
            "检索失败时的澄清、降级与兜底策略",
            "企业内部 AI 平台的权限、审计与可观测性",
        ]
    else:
        resume_titles = [
            "面试训练工作台的 FastAPI 接口编排",
            "面试训练工作台的任务状态一致性设计",
            "搜索问答助手的混合检索与模型降级",
            "交易通知系统的消息一致性与失败补偿",
            "PostgreSQL 数据模型与后台任务管道治理",
            "Prompt 结构化输出与多模型调用策略",
        ]
    jd_titles = [
        "AI Agent 任务规划与工具调用机制",
        "Agent 记忆管理与知识库协同",
        "Java 服务端高可用架构设计",
        "高并发接口限流、降级与压测方案",
        "Elasticsearch / 向量检索底层原理",
        "模型评测、灰度与成本控制",
    ]
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
            "status": "ready",
            "planner_summary": "已按完整简历、完整 JD 和匹配分析生成初始训练菜单。",
            "menu_categories": categories,
            "metadata": {
                "quality_target": "10-14 leaves",
                "input_context_mode": "full_resume_full_job",
            },
            "low_confidence_flags": [],
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.HIGH,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


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


def _generate_fake_progress_global_understanding(request: LlmTransportRequest) -> LlmTransportResult:
    context = request.evidence_bundle.get("context") if isinstance(request.evidence_bundle, dict) else {}
    job_payload = context.get("job_payload", {}) if isinstance(context, dict) else {}
    requirements = job_payload.get("requirements") if isinstance(job_payload, dict) else []
    resume_markdown = context.get("resume_markdown") if isinstance(context, dict) else ""
    job_requirement = _first_text(*(requirements or []))
    resume_evidence = _first_text(resume_markdown)
    seed = _request_seed(request)
    trace_ref = stable_resource_id("trace", f"fake-polish-progress-v2-global-trace:{seed}")
    evidence_ref = stable_resource_id("trace", f"fake-polish-progress-v2-global-evidence:{seed}")
    return LlmTransportResult(
        result={
            "transport": "fake",
            "task_type": request.task_type,
            "schema_id": POLISH_PROGRESS_GLOBAL_UNDERSTANDING_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_GLOBAL_UNDERSTANDING_PROMPT_VERSION,
            "status": "success",
            "candidate_profile_summary": {
                "one_sentence_positioning": f"候选人具备可追问的后端项目证据：{resume_evidence}",
                "experience_level_assessment": "可按中级后端候选人进行真实性和技术深度打磨。",
                "core_strengths": ["有后端工作流项目证据", "能与岗位后端 API 要求形成交集"],
                "core_risks": ["真实贡献边界需要追问", "业务结果和指标证据需要补强"],
                "most_interviewable_projects": [resume_evidence],
                "least_supported_claims": ["上线效果、指标和故障恢复细节"],
                "communication_risk_notes": ["需要避免只讲技术名词，改为按场景、动作、结果表达。"],
            },
            "target_role_competency_map": [
                {
                    "competency_id": "competency_backend_api",
                    "title": "后端 API 与服务治理",
                    "importance": "high",
                    "job_requirement_refs": [job_requirement],
                    "why_it_matters": "岗位要求候选人能承担后端 API 和面试准备工作流。",
                    "expected_interview_depth": "advanced",
                }
            ],
            "resume_evidence_map": [
                {
                    "evidence_id": "evidence_backend_project",
                    "source_area": "project",
                    "title": "后端工作流项目证据",
                    "evidence_summary": resume_evidence,
                    "explicit_evidence": [resume_evidence],
                    "reasonable_inferences": ["可追问接口设计、数据流和落地职责"],
                    "unsupported_or_weak_parts": ["指标、故障恢复、贡献边界"],
                    "interview_value": "high",
                }
            ],
            "role_gap_risk_map": [
                {
                    "risk_id": "risk_contribution_boundary",
                    "risk_title": "项目贡献边界和结果证据不够稳",
                    "risk_type": "unclear_contribution",
                    "severity": "high",
                    "evidence_summary": resume_evidence,
                    "likely_interviewer_attack": "你具体负责哪一段？如果没有你，项目会有什么不同？",
                    "defense_strategy_hint": "用背景、个人动作、技术取舍、验证结果和协作边界回答。",
                }
            ],
            "interview_strategy": {
                "overall_strategy": "先验证真实项目和贡献边界，再进入技术原理、工程取舍和风险说明。",
                "recommended_sequence": ["项目真实性", "后端技术深度", "工程取舍", "缺口说明", "表达结构"],
                "high_value_attack_points": ["贡献边界", "指标验证", "失败恢复"],
                "avoid_overfitting_notes": ["不要只围绕 FastAPI 技术名生成菜单。"],
                "suggested_difficulty_curve": "从 intermediate 项目核验进入 advanced 技术追问，再到连续追问准备。",
            },
            "recommended_progress_axes": [
                {
                    "axis_id": "axis_authenticity",
                    "title": "项目真实性与贡献边界",
                    "reason": "该方向最能提升打磨模式第一轮问题质量。",
                    "related_competency_ids": ["competency_backend_api"],
                    "related_evidence_ids": ["evidence_backend_project"],
                    "related_risk_ids": ["risk_contribution_boundary"],
                    "priority": 1,
                }
            ],
            "low_confidence_flags": [],
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.MEDIUM,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


def _generate_fake_progress_tree_draft_plan_v2(request: LlmTransportRequest) -> LlmTransportResult:
    selected_chunks = _selected_evidence_chunks(request.evidence_bundle)
    job_requirement = _join_text(
        _chunk_text(selected_chunks, "job_requirement"),
        _chunk_text(selected_chunks, "job_responsibility"),
    )
    resume_evidence = _chunk_text(selected_chunks, "resume_project", "resume_skill", "resume_work_experience")
    match_gap = _chunk_text(selected_chunks, "match_gap", fallback="需要继续证明真实贡献边界")
    evidence_chunk_ids = _chunk_ids(
        selected_chunks,
        "job_requirement",
        "resume_project",
        "resume_skill",
        "resume_work_experience",
        "match_gap",
    )
    nodes = _fake_progress_menu_nodes(
        selected_chunks,
        job_requirement=job_requirement,
        resume_evidence=resume_evidence,
        match_gap=match_gap,
        evidence_chunk_ids=evidence_chunk_ids,
        grounded=False,
    )
    seed = _request_seed(request)
    trace_ref = stable_resource_id("trace", f"fake-polish-progress-v2-draft-trace:{seed}")
    evidence_ref = stable_resource_id("trace", f"fake-polish-progress-v2-draft-evidence:{seed}")
    return LlmTransportResult(
        result={
            "transport": "fake",
            "task_type": request.task_type,
            "schema_id": POLISH_PROGRESS_TREE_DRAFT_PLAN_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_TREE_DRAFT_PLAN_PROMPT_VERSION,
            "status": "success",
            "plan_quality_intent": {
                "tree_positioning": "先给出可用但略普通的后端项目打磨树，等待 critic 强化。",
                "target_interview_level": "advanced",
                "planning_rationale": "围绕岗位后端要求和简历项目证据构造可追问节点。",
            },
            "progress_tree_plan": {"status": "ready", "nodes": nodes},
            "coverage_summary": {
                "covered_competencies": [node["display_title"] for node in nodes if node["category"] == "jd_gap_learning"],
                "covered_projects": [node["display_title"] for node in nodes if node["category"] == "resume_deep_dive"],
                "covered_job_gaps": [match_gap],
                "covered_risks": ["贡献边界"],
                "missing_but_important": ["指标验证"],
            },
            "critic_notes_for_next_task": ["草案节点需要继续强化证据绑定和连续追问方向。"],
            "low_confidence_flags": [],
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.MEDIUM,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


def _generate_fake_progress_tree_critic_refiner(request: LlmTransportRequest) -> LlmTransportResult:
    selected_chunks = _selected_evidence_chunks(request.evidence_bundle)
    job_requirement = _join_text(
        _chunk_text(selected_chunks, "job_requirement"),
        _chunk_text(selected_chunks, "job_responsibility"),
    )
    resume_evidence = _chunk_text(selected_chunks, "resume_project", "resume_skill", "resume_work_experience")
    match_gap = _chunk_text(selected_chunks, "match_gap", fallback="需要补强指标和贡献边界")
    evidence_chunk_ids = _chunk_ids(
        selected_chunks,
        "job_requirement",
        "resume_project",
        "resume_skill",
        "resume_work_experience",
        "match_gap",
    )
    seed = _request_seed(request)
    trace_ref = stable_resource_id("trace", f"fake-polish-progress-v2-critic-trace:{seed}")
    evidence_ref = stable_resource_id("trace", f"fake-polish-progress-v2-critic-evidence:{seed}")
    nodes = _fake_progress_menu_nodes(
        selected_chunks,
        job_requirement=job_requirement,
        resume_evidence=resume_evidence,
        match_gap=match_gap,
        evidence_chunk_ids=evidence_chunk_ids,
        grounded=False,
    )
    return LlmTransportResult(
        result={
            "transport": "fake",
            "task_type": request.task_type,
            "schema_id": POLISH_PROGRESS_TREE_CRITIC_REFINER_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_TREE_CRITIC_REFINER_PROMPT_VERSION,
            "status": "success",
            "quality_review": {
                "personalization_score": 92,
                "job_alignment_score": 91,
                "interview_value_score": 93,
                "evidence_groundability_score": 90,
                "structure_quality_score": 88,
                "non_generic_score": 91,
                "overall_quality_score": 91,
                "major_findings": ["已将普通项目介绍重写为具体面试菜单节点。"],
                "must_fix_items": [],
                "generic_node_refs": ["fake_v2_draft_backend_project"],
                "weak_evidence_node_refs": [],
                "duplicate_node_refs": [],
                "over_inferred_node_refs": [],
                "missing_high_value_topics": [],
            },
            "refinement_strategy": {
                "strategy_summary": "保留岗位后端主线，强化真实性、贡献边界、指标和失败恢复追问。",
                "nodes_to_keep": [],
                "nodes_to_merge": [],
                "nodes_to_delete": ["fake_v2_draft_backend_project"],
                "nodes_to_add": [node["progress_node_ref"] for node in nodes],
                "nodes_to_rewrite": ["fake_v2_draft_backend_project"],
            },
            "refined_progress_tree_plan": {"status": "ready", "nodes": nodes},
            "quality_gate": {
                "passed": True,
                "reason": "节点具备岗位贴合、个性化证据和追问价值。",
                "remaining_risks": ["真实业务结果仍需候选人回答时补证据。"],
            },
            "low_confidence_flags": [],
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.MEDIUM,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


def _generate_fake_progress_tree_grounding(request: LlmTransportRequest) -> LlmTransportResult:
    selected_chunks = _selected_evidence_chunks(request.evidence_bundle)
    job_requirement = _join_text(
        _chunk_text(selected_chunks, "job_requirement"),
        _chunk_text(selected_chunks, "job_responsibility"),
    )
    resume_evidence = _chunk_text(selected_chunks, "resume_project", "resume_skill", "resume_work_experience")
    match_gap = _chunk_text(selected_chunks, "match_gap", fallback="需要补强指标和贡献边界")
    evidence_chunk_ids = _chunk_ids(
        selected_chunks,
        "job_requirement",
        "resume_project",
        "resume_skill",
        "resume_work_experience",
        "match_gap",
    )
    nodes = _fake_progress_menu_nodes(
        selected_chunks,
        job_requirement=job_requirement,
        resume_evidence=resume_evidence,
        match_gap=match_gap,
        evidence_chunk_ids=evidence_chunk_ids,
        grounded=True,
    )
    seed = _request_seed(request)
    trace_ref = stable_resource_id("trace", f"fake-polish-progress-v2-grounding-trace:{seed}")
    evidence_ref = stable_resource_id("trace", f"fake-polish-progress-v2-grounding-evidence:{seed}")
    return LlmTransportResult(
        result={
            "transport": "fake",
            "task_type": request.task_type,
            "schema_id": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_TREE_GROUNDED_PROMPT_VERSION,
            "status": "success",
            "progress_tree_plan": {"status": "ready", "nodes": nodes},
            "grounding_summary": {
                "strongly_grounded_nodes_count": len(nodes),
                "partially_grounded_nodes_count": 0,
                "weakly_grounded_nodes_count": 0,
                "ungrounded_nodes_count": 0,
                "unsupported_claims": [],
                "evidence_gaps": [],
                "recommended_user_visible_warning": None,
            },
            "initial_progress_tree_state": {
                "status": "ready",
                "node_states": [
                    {
                        "progress_node_ref": node["progress_node_ref"],
                        "status": "pending",
                        "completed_questions_count": 0,
                        "latest_feedback_summary": None,
                    }
                    for node in nodes
                ],
                "current_priority": {
                    "progress_node_ref": nodes[0]["progress_node_ref"],
                    "title": nodes[0]["title"],
                    "expected_capability": nodes[0]["expected_capability"],
                    "priority_reason": nodes[0]["priority_reason"],
                },
                "progress": {"progress_percent": 135},
            },
            "low_confidence_flags": [],
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.MEDIUM,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


def _fake_progress_menu_nodes(
    selected_chunks: list[dict[str, Any]],
    *,
    job_requirement: str,
    resume_evidence: str,
    match_gap: str,
    evidence_chunk_ids: list[str],
    grounded: bool,
) -> list[dict[str, Any]]:
    resume_sources = _fake_menu_sources(
        selected_chunks,
        {"resume_project", "resume_skill", "resume_work_experience", "match_focus", "turn_feedback", "asset_summary"},
        fallback_text=resume_evidence,
        fallback_titles=("项目职责说明", "关键技术取舍", "结果验证与异常恢复"),
    )
    gap_sources = _fake_menu_sources(
        selected_chunks,
        {"job_requirement", "job_responsibility", "match_gap", "match_suggested_question"},
        fallback_text=job_requirement or match_gap,
        fallback_titles=("岗位核心要求", "缺口补齐路径", "工程实践边界"),
    )
    nodes = []
    for index, source in enumerate(resume_sources[:3], start=1):
        title = _fake_menu_title(source["text"], category="resume_deep_dive")
        chunk_id = source["chunk_id"] or (evidence_chunk_ids[0] if evidence_chunk_ids else "")
        nodes.append(
            {
                "progress_node_ref": stable_resource_id("trace", f"fake-v2-menu-D{index}:{source['text']}"),
                "node_code": f"D{index}",
                "category": "resume_deep_dive",
                "display_category_title": "深度打磨类",
                "display_title": title,
                "exam_point": title,
                "title": title,
                "basis_type": "resume_signal",
                "resume_signal": source["text"] or resume_evidence,
                "jd_basis": job_requirement or None,
                "depth_goal": f"准备到能讲清「{title}」的业务场景、个人负责范围、关键取舍和验证结果。",
                "preparation_goal": f"训练用户把「{title}」讲成具体项目经历，而不是只罗列技术名词。",
                "expected_capability": f"准备到能讲清「{title}」的业务场景、个人负责范围、关键取舍和验证结果。",
                "priority_reason": "该项来自简历已有线索，适合优先做深度打磨。",
                "node_type": "project_deep_dive",
                "first_question": f"请结合简历线索说明你在「{title}」中具体负责什么、为什么这样设计，以及如何验证结果。",
                "follow_up_focus": [
                    "连续追问个人负责范围和协作边界",
                    "连续追问关键方案的取舍依据",
                    "连续追问上线验证、指标或异常恢复过程",
                ],
                "expected_answer_signals": [
                    "能说明真实场景和个人动作",
                    "能解释关键技术取舍",
                    "能给出验证结果或证据边界",
                ],
                "common_loss_risks": [
                    "只复述技术栈，缺少场景",
                    "个人贡献边界不清",
                    "缺少结果验证方式",
                ],
                "related_job_requirements": [job_requirement] if job_requirement else [],
                "related_resume_evidence": [source["text"] or resume_evidence],
                "related_match_gaps": [match_gap] if match_gap else [],
                "evidence_chunk_ids": [chunk_id] if chunk_id else evidence_chunk_ids[:1],
                "evidence_bindings": [_binding(chunk_id, source["source_type"], "该证据支撑深度打磨菜单项。")]
                if chunk_id
                else [],
                "grounding_status": "strongly_grounded" if grounded and chunk_id else "partially_grounded",
                "confidence_level": "high" if grounded and chunk_id else "medium",
                "children": [],
            }
        )
    for index, source in enumerate(gap_sources[:3], start=1):
        title = _fake_menu_title(source["text"], category="jd_gap_learning")
        chunk_id = source["chunk_id"] or (evidence_chunk_ids[0] if evidence_chunk_ids else "")
        nodes.append(
            {
                "progress_node_ref": stable_resource_id("trace", f"fake-v2-menu-A{index}:{source['text']}"),
                "node_code": f"A{index}",
                "category": "jd_gap_learning",
                "display_category_title": "补齐学习类",
                "display_title": title,
                "exam_point": title,
                "title": title,
                "basis_type": "jd_requirement" if source["source_type"].startswith("job_") else "match_gap",
                "resume_signal": resume_evidence or None,
                "jd_basis": source["text"] or job_requirement or match_gap,
                "depth_goal": f"准备到能说明「{title}」的核心原理、常见方案、适用边界和补齐计划。",
                "preparation_goal": f"训练用户把「{title}」讲成原理、方案和学习补齐路径。",
                "expected_capability": f"准备到能说明「{title}」的核心原理、常见方案、适用边界和补齐计划。",
                "priority_reason": "该项来自 JD 要求或匹配缺口，适合补齐学习。",
                "node_type": "job_gap",
                "first_question": f"JD 提到「{title}」时，你会如何说明它的原理、适用场景和当前补齐计划？",
                "follow_up_focus": [
                    "连续追问核心概念和典型方案",
                    "连续追问与已有项目的可迁移经验",
                    "连续追问短期补齐计划和验证方式",
                ],
                "expected_answer_signals": [
                    "能解释基础原理和常见实践",
                    "能诚实区分已实践和待补齐部分",
                    "能给出具体补齐路径",
                ],
                "common_loss_risks": [
                    "只背关键词，无法解释原理",
                    "把学习项说成已主导经验",
                    "补齐计划不够具体",
                ],
                "related_job_requirements": [source["text"] or job_requirement or match_gap],
                "related_resume_evidence": [resume_evidence] if resume_evidence else [],
                "related_match_gaps": [match_gap] if match_gap else [],
                "evidence_chunk_ids": [chunk_id] if chunk_id else evidence_chunk_ids[:1],
                "evidence_bindings": [_binding(chunk_id, source["source_type"], "该证据支撑补齐学习菜单项。")]
                if chunk_id
                else [],
                "grounding_status": "strongly_grounded" if grounded and chunk_id else "partially_grounded",
                "confidence_level": "high" if grounded and chunk_id else "medium",
                "children": [],
            }
        )
    return nodes


def _fake_menu_sources(
    chunks: list[dict[str, Any]],
    source_types: set[str],
    *,
    fallback_text: str,
    fallback_titles: tuple[str, str, str],
) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    seen: set[str] = set()
    for chunk in chunks:
        if chunk.get("source_type") not in source_types:
            continue
        chunk_id = chunk.get("chunk_id") if isinstance(chunk.get("chunk_id"), str) else ""
        for text in _fake_menu_text_candidates(_first_text(chunk.get("text"), chunk.get("title"))):
            if text in seen:
                continue
            seen.add(text)
            sources.append({"text": text, "chunk_id": chunk_id, "source_type": chunk.get("source_type") or "other"})
            if len(sources) >= 3:
                return sources
    fallback_basis = fallback_text or "来自当前材料的可训练考点"
    for title in fallback_titles:
        if len(sources) >= 3:
            break
        text = f"{title}：{fallback_basis}"
        if text not in seen:
            seen.add(text)
            sources.append({"text": text, "chunk_id": "", "source_type": "fallback"})
    return sources


def _fake_menu_text_candidates(value: str) -> list[str]:
    normalized = value.replace("；", "\n").replace("。", "\n")
    result = []
    for line in normalized.splitlines():
        text = line.strip(" \t-•*、，；。")
        if text:
            result.append(text)
    return result or ([value] if value else [])


def _fake_menu_title(value: str, *, category: str) -> str:
    compact = _fake_compact_text(value)
    if "硬件测试" in compact and ("智能辅助平台" in compact or "辅助平台" in compact or "平台" in compact):
        return "硬件测试智能辅助平台的服务端架构设计"
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
    if title:
        return title[:32]
    return "岗位能力补齐与验证计划" if category == "jd_gap_learning" else "项目经历深挖与贡献边界验证"


def _fake_compact_text(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _fake_clean_exam_point_phrase(value: str) -> str:
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


def _chunk_id(chunks: list[dict[str, Any]], *source_types: str) -> str:
    source_type_set = set(source_types)
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if chunk.get("source_type") in source_type_set and isinstance(chunk_id, str) and chunk_id:
            return chunk_id
    return ""


def _join_text(*values: str) -> str:
    return "；".join(value for value in values if value)


def _binding(chunk_id: str, source_type: str, reason: str) -> dict[str, str]:
    return {
        "evidence_chunk_id": chunk_id,
        "source_type": source_type,
        "binding_reason": reason,
        "supports_field": "interview_intent",
    }


def _generate_fake_progress_tree_plan(request: LlmTransportRequest) -> LlmTransportResult:
    context = request.evidence_bundle.get("context") if isinstance(request.evidence_bundle, dict) else {}
    selected_chunks = _selected_evidence_chunks(request.evidence_bundle)
    job_requirement = _chunk_text(
        selected_chunks,
        "job_requirement",
        fallback=_legacy_context_text(context, "job_snapshot", "requirements"),
    )
    job_responsibility = _chunk_text(
        selected_chunks,
        "job_responsibility",
        fallback=_legacy_context_text(context, "job_snapshot", "responsibilities"),
    )
    resume_evidence = _chunk_text(
        selected_chunks,
        "resume_project",
        "resume_skill",
        "resume_work_experience",
        fallback=_legacy_context_text(
            context,
            "resume_snapshot",
            "project_experiences",
            "summary",
            "markdown_text",
        ),
    )
    evidence_chunk_ids = _chunk_ids(
        selected_chunks,
        "job_requirement",
        "resume_project",
        "resume_skill",
        "resume_work_experience",
    )
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
    trace_ref = stable_resource_id("trace", f"fake-polish-progress-plan-trace:{seed}")
    evidence_ref = stable_resource_id("trace", f"fake-polish-progress-plan-evidence:{seed}")
    node_ref = "fake_llm_progress_backend_api"
    child_ref = "fake_llm_progress_backend_api_fastapi"
    return LlmTransportResult(
        result={
            "transport": "fake",
            "task_type": request.task_type,
            "contract_ids": list(request.contract_ids),
            "result_ref": stable_resource_id("task", f"fake-polish-progress-plan-result:{seed}"),
            "model_name": "fake_llm_polish_progress_v1",
            "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
            "schema_id": POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
            "progress_tree_plan": {
                "schema_id": POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
                "schema_version": POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
                "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
                "status": "ready",
                "nodes": [
                    {
                        "progress_node_ref": node_ref,
                        "title": "Fake LLM 节点：岗位后端能力验证",
                        "expected_capability": f"围绕岗位要求验证候选人的后端落地能力：{job_requirement}",
                        "related_job_requirements": [job_requirement, job_responsibility],
                        "related_resume_evidence": [resume_evidence],
                        "missing_points": ["Fake LLM 缺口：需要继续证明真实贡献边界"],
                        "evidence_chunk_ids": evidence_chunk_ids,
                        "children": [
                            {
                                "progress_node_ref": child_ref,
                                "title": "Fake LLM 子节点：FastAPI 项目证据",
                                "expected_capability": f"用简历证据说明项目中的技术取舍：{resume_evidence}",
                                "related_job_requirements": [job_requirement, job_responsibility],
                                "related_resume_evidence": [resume_evidence],
                                "missing_points": ["Fake LLM 缺口：需要补充指标和风险处理"],
                                "evidence_chunk_ids": evidence_chunk_ids,
                                "children": [],
                            }
                        ],
                    }
                ],
            },
            "progress_tree_state": {
                "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
                "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
                "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
                "status": "ready",
                "node_states": [
                    {
                        "progress_node_ref": node_ref,
                        "status": "in_progress",
                        "completed_questions_count": 0,
                        "latest_feedback_summary": None,
                    },
                    {
                        "progress_node_ref": child_ref,
                        "status": "in_progress",
                        "completed_questions_count": 0,
                        "latest_feedback_summary": None,
                    },
                ],
                "current_priority": {
                    "progress_node_ref": child_ref,
                    "title": "Fake LLM 子节点：FastAPI 项目证据",
                    "expected_capability": f"用简历证据说明项目中的技术取舍：{resume_evidence}",
                },
                "updated_from_turns_count": 0,
                "progress": {"progress_percent": 0},
            },
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.MEDIUM,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


def _generate_fake_progress_tree_state(request: LlmTransportRequest) -> LlmTransportResult:
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
    result: list[dict[str, Any]] = []
    for node in nodes:
        result.append(node)
        result.extend(_flatten_nodes(node.get("children", [])))
    return result


def _selected_evidence_chunks(evidence_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    chunks = evidence_bundle.get("selected_evidence_chunks")
    if not chunks and isinstance(evidence_bundle.get("context"), dict):
        chunks = evidence_bundle["context"].get("selected_evidence_chunks")
    if not isinstance(chunks, list):
        return []
    return [chunk for chunk in chunks if isinstance(chunk, dict)]


def _chunk_text(chunks: list[dict[str, Any]], *source_types: str, fallback: str | None = None) -> str:
    source_type_set = set(source_types)
    for chunk in chunks:
        if chunk.get("source_type") in source_type_set:
            text = _first_text(chunk.get("text"), chunk.get("title"))
            if text:
                return text
    return fallback or ""


def _chunk_ids(chunks: list[dict[str, Any]], *source_types: str) -> list[str]:
    source_type_set = set(source_types)
    result: list[str] = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if chunk.get("source_type") in source_type_set and isinstance(chunk_id, str) and chunk_id:
            result.append(chunk_id)
    return result[:8]


def _legacy_context_text(
    context: object,
    snapshot_key: str,
    *field_names: str,
) -> str:
    if not isinstance(context, dict):
        return ""
    snapshot = context.get(snapshot_key, {})
    if not isinstance(snapshot, dict):
        return ""
    values: list[Any] = []
    for field_name in field_names:
        value = snapshot.get(field_name)
        if isinstance(value, list):
            values.extend(value)
        else:
            values.append(value)
    return _first_text(*values)


def _turns_count(evidence_bundle: dict[str, Any]) -> int:
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
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Fake LLM 输入证据不足"


def _generate_fake_job_match(request: LlmTransportRequest) -> LlmTransportResult:
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
    return [
        ResumeChunk.model_validate(chunk)
        for chunk in evidence_bundle.get("resume_chunks", [])
    ]


def _job_requirement_chunks(evidence_bundle: dict[str, Any]) -> list[JobRequirementChunk]:
    return [
        JobRequirementChunk.model_validate(chunk)
        for chunk in evidence_bundle.get("job_requirement_chunks", [])
    ]


def _tokens(text: str) -> set[str]:
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
    return max(lower, min(upper, value))
