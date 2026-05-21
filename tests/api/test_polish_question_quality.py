from __future__ import annotations

from collections.abc import Iterable, Sequence

import pytest

from app.application.polish.entities import PolishSession
from app.application.polish.evidence_signals import extract_evidence_signals
from app.application.polish.progress_tree import build_progress_node_question
from app.application.polish.question_metadata import (
    QuestionBuilderVersion,
    build_question_metadata,
    empty_question_metadata,
)
from app.application.polish.question_patterns import QUESTION_PATTERNS, get_question_pattern
from app.application.polish.question_quality import validate_question_quality
from app.application.polish.scenario_constraints import build_scenario_constraints
from app.application.polish.theme_strategy import resolve_polish_theme_strategy
from app.domain.shared.clock import utc_now


LEGACY_TEMPLATE_PHRASES = (
    "请选一个你实际参与的具体场景",
    "讲清楚当时要解决的问题",
    "你负责的技术改造或决策",
    "为什么这样取舍",
    "上线后如何验证效果",
)


def test_question_pattern_library_exposes_required_v2_patterns() -> None:
    required_ids = {
        "real_request_trace_deep_dive",
        "constraint_change_refactor",
        "state_machine_and_reconciliation",
        "partial_success_failure_recovery",
        "owner_tradeoff_system_design",
        "performance_cost_observability",
        "star_communication_refactor",
        "mixed_technical_expression",
    }

    assert required_ids.issubset(set(QUESTION_PATTERNS))
    for pattern_id in required_ids:
        pattern = get_question_pattern(pattern_id)
        assert pattern.pattern_id == pattern_id
        assert pattern.applicable_themes
        assert pattern.required_question_elements
        assert pattern.expected_answer_dimensions
        assert pattern.quality_rules


def test_quality_validator_blocks_legacy_template_question() -> None:
    strategy = resolve_polish_theme_strategy("technical")
    scenario = build_scenario_constraints(
        progress_node_title="混合检索策略设计与优化",
        expected_capability="能说明检索策略的工程取舍。",
        related_job_requirements=[],
        related_resume_evidence=[],
        missing_points=[],
        selected_evidence_chunks=[],
        history_feedback=[],
        custom_topic_text=None,
        polish_theme=strategy.theme,
    )
    pattern = get_question_pattern("owner_tradeoff_system_design")

    result = validate_question_quality(
        question_text=(
            "针对「混合检索策略设计与优化」这个进展节点，请选一个你实际参与的具体场景，"
            "讲清楚当时要解决的问题、你负责的技术改造或决策、为什么这样取舍，以及上线后如何验证效果。"
        ),
        selected_pattern=pattern,
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=[],
        recent_question_texts=[],
        source_availability="unavailable",
        confidence_level=scenario.confidence_level,
    )

    assert result.allow_emit is False
    assert "legacy_template" in result.blocking_issues


