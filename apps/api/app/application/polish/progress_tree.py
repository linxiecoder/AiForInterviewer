"""LLM-backed progress tree generation and state refresh."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from typing import Any

from app.application.polish.entities import PolishQuestionDraft, PolishQuestionSource, PolishSession
from app.application.polish.evidence_signals import EvidenceSignalSet, extract_evidence_signals
from app.application.polish.progress_evidence import ProgressEvidenceChunk, select_progress_tree_evidence_chunks
from app.application.polish.question_metadata import QuestionMetadata, build_question_metadata
from app.application.polish.question_patterns import QuestionPattern, get_question_pattern, select_question_pattern
from app.application.polish.question_quality import (
    QuestionQualityResult,
    fallback_question_text,
    repair_question_text,
    validate_question_quality,
)
from app.application.polish.scenario_constraints import ScenarioConstraint, build_scenario_constraints
from app.application.polish.theme_strategy import PolishThemeStrategy, resolve_polish_theme_strategy
from app.application.polish.progress_context import has_sufficient_progress_context, truncate_text
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_TREE_PLAN_CONTRACT_IDS,
    POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
    POLISH_PROGRESS_TREE_STATE_CONTRACT_IDS,
    POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
    build_initial_progress_tree_prompt,
    build_progress_tree_state_refresh_prompt,
)
from app.application.polish.progress_tree_v2 import (
    PolishProgressTreeQualityFirstPlanner,
    PolishProgressTreeV2Pipeline,
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
PROGRESS_TREE_STATUS_REFRESH_FAILED = "refresh_failed"
PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT = "insufficient_context"
QUESTION_GENERATION_PROGRESS_NODE_CONTRACT = (
    "生成下一题时必须使用 progress_node_ref 对应节点的 title、expected_capability、相关岗位要求、"
    "相关简历证据、当前缺口和历史 turns。"
)
QUESTION_SOURCE_JOB_TYPES = {"job_requirement", "job_responsibility"}
QUESTION_SOURCE_RESUME_TYPES = {"resume_project", "resume_skill", "resume_work_experience", "resume_summary"}
QUESTION_SOURCE_TITLE_BY_TYPE = {
    "job_requirement": "岗位要求",
    "resume_evidence": "简历项目经历",
    "progress_node": "当前进展节点",
    "missing_point": "当前缺口",
    "history_feedback": "历史反馈",
}
PROGRESS_TREE_PLANNER_ENV = "AIFI_PROGRESS_TREE_PLANNER"
DEFAULT_PROGRESS_TREE_PLANNER = "quality_first"
PROGRESS_TREE_PLANNER_QUALITY_FIRST = "quality_first"
PROGRESS_TREE_PLANNER_V2_PIPELINE = "v2_pipeline"
PENDING_FEEDBACK_TEXT = "本轮反馈尚未生成"


@dataclass(frozen=True)
class ProgressNodeQuestionContext:
    session: PolishSession
    context: dict[str, Any]
    plan: dict[str, Any]
    state: dict[str, Any]
    requested_ref: str | None
    node: dict[str, Any]
    evidence_chunks: tuple[ProgressEvidenceChunk, ...]
    evidence_refs: tuple[str, ...]
    sources: tuple[PolishQuestionSource, ...]
    citations: str
    strategy: PolishThemeStrategy
    source_availability: str
    progress_node_ref: str | None
    context_digest: str | None


@dataclass(frozen=True)
class DeterministicProgressNodeQuestionBuild:
    session: PolishSession
    context: dict[str, Any]
    plan: dict[str, Any]
    state: dict[str, Any]
    requested_ref: str | None
    question_context: ProgressNodeQuestionContext
    draft: PolishQuestionDraft
    question_pattern: QuestionPattern
    scenario_constraint: ScenarioConstraint
    quality_result: QuestionQualityResult
    question_metadata: QuestionMetadata
    evidence_signals: EvidenceSignalSet


class PolishProgressTreeLlmService:
    """Call the configured LLM transport and normalize progress tree outputs."""

    def __init__(self, transport: LlmTransport | None) -> None:
        self._transport = transport

    def generate_initial(self, context: dict[str, Any]) -> dict[str, Any]:
        planner = _progress_tree_planner()
        if planner == PROGRESS_TREE_PLANNER_QUALITY_FIRST:
            return PolishProgressTreeQualityFirstPlanner(self._transport).generate_initial(context)
        if planner == PROGRESS_TREE_PLANNER_V2_PIPELINE:
            return PolishProgressTreeV2Pipeline(self._transport).generate_initial(context)

        if not has_sufficient_progress_context(context):
            return _insufficient_artifacts(context)
        if self._transport is None:
            return _failed_artifacts(context, reason="llm_transport_missing")

        try:
            result = self._transport.generate(
                LlmTransportRequest(
                    contract_ids=POLISH_PROGRESS_TREE_PLAN_CONTRACT_IDS,
                    task_type="polish_progress_tree_plan",
                    input_refs=_input_refs(context),
                    evidence_bundle=build_initial_progress_tree_prompt(context),
                )
            )
        except (LlmTransportConfigurationError, LlmTransportUnavailableError, LlmTransportResponseError):
            return _failed_artifacts(context, reason="llm_transport_failed")

        return _normalize_initial_artifacts(result.result, context)

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
        if existing_plan.get("schema_id") in {
            "polish_progress_tree_grounded_plan_v2",
            "polish_progress_quality_first_menu_v1",
        }:
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
            result = self._transport.generate(
                LlmTransportRequest(
                    contract_ids=POLISH_PROGRESS_TREE_STATE_CONTRACT_IDS,
                    task_type="polish_progress_tree_state",
                    input_refs=_input_refs(context),
                    evidence_bundle=build_progress_tree_state_refresh_prompt(
                        context=context,
                        existing_plan=existing_plan,
                        existing_state=existing_state,
                    ),
                )
            )
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


def _progress_tree_planner() -> str:
    value = os.getenv(PROGRESS_TREE_PLANNER_ENV, DEFAULT_PROGRESS_TREE_PLANNER).strip().lower()
    if value in {PROGRESS_TREE_PLANNER_QUALITY_FIRST, PROGRESS_TREE_PLANNER_V2_PIPELINE}:
        return value
    return DEFAULT_PROGRESS_TREE_PLANNER



def build_progress_node_question_context(
    *,
    session: PolishSession,
    context: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str | None,
) -> ProgressNodeQuestionContext:
    node = resolve_progress_node(plan=plan, state=state, requested_ref=requested_ref)
    strategy = _safe_polish_theme_strategy(session.polish_theme)
    context_digest = truncate_text(context.get("content_digest"), max_chars=120)
    if node is None:
        topic = session.custom_topic_text_summary or session.topic_id or "manual_topic"
        fallback_progress_node_ref = truncate_text(requested_ref, max_chars=120) or _node_ref(
            str(context.get("content_digest") or "fallback"),
            f"manual:{topic}",
        )
        fallback_node = {
            "progress_node_ref": fallback_progress_node_ref,
            "title": topic,
            "expected_capability": "补充业务链路、关键指标、失败案例和系统组件后再继续打磨。",
            "related_job_requirements": [],
            "related_resume_evidence": [],
            "missing_points": ["progress_node_ref 不可用"],
        }
        source = PolishQuestionSource(
            index=1,
            source_type="progress_node",
            title=QUESTION_SOURCE_TITLE_BY_TYPE["progress_node"],
            excerpt="未找到可用的 progress_node_ref，已按当前打磨主题生成低置信问题。",
            ref_id=fallback_progress_node_ref,
            availability="unavailable",
        )
        return ProgressNodeQuestionContext(
            session=session,
            context=context,
            plan=plan,
            state=state,
            requested_ref=requested_ref,
            node=fallback_node,
            evidence_chunks=(),
            evidence_refs=(),
            sources=(source,),
            citations="[1]",
            strategy=strategy,
            source_availability="unavailable",
            progress_node_ref=fallback_progress_node_ref,
            context_digest=context_digest,
        )

    evidence_selection = select_progress_tree_evidence_chunks(
        context,
        purpose="next_question",
        existing_plan=plan,
        existing_state=state,
        progress_node_ref=node["progress_node_ref"],
    )
    evidence_chunks = tuple(evidence_selection.selected_chunks)
    evidence_refs = tuple(chunk.chunk_id for chunk in evidence_chunks)
    job_snapshot = context.get("job_snapshot", {}) if isinstance(context.get("job_snapshot"), dict) else {}
    resume_snapshot = context.get("resume_snapshot", {}) if isinstance(context.get("resume_snapshot"), dict) else {}
    match_context = context.get("match_context", {}) if isinstance(context.get("match_context"), dict) else {}
    sources = _index_question_sources(
        [
            _progress_node_source(node),
            _source_from_chunks(
                list(evidence_chunks),
                source_types=QUESTION_SOURCE_JOB_TYPES,
                normalized_source_type="job_requirement",
                fallback_title=QUESTION_SOURCE_TITLE_BY_TYPE["job_requirement"],
                fallback_ref_id=_snapshot_ref_id(job_snapshot, "job_version_id", "job_id"),
                fallback_values=[
                    *node.get("related_job_requirements", []),
                    *job_snapshot.get("requirements", []),
                    *job_snapshot.get("responsibilities", []),
                ],
            ),
            _source_from_chunks(
                list(evidence_chunks),
                source_types=QUESTION_SOURCE_RESUME_TYPES,
                normalized_source_type="resume_evidence",
                fallback_title=QUESTION_SOURCE_TITLE_BY_TYPE["resume_evidence"],
                fallback_ref_id=_snapshot_ref_id(resume_snapshot, "resume_version_id", "resume_id"),
                fallback_values=[
                    *node.get("related_resume_evidence", []),
                    *resume_snapshot.get("project_experiences", []),
                    resume_snapshot.get("summary"),
                ],
            ),
            _source_from_chunks(
                list(evidence_chunks),
                source_types={"match_gap"},
                normalized_source_type="missing_point",
                fallback_title=QUESTION_SOURCE_TITLE_BY_TYPE["missing_point"],
                fallback_ref_id=_snapshot_ref_id(match_context, "analysis_id"),
                fallback_values=[
                    *node.get("missing_points", []),
                    *match_context.get("missing_points", []),
                ],
                required=False,
            ),
            _source_from_chunks(
                list(evidence_chunks),
                source_types={"turn_feedback"},
                normalized_source_type="history_feedback",
                fallback_title=QUESTION_SOURCE_TITLE_BY_TYPE["history_feedback"],
                fallback_ref_id=None,
                fallback_values=[_latest_turn_feedback(context.get("turns", []))],
                required=False,
            ),
        ]
    )
    citations = "".join(f"[{source.index}]" for source in sources)
    return ProgressNodeQuestionContext(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=requested_ref,
        node=node,
        evidence_chunks=evidence_chunks,
        evidence_refs=evidence_refs,
        sources=sources,
        citations=citations,
        strategy=strategy,
        source_availability=_question_source_availability(sources),
        progress_node_ref=node.get("progress_node_ref"),
        context_digest=context_digest,
    )


def build_deterministic_progress_node_question(
    *,
    session: PolishSession,
    context: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str | None,
) -> DeterministicProgressNodeQuestionBuild:
    question_context = build_progress_node_question_context(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=requested_ref,
    )
    question_text, pattern, scenario, quality, metadata, evidence_signals = _build_deterministic_v2_question(
        session=session,
        context=context,
        node=question_context.node,
        evidence_chunks=list(question_context.evidence_chunks),
        evidence_refs=question_context.evidence_refs,
        sources=question_context.sources,
        citations=question_context.citations,
        strategy=question_context.strategy,
    )
    draft = PolishQuestionDraft(
        question_text=question_text,
        question_sources=question_context.sources,
        progress_node_ref=question_context.progress_node_ref,
        evidence_refs=question_context.evidence_refs,
        context_digest=question_context.context_digest,
        question_pattern=pattern.pattern_id,
        quality_score=quality.quality_score,
        confidence_level=scenario.confidence_level,
        low_confidence_flags=metadata.low_confidence_flags,
        expected_answer_dimensions=pattern.expected_answer_dimensions,
        question_metadata=metadata.to_dict(),
        evidence_signal_refs=metadata.evidence_signal_refs,
        builder_version=metadata.builder_version,
        validator_version=metadata.validator_version,
    )
    return DeterministicProgressNodeQuestionBuild(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=requested_ref,
        question_context=question_context,
        draft=draft,
        question_pattern=pattern,
        scenario_constraint=scenario,
        quality_result=quality,
        question_metadata=metadata,
        evidence_signals=evidence_signals,
    )


def build_progress_node_question(
    *,
    session: PolishSession,
    context: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str | None,
) -> PolishQuestionDraft:
    return build_deterministic_progress_node_question(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=requested_ref,
    ).draft


def _build_deterministic_v2_question(
    *,
    session: PolishSession,
    context: dict[str, Any],
    node: dict[str, Any],
    evidence_chunks: list[ProgressEvidenceChunk],
    evidence_refs: tuple[str, ...],
    sources: tuple[PolishQuestionSource, ...],
    citations: str,
    strategy: PolishThemeStrategy,
) -> tuple[str, QuestionPattern, ScenarioConstraint, QuestionQualityResult, QuestionMetadata, EvidenceSignalSet]:
    focus = _question_focus(node)
    evidence_signals = extract_evidence_signals(
        progress_node=node,
        selected_evidence_chunks=evidence_chunks,
        session_context=context,
        theme=strategy.theme,
        custom_topic_text=session.custom_topic_text_summary,
        recent_turns=context.get("turns", []),
    )
    scenario = build_scenario_constraints(
        progress_node_title=focus,
        expected_capability=truncate_text(node.get("expected_capability"), max_chars=240),
        related_job_requirements=_node_text_list(node, "related_job_requirements"),
        related_resume_evidence=_node_text_list(node, "related_resume_evidence"),
        missing_points=[*_node_text_list(node, "missing_points"), *_node_text_list(node, "related_match_gaps")],
        selected_evidence_chunks=evidence_chunks,
        history_feedback=_recent_feedback_texts(context.get("turns", [])),
        custom_topic_text=session.custom_topic_text_summary,
        polish_theme=strategy.theme,
        evidence_signals=evidence_signals,
    )
    pattern = select_question_pattern(
        theme_strategy=strategy,
        scenario_constraint=scenario,
        progress_node_title=focus,
        evidence_signals=evidence_signals,
    )
    question_text = _deterministic_v2_question_text(
        focus=focus,
        pattern=pattern,
        strategy=strategy,
        scenario=scenario,
        citations=citations,
    )
    source_availability = _question_source_availability(sources)
    quality = validate_question_quality(
        question_text=question_text,
        selected_pattern=pattern,
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=evidence_refs,
        recent_question_texts=_recent_question_texts(context.get("turns", [])),
        source_availability=source_availability,
        confidence_level=scenario.confidence_level,
        evidence_signals=evidence_signals,
    )
    if quality.allow_emit:
        metadata = build_question_metadata(
            question_pattern=pattern.pattern_id,
            scenario_constraint=scenario,
            expected_answer_dimensions=pattern.expected_answer_dimensions,
            quality_result=quality,
            evidence_signals=evidence_signals,
            anti_repeat_refs=_recent_question_refs(context.get("turns", [])),
            source_availability=source_availability,
        )
        return question_text, pattern, scenario, quality, metadata, evidence_signals

    repaired_text = repair_question_text(
        question_text=question_text,
        selected_pattern=pattern,
        theme_strategy=strategy,
        citations=citations,
    )
    repaired_quality = validate_question_quality(
        question_text=repaired_text,
        selected_pattern=pattern,
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=evidence_refs,
        recent_question_texts=_recent_question_texts(context.get("turns", [])),
        source_availability=source_availability,
        confidence_level=scenario.confidence_level,
        evidence_signals=evidence_signals,
    )
    if repaired_quality.allow_emit:
        metadata = build_question_metadata(
            question_pattern=pattern.pattern_id,
            scenario_constraint=scenario,
            expected_answer_dimensions=pattern.expected_answer_dimensions,
            quality_result=repaired_quality,
            evidence_signals=evidence_signals,
            anti_repeat_refs=_recent_question_refs(context.get("turns", [])),
            additional_low_confidence_flags=("validator_repaired",),
            source_availability=source_availability,
        )
        return repaired_text, pattern, scenario, repaired_quality, metadata, evidence_signals

    if strategy.theme == "communication":
        fallback_pattern = get_question_pattern("star_communication_refactor")
    elif strategy.theme == "mixed":
        fallback_pattern = get_question_pattern("mixed_technical_expression")
    else:
        fallback_pattern = get_question_pattern("owner_tradeoff_system_design")
    fallback_text = fallback_question_text(focus=focus, selected_pattern=fallback_pattern, citations=citations)
    fallback_quality = validate_question_quality(
        question_text=fallback_text,
        selected_pattern=fallback_pattern,
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=evidence_refs,
        recent_question_texts=(),
        source_availability=source_availability,
        confidence_level="low",
        evidence_signals=evidence_signals,
    )
    metadata = build_question_metadata(
        question_pattern=fallback_pattern.pattern_id,
        scenario_constraint=scenario,
        expected_answer_dimensions=fallback_pattern.expected_answer_dimensions,
        quality_result=fallback_quality,
        evidence_signals=evidence_signals,
        anti_repeat_refs=_recent_question_refs(context.get("turns", [])),
        additional_low_confidence_flags=("pattern_fallback",),
        source_availability=source_availability,
    )
    return fallback_text, fallback_pattern, scenario, fallback_quality, metadata, evidence_signals


def _deterministic_v2_question_text(
    *,
    focus: str,
    pattern: QuestionPattern,
    strategy: PolishThemeStrategy,
    scenario: ScenarioConstraint,
    citations: str,
) -> str:
    dimensions = "、".join(pattern.expected_answer_dimensions[:6])
    if pattern.pattern_id == "real_request_trace_deep_dive":
        return (
            f"围绕「{focus}」，业务约束是并发请求下仍要保持最终一致。请沿完整请求链路拆解："
            "请求进入后锁在哪一层取得，哪些步骤放进本地事务，半事务消息如何提交和确认；"
            "如果锁释放、事务提交、消息发送或消费任一步失败，失败兜底与重试收敛怎么设计？"
            "最后说明为什么不用本地消息表或纯补偿方案，以及你的核心 trade-off 和验证指标。"
            f"回答重点：{dimensions}。{citations}"
        )
    if pattern.pattern_id == "constraint_change_refactor":
        return (
            f"围绕「{focus}」，请先说明新业务约束如何从单一库存演进到仓库维度并发扣减，"
            "再解释如何在获得吞吐提升的同时保持总库存一致、防止总量超卖风险，并控制对账复杂度。"
            "请补充失败路径、上线验证指标和关键 trade-off。"
            f"回答重点：{dimensions}。{citations}"
        )
    if pattern.pattern_id == "state_machine_and_reconciliation":
        return (
            f"围绕「{focus}」，业务约束是双层库存必须可追踪并最终收敛。请定义核心状态和状态流转，"
            "说明如何防重复扣减、防重复回补，遇到重复消息、超时或人工修正时如何定义对账口径和收敛判断。"
            "请给出失败路径、验证指标和必要 trade-off。"
            f"回答重点：{dimensions}。{citations}"
        )
    if pattern.pattern_id == "partial_success_failure_recovery":
        component_text = _component_display(scenario.system_components) or "已出现的多组件链路"
        storage_text = _component_display(
            tuple(component for component in scenario.system_components if component in {"MySQL", "Redis", "Elasticsearch", "ES"})
        ) or "已出现的存储组件"
        return (
            f"围绕「{focus}」，业务约束是 {component_text} 多组件结果要对用户可解释。"
            f"请设计向量化超时后的状态机：当 {storage_text} 出现部分成功 / 部分失败时，如何做重试收敛、断点续跑、幂等保护，"
            "并用线程池隔离、消息堆积治理和成本上限避免高峰期失控。"
            f"回答重点：{dimensions}。{citations}"
        )
    if pattern.pattern_id == "performance_cost_observability":
        return (
            f"围绕「{focus}」，业务约束是 1GB 日志从上传入口进入异步处理后要可追踪地完成。"
            "请按上传入口、解析、切块、向量化、入库拆解管道，说明如何从 15 秒到 3 秒，"
            "并设计削峰填谷、并行度控制、资源隔离、失败重试、成本权衡和可观测指标。"
            f"回答重点：{dimensions}。{citations}"
        )
    if pattern.pattern_id == "agent_tool_failure_context_contamination":
        return (
            f"围绕「{focus}」，业务约束是 Agent 在工具调用、RAG 和记忆之间必须可解释、可回滚。"
            "请拆解一次工具调用失败后的链路：上下文污染如何隔离，计划回滚如何保证不重复执行，"
            "记忆写入和 RAG 召回如何校验，成本和重试上限如何控制，并说明可观测指标。"
            f"回答重点：{dimensions}。{citations}"
        )
    if pattern.pattern_id == "star_communication_refactor":
        return (
            f"围绕「{focus}」，请用 STAR 结构重讲一遍：用 30 秒做背景压缩，明确个人职责边界，"
            "按逻辑顺序说明关键动作和取舍表达，最后用结果指标、复盘总结和面试口语化表达收束。"
            f"回答重点：{dimensions}。{citations}"
        )
    if pattern.pattern_id == "mixed_technical_expression":
        return (
            f"本题权重比例为显性技术 {strategy.explicit_weight}%、隐性表达 {strategy.implicit_weight}%。"
            f"围绕「{focus}」，请先说明业务约束，再展开技术深度：{scenario.failure_mode}"
            "你会如何组织方案链路、失败兜底、验证指标和成本控制；同时请按背景、约束、方案、结果、复盘的表达结构回答。"
            f"回答重点：{dimensions}。{citations}"
        )
    low_confidence_prefix = "低置信度：" if scenario.confidence_level == "low" else ""
    return (
        f"{low_confidence_prefix}围绕「{focus}」，请先限定业务约束、项目链路、系统组件和用户可见结果，"
        "再选择一个失败路径说明状态机或幂等设计、性能或成本约束、验证指标、状态收敛口径和核心 trade-off。"
        "如果当前材料不足，请补充项目链路、关键指标、失败案例和系统组件后再继续深挖。"
        f"回答重点：{dimensions}。{citations}"
    )


def _component_display(components: tuple[str, ...]) -> str:
    display = []
    for component in components:
        if component == "Elasticsearch":
            label = "Elasticsearch（ES）"
        elif component == "向量化":
            label = "向量化服务"
        else:
            label = component
        if label not in display:
            display.append(label)
    return " / ".join(display)


def _recent_question_refs(turns: object) -> tuple[str, ...]:
    if not isinstance(turns, list):
        return ()
    refs: list[str] = []
    for index, turn in enumerate(turns[-5:], start=1):
        if not isinstance(turn, dict):
            continue
        explicit_ref = truncate_text(turn.get("question_id") or turn.get("question_ref"), max_chars=120)
        if explicit_ref:
            refs.append(explicit_ref)
            continue
        text = truncate_text(turn.get("question_text"), max_chars=400)
        if text:
            refs.append(f"recent_question:{index}:{sha256(text.encode('utf-8')).hexdigest()[:12]}")
    return tuple(refs)


def _node_text_list(node: dict[str, Any], key: str) -> list[str]:
    value = node.get(key)
    if isinstance(value, (list, tuple)):
        return [text for item in value if (text := truncate_text(item, max_chars=240))]
    text = truncate_text(value, max_chars=240)
    return [text] if text else []


def _recent_question_texts(turns: object) -> list[str]:
    if not isinstance(turns, list):
        return []
    result: list[str] = []
    for turn in turns[-5:]:
        if isinstance(turn, dict) and (text := truncate_text(turn.get("question_text"), max_chars=400)):
            result.append(text)
    return result


def _recent_feedback_texts(turns: object) -> list[str]:
    if not isinstance(turns, list):
        return []
    result: list[str] = []
    for turn in turns[-5:]:
        if isinstance(turn, dict) and (text := truncate_text(turn.get("feedback_text"), max_chars=240)):
            result.append(text)
    return result


def _question_source_availability(sources: tuple[PolishQuestionSource, ...]) -> str:
    if not sources:
        return "unavailable"
    availability = {source.availability for source in sources}
    if availability == {"available"}:
        return "available"
    if "available" in availability:
        return "partial"
    return "unavailable"


def _safe_polish_theme_strategy(theme: str | None) -> PolishThemeStrategy:
    try:
        return resolve_polish_theme_strategy(theme)
    except ValueError:
        return resolve_polish_theme_strategy(None)


def build_progress_node_question_text(
    *,
    session: PolishSession,
    context: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str | None,
) -> str:
    return build_progress_node_question(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=requested_ref,
    ).question_text


def _index_question_sources(sources: list[PolishQuestionSource | None]) -> tuple[PolishQuestionSource, ...]:
    indexed: list[PolishQuestionSource] = []
    seen: set[tuple[str, str, str]] = set()
    for source in sources:
        if source is None:
            continue
        key = (source.source_type, source.title, source.excerpt)
        if key in seen:
            continue
        seen.add(key)
        indexed.append(
            PolishQuestionSource(
                index=len(indexed) + 1,
                source_type=source.source_type,
                title=source.title,
                excerpt=source.excerpt,
                ref_id=source.ref_id,
                availability=source.availability,
            )
        )
    return tuple(indexed)


def _progress_node_source(node: dict[str, Any]) -> PolishQuestionSource:
    return PolishQuestionSource(
        index=0,
        source_type="progress_node",
        title=QUESTION_SOURCE_TITLE_BY_TYPE["progress_node"],
        excerpt=_source_excerpt(
            "；".join(
                item
                for item in (
                    f"节点：{truncate_text(node.get('title'), max_chars=80)}",
                    f"能力目标：{truncate_text(node.get('expected_capability'), max_chars=120)}",
                )
                if item
            )
        ),
        ref_id=truncate_text(node.get("progress_node_ref"), max_chars=120) or None,
        availability="available",
    )


def _source_from_chunks(
    chunks: list[ProgressEvidenceChunk],
    *,
    source_types: set[str],
    normalized_source_type: str,
    fallback_title: str,
    fallback_ref_id: str | None,
    fallback_values: list[object | None],
    required: bool = True,
) -> PolishQuestionSource | None:
    chunk = next((item for item in chunks if item.source_type in source_types and item.text), None)
    if chunk is not None:
        return PolishQuestionSource(
            index=0,
            source_type=normalized_source_type,
            title=_question_source_title(normalized_source_type, chunk.source_type),
            excerpt=_source_excerpt(chunk.text),
            ref_id=_chunk_ref_id(chunk) or fallback_ref_id,
            availability="available",
        )

    fallback_text = _first_available_text(*fallback_values)
    if fallback_text:
        return PolishQuestionSource(
            index=0,
            source_type=normalized_source_type,
            title=fallback_title,
            excerpt=_source_excerpt(fallback_text),
            ref_id=fallback_ref_id,
            availability="partial",
        )
    if not required:
        return None
    return PolishQuestionSource(
        index=0,
        source_type=normalized_source_type,
        title=fallback_title,
        excerpt="当前来源暂不可用，题目已按进展节点低置信生成。",
        ref_id=fallback_ref_id,
        availability="unavailable",
    )


def _question_source_title(normalized_source_type: str, raw_source_type: str) -> str:
    if raw_source_type == "job_responsibility":
        return "岗位职责"
    if raw_source_type == "resume_skill":
        return "简历技能证据"
    if raw_source_type == "resume_work_experience":
        return "简历工作经历"
    return QUESTION_SOURCE_TITLE_BY_TYPE.get(normalized_source_type, "来源")


def _question_focus(node: dict[str, Any]) -> str:
    return (
        truncate_text(node.get("title"), max_chars=80)
        or truncate_text(node.get("expected_capability"), max_chars=80)
        or "当前能力打磨目标"
    )


def _source_excerpt(value: object | None) -> str:
    return truncate_text(value, max_chars=180) or "内容待补充"


def _first_available_text(*values: object | None) -> str | None:
    for value in values:
        if isinstance(value, (list, tuple)):
            nested = _first_available_text(*value)
            if nested:
                return nested
            continue
        text = truncate_text(value, max_chars=320)
        if text:
            return text
    return None


def _chunk_ref_id(chunk: ProgressEvidenceChunk) -> str | None:
    source_ref = chunk.source_ref or {}
    for key in ("job_version_id", "resume_version_id", "analysis_id", "question_id", "turn_index"):
        ref_value = source_ref.get(key)
        if ref_value:
            return str(ref_value)
    return chunk.chunk_id


def _snapshot_ref_id(snapshot: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = snapshot.get(key)
        if value:
            return str(value)
    return None


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


def _normalize_initial_artifacts(result: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    plan_payload = result.get("progress_tree_plan") or result.get("plan")
    state_payload = result.get("progress_tree_state") or result.get("state")
    if not isinstance(plan_payload, dict):
        return _failed_artifacts(context, reason="llm_plan_missing")

    plan = _normalize_plan(
        plan_payload,
        context_digest=context["content_digest"],
        prompt_version=_metadata_value(
            result,
            plan_payload,
            "prompt_version",
            POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        ),
        schema_id=_metadata_value(result, plan_payload, "schema_id", POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID),
        schema_version=_metadata_value(
            result,
            plan_payload,
            "schema_version",
            POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
        ),
    )
    if plan["status"] != PROGRESS_TREE_STATUS_READY:
        return {
            "status": plan["status"],
            "progress_tree_plan": plan,
            "progress_tree_state": _empty_state(
                plan["status"],
                prompt_version=POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
            ),
            "progress_percent": 0,
        }
    if not isinstance(state_payload, dict):
        state = _initial_state_fallback(
            plan,
            prompt_version=POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
            failure_reason="llm_state_invalid_state_fallback",
        )
        return {
            "status": PROGRESS_TREE_STATUS_READY,
            "progress_tree_plan": plan,
            "progress_tree_state": state,
            "progress_percent": _progress_percent(state),
        }

    state = _normalize_state(
        state_payload,
        existing_plan=plan,
        allow_refresh_failed=False,
        prompt_version=_metadata_value(
            result,
            state_payload,
            "prompt_version",
            POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        ),
        schema_id=_metadata_value(result, state_payload, "schema_id", POLISH_PROGRESS_TREE_STATE_SCHEMA_ID),
        schema_version=_metadata_value(
            result,
            state_payload,
            "schema_version",
            POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
        ),
    )
    if state["status"] != PROGRESS_TREE_STATUS_READY:
        state = _initial_state_fallback(
            plan,
            prompt_version=POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
            failure_reason="llm_state_invalid_state_fallback",
        )
    return {
        "status": PROGRESS_TREE_STATUS_READY,
        "progress_tree_plan": plan,
        "progress_tree_state": state,
        "progress_percent": _progress_percent(state),
    }


def _normalize_plan(
    plan_payload: dict[str, Any],
    *,
    context_digest: str,
    prompt_version: str,
    schema_id: str,
    schema_version: str,
) -> dict[str, Any]:
    raw_status = plan_payload.get("status")
    if raw_status == PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT:
        return {
            "schema_id": schema_id,
            "schema_version": schema_version,
            "prompt_version": prompt_version,
            "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
            "context_digest": context_digest,
            "nodes": [],
        }
    nodes = [
        node
        for index, item in enumerate(plan_payload.get("nodes", []), start=1)
        if (node := _normalize_node(item, index=index, context_digest=context_digest)) is not None
    ]
    if not nodes:
        return {
            "schema_id": schema_id,
            "schema_version": schema_version,
            "prompt_version": prompt_version,
            "status": PROGRESS_TREE_STATUS_FAILED,
            "context_digest": context_digest,
            "nodes": [],
        }
    return {
        "schema_id": schema_id,
        "schema_version": schema_version,
        "prompt_version": prompt_version,
        "status": PROGRESS_TREE_STATUS_READY,
        "context_digest": context_digest,
        "nodes": nodes[:10],
    }


def _normalize_node(item: object, *, index: int, context_digest: str) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    title = truncate_text(item.get("title"), max_chars=120)
    expected_capability = truncate_text(item.get("expected_capability"), max_chars=480)
    if not title or not expected_capability:
        return None
    node_ref = truncate_text(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
    children = [
        child
        for child_index, child_item in enumerate(item.get("children", []), start=1)
        if (
            child := _normalize_node(
                child_item,
                index=(index * 100) + child_index,
                context_digest=context_digest,
            )
        )
        is not None
    ]
    return {
        "progress_node_ref": node_ref or _node_ref(context_digest, f"{index}:{title}"),
        "title": title,
        "expected_capability": expected_capability,
        "related_job_requirements": _string_list(item.get("related_job_requirements"), limit=5),
        "related_resume_evidence": _string_list(item.get("related_resume_evidence"), limit=5),
        "missing_points": _string_list(item.get("missing_points"), limit=5),
        "evidence_chunk_ids": _node_evidence_chunk_ids(item),
        "children": children[:10],
    }


def _node_evidence_chunk_ids(item: dict[str, Any]) -> list[str]:
    evidence_chunk_ids = _string_list(item.get("evidence_chunk_ids"), limit=20)
    if evidence_chunk_ids:
        return evidence_chunk_ids
    evidence = item.get("evidence")
    if isinstance(evidence, dict):
        return _string_list(evidence.get("evidence_chunk_ids"), limit=20)
    return []


def _normalize_state(
    state_payload: dict[str, Any],
    *,
    existing_plan: dict[str, Any],
    allow_refresh_failed: bool,
    prompt_version: str,
    schema_id: str,
    schema_version: str,
) -> dict[str, Any]:
    if state_payload.get("status") == PROGRESS_TREE_STATUS_REFRESH_FAILED and allow_refresh_failed:
        return _empty_state(PROGRESS_TREE_STATUS_REFRESH_FAILED, prompt_version=prompt_version)

    plan_nodes = _flatten_progress_nodes(existing_plan.get("nodes", []))
    if not plan_nodes:
        return _empty_state(PROGRESS_TREE_STATUS_FAILED, prompt_version=prompt_version)
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
        return _empty_state(PROGRESS_TREE_STATUS_FAILED, prompt_version=prompt_version)

    return {
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
    }


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
        "schema_id": POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "context_digest": context["content_digest"],
        "nodes": [],
    }
    return {
        "status": PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
        "progress_tree_plan": plan,
        "progress_tree_state": _empty_state(
            PROGRESS_TREE_STATUS_INSUFFICIENT_CONTEXT,
            prompt_version=POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        ),
        "progress_percent": 0,
    }


def _failed_artifacts(context: dict[str, Any], *, reason: str) -> dict[str, Any]:
    plan = {
        "schema_id": POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
        "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        "status": PROGRESS_TREE_STATUS_FAILED,
        "context_digest": context["content_digest"],
        "nodes": [],
        "failure_reason": reason,
    }
    return {
        "status": PROGRESS_TREE_STATUS_FAILED,
        "progress_tree_plan": plan,
        "progress_tree_state": _empty_state(
            PROGRESS_TREE_STATUS_FAILED,
            prompt_version=POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
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


def _bounded_int(value: object, lower: int, upper: int) -> int:
    if isinstance(value, bool):
        return lower
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return lower
    return max(lower, min(upper, parsed))


def _normalize_status(value: object) -> str:
    if value in {"completed", "mastered"}:
        return "completed"
    if value in {"in_progress", "active", "current"}:
        return "in_progress"
    return "pending"


def _node_ref(context_digest: str, seed: str) -> str:
    return f"progress_{sha256(f'{context_digest}:{seed}'.encode('utf-8')).hexdigest()[:16]}"


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