@pytest.mark.parametrize(
    ("case_id", "title", "evidence", "expected_pattern", "required_terms"),
    [
        (
            "distributed_lock_transaction_message",
            "分布式锁与事务消息最终一致",
            "订单库存扣减请求链路使用分布式锁、本地事务、半事务消息保障最终一致。",
            "real_request_trace_deep_dive",
            ("完整请求链路", "锁在哪一层", "本地事务", "半事务消息", "失败兜底", "本地消息表", "纯补偿方案", "trade-off"),
        ),
        (
            "warehouse_concurrent_deduction",
            "仓库维度并发扣减",
            "物料库存从全局扣减改为仓库维度并发扣减，需要提升吞吐并保持总库存一致。",
            "constraint_change_refactor",
            ("仓库维度", "吞吐提升", "总库存一致", "超卖风险", "对账复杂度"),
        ),
        (
            "two_layer_inventory_state_machine",
            "双层库存状态机与对账机制",
            "双层库存需要状态机、对账、扣减和回补，避免重复扣减与重复回补。",
            "state_machine_and_reconciliation",
            ("核心状态", "状态流转", "防重复扣减", "防重复回补", "对账口径", "收敛判断"),
        ),
        (
            "large_log_async_pipeline",
            "1GB 日志文件异步处理管道",
            "1GB 日志从上传入口进入异步处理，解析、切块、向量化、入库从 15 秒优化到 3 秒。",
            "performance_cost_observability",
            ("上传入口", "解析", "切块", "向量化", "入库", "削峰填谷", "并行度控制", "资源隔离", "失败重试", "成本权衡"),
        ),
        (
            "minio_mq_vector_partial_success",
            "MinIO / MQ / 向量化部分成功不一致",
            "MinIO 上传后通过 MQ 触发向量化，向量化服务高峰期超时，MySQL / Redis / ES 出现部分成功。",
            "partial_success_failure_recovery",
            (
                "MinIO",
                "MQ",
                "向量化超时",
                "部分成功",
                "部分失败",
                "MySQL",
                "Redis",
                "ES",
                "状态机",
                "重试收敛",
                "断点续跑",
                "幂等",
                "线程池",
                "消息堆积",
                "成本上限",
            ),
        ),
    ],
)
def test_progress_node_question_generates_golden_technical_cases(
    case_id: str,
    title: str,
    evidence: str,
    expected_pattern: str,
    required_terms: Sequence[str],
) -> None:
    draft = _build_question(
        title=title,
        evidence=evidence,
        polish_theme="technical",
        node_ref=f"node_{case_id}",
        expected_capability=f"能围绕{title}说明工程链路、异常收敛和取舍。",
    )

    _assert_contains_all(draft.question_text, required_terms)
    _assert_no_legacy_template(draft.question_text)
    assert draft.question_pattern == expected_pattern
    assert draft.quality_score >= 80
    assert draft.confidence_level in {"high", "medium"}
    assert draft.expected_answer_dimensions
    assert draft.progress_node_ref == f"node_{case_id}"
    assert draft.evidence_refs
    assert draft.context_digest == "quality-test-digest"
    assert "[1]" in draft.question_text


def test_abstract_node_degrades_without_legacy_template_or_fabricated_entities() -> None:
    draft = _build_question(
        title="混合检索策略设计与优化",
        evidence="",
        polish_theme="technical",
        include_evidence=False,
        node_ref="node_abstract_retrieval",
        expected_capability="能说明检索策略的约束、指标和失败处理。",
    )

    _assert_no_legacy_template(draft.question_text)
    assert draft.confidence_level == "low"
    assert draft.low_confidence_flags
    _assert_contains_any(draft.question_text, ("低置信度", "补充项目链路", "关键指标", "失败案例"))
    _assert_contains_all(draft.question_text, ("业务约束", "性能或成本约束", "失败路径", "验证指标"))
    for unsupported_entity in ("MinIO", "MQ", "Redis", "ES", "MySQL"):
        assert unsupported_entity not in draft.question_text


def test_partial_success_without_concrete_entities_falls_back_safely() -> None:
    draft = _build_question(
        title="部分成功状态收敛",
        evidence="链路存在部分成功和部分失败，但材料未说明具体系统组件。",
        polish_theme="technical",
        node_ref="node_partial_success_abstract",
        expected_capability="能说明部分成功后的状态收敛和补偿口径。",
    )

    _assert_no_legacy_template(draft.question_text)
    assert draft.question_pattern == "owner_tradeoff_system_design"
    assert draft.quality_score >= 70
    _assert_contains_all(draft.question_text, ("业务约束", "失败路径", "性能或成本约束", "验证指标", "trade-off"))
    for unsupported_entity in ("MinIO", "MQ", "Redis", "ES", "MySQL"):
        assert unsupported_entity not in draft.question_text


def test_partial_success_metadata_uses_only_signaled_storage_components() -> None:
    draft = _build_question(
        title="MinIO / MQ / 向量化部分成功不一致",
        evidence="MinIO 上传后通过 MQ 触发向量化，MySQL 出现部分成功，需要重试收敛。",
        polish_theme="technical",
        node_ref="node_partial_success_mysql_only",
        expected_capability="能说明多组件链路的失败恢复。",
    )

    assert draft.question_pattern == "partial_success_failure_recovery"
    summary = draft.question_metadata["scenario_constraint_summary"]
    assert "MySQL" in summary
    assert "Redis" not in summary
    assert "ES" not in summary
    assert "Elasticsearch" not in summary


def test_quality_validator_blocks_fabricated_concrete_entities_from_signals() -> None:
    strategy = resolve_polish_theme_strategy("technical")
    signals = extract_evidence_signals(
        progress_node={"progress_node_ref": "node_no_minio", "title": "缓存链路失败恢复"},
        selected_evidence_chunks=[],
        session_context={},
        theme=strategy.theme,
    )
    scenario = build_scenario_constraints(
        progress_node_title="缓存链路失败恢复",
        expected_capability="能说明失败恢复。",
        related_job_requirements=[],
        related_resume_evidence=[],
        missing_points=[],
        selected_evidence_chunks=[],
        history_feedback=[],
        custom_topic_text=None,
        polish_theme=strategy.theme,
        evidence_signals=signals,
    )

    result = validate_question_quality(
        question_text="围绕「缓存链路失败恢复」，请说明 MinIO、Redis 和 ES 的失败路径、成本和验证指标。",
        selected_pattern=get_question_pattern("owner_tradeoff_system_design"),
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=[],
        recent_question_texts=[],
        source_availability="unavailable",
        confidence_level=scenario.confidence_level,
        evidence_signals=signals,
    )

    assert result.allow_emit is False
    assert "unsupported_entity_reference" in result.blocking_issues


def test_quality_validator_blocks_fabricated_mq_from_signals() -> None:
    strategy = resolve_polish_theme_strategy("technical")
    signals = extract_evidence_signals(
        progress_node={"progress_node_ref": "node_no_mq", "title": "缓存链路失败恢复"},
        selected_evidence_chunks=[],
        session_context={},
        theme=strategy.theme,
    )
    scenario = build_scenario_constraints(
        progress_node_title="缓存链路失败恢复",
        expected_capability="能说明失败恢复。",
        related_job_requirements=[],
        related_resume_evidence=[],
        missing_points=[],
        selected_evidence_chunks=[],
        history_feedback=[],
        custom_topic_text=None,
        polish_theme=strategy.theme,
        evidence_signals=signals,
    )

    result = validate_question_quality(
        question_text="围绕「缓存链路失败恢复」，业务约束是链路需要可恢复。请说明 MQ 的失败路径、性能或成本约束、验证指标和 trade-off。",
        selected_pattern=get_question_pattern("owner_tradeoff_system_design"),
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=[],
        recent_question_texts=[],
        source_availability="unavailable",
        confidence_level=scenario.confidence_level,
        evidence_signals=signals,
    )

    assert result.allow_emit is False
    assert "unsupported_entity_reference" in result.blocking_issues


def test_question_metadata_roundtrip_and_low_confidence_merge() -> None:
    strategy = resolve_polish_theme_strategy("technical")
    signals = extract_evidence_signals(
        progress_node={"progress_node_ref": "node_metadata", "title": "系统设计能力"},
        selected_evidence_chunks=[],
        session_context={},
        theme=strategy.theme,
    )
    scenario = build_scenario_constraints(
        progress_node_title="系统设计能力",
        expected_capability=None,
        related_job_requirements=[],
        related_resume_evidence=[],
        missing_points=[],
        selected_evidence_chunks=[],
        history_feedback=[],
        custom_topic_text=None,
        polish_theme=strategy.theme,
        evidence_signals=signals,
    )
    quality = validate_question_quality(
        question_text=(
            "低置信度：围绕「系统设计能力」，请先限定业务约束、失败路径、"
            "性能或成本约束、验证指标和 trade-off。"
        ),
        selected_pattern=get_question_pattern("owner_tradeoff_system_design"),
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=[],
        recent_question_texts=[],
        source_availability="unavailable",
        confidence_level=scenario.confidence_level,
        evidence_signals=signals,
    )

    metadata = build_question_metadata(
        question_pattern="owner_tradeoff_system_design",
        scenario_constraint=scenario,
        expected_answer_dimensions=("业务边界", "失败路径"),
        quality_result=quality,
        evidence_signals=signals,
        anti_repeat_refs=("recent_question_001",),
        additional_low_confidence_flags=("validator_repaired",),
    )
    payload = metadata.to_dict()

    assert payload["question_pattern"] == "owner_tradeoff_system_design"
    assert payload["builder_version"] == QuestionBuilderVersion.EVIDENCE_AWARE_V1.value
    assert payload["validator_version"]
    assert payload["signal_version"]
    assert payload["evidence_signal_refs"]
    assert "validator_repaired" in payload["low_confidence_flags"]
    assert "weak_metric_evidence" in payload["low_confidence_flags"]
    assert payload["anti_repeat_refs"] == ["recent_question_001"]

    empty = empty_question_metadata().to_dict()
    assert empty["question_pattern"] is None
    assert empty["quality_score"] is None
    assert empty["builder_version"]


def test_communication_question_requires_star_expression_structure() -> None:
    draft = _build_question(
        title="项目贡献与沟通复盘",
        evidence="候选人需要把复杂项目用面试表达讲清楚，避免职责边界含糊。",
        polish_theme="communication",
        node_ref="node_communication",
        expected_capability="能用结构化表达讲清楚项目背景、个人职责和复盘。",
    )

    _assert_contains_all(draft.question_text, ("STAR", "背景压缩", "个人职责边界", "逻辑顺序"))
    _assert_contains_any(draft.question_text, ("复盘总结", "口语化表达"))
    assert draft.question_pattern == "star_communication_refactor"
    assert "半事务消息" not in draft.question_text
    assert "锁在哪一层" not in draft.question_text


def test_mixed_question_exposes_weights_and_expression_structure() -> None:
    draft = _build_question(
        title="AI Agent 任务规划与工具调用机制",
        evidence="Agent 工具调用需要处理工具失败、计划回滚、上下文污染和成本控制。",
        polish_theme="mixed",
        node_ref="node_mixed_agent",
        expected_capability="能同时说明技术深度与表达结构。",
    )

    _assert_contains_all(draft.question_text, ("显性技术", "隐性表达", "权重比例", "技术深度", "表达结构"))
    _assert_contains_any(draft.question_text, ("工具调用失败", "计划回滚", "上下文污染", "成本控制"))
    assert draft.question_pattern == "mixed_technical_expression"
    assert draft.quality_score >= 80
    assert draft.question_metadata
    assert draft.question_metadata["builder_version"] == QuestionBuilderVersion.EVIDENCE_AWARE_V1.value
    assert draft.evidence_signal_refs


def _build_question(
    *,
    title: str,
    evidence: str,
    polish_theme: str,
    node_ref: str,
    expected_capability: str,
    include_evidence: bool = True,
):
    now = utc_now()
    session = PolishSession(
        session_id=f"ses_{node_ref}",
        owner_id="usr_quality",
        actor_id="usr_quality",
        binding_id="bind_quality",
        resume_id="res_quality",
        resume_version_id="res_ver_quality",
        job_id="job_quality",
        job_version_id="job_ver_quality",
        status="running",
        topic_id="topic_technical_depth",
        subtopic_id=None,
        custom_topic_text_summary=None,
        created_at=now,
        updated_at=now,
        polish_theme=polish_theme,
        progress_tree_status="ready",
    )
    node = {
        "progress_node_ref": node_ref,
        "title": title,
        "expected_capability": expected_capability,
        "related_job_requirements": [evidence] if evidence else [],
        "related_resume_evidence": [evidence] if evidence else [],
        "missing_points": [],
        "children": [],
    }
    context = {
        "content_digest": "quality-test-digest",
        "job_snapshot": {
            "job_id": "job_quality",
            "job_version_id": "job_ver_quality",
            "requirements": [evidence] if include_evidence and evidence else [],
            "responsibilities": [evidence] if include_evidence and evidence else [],
        },
        "resume_snapshot": {
            "resume_id": "res_quality",
            "resume_version_id": "res_ver_quality",
            "summary": evidence if include_evidence and evidence else None,
            "project_experiences": [evidence] if include_evidence and evidence else [],
            "skills": [],
        },
        "match_context": {
            "analysis_id": "ana_quality",
            "missing_points": [],
        },
        "turns": [],
    }
    return build_progress_node_question(
        session=session,
        context=context,
        plan={"status": "ready", "context_digest": "quality-test-digest", "nodes": [node]},
        state={
            "status": "ready",
            "current_priority": {
                "progress_node_ref": node_ref,
                "title": title,
                "expected_capability": expected_capability,
            },
            "node_states": [],
            "progress": {"progress_percent": 0},
        },
        requested_ref=node_ref,
    )


def _assert_contains_all(text: str, terms: Iterable[str]) -> None:
    missing = [term for term in terms if term not in text]
    assert not missing, f"missing terms: {missing}\n{text}"


def _assert_contains_any(text: str, terms: Iterable[str]) -> None:
    assert any(term in text for term in terms), text


def _assert_no_legacy_template(text: str) -> None:
    assert not all(phrase in text for phrase in LEGACY_TEMPLATE_PHRASES), text
