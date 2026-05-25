from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from types import SimpleNamespace

import pytest

from app.application.polish.entities import PolishSession
from app.application.polish.evidence_signals import extract_evidence_signals
from app.application.polish.progress_tree import build_progress_node_question
from app.application.polish.question_metadata import (
    QuestionBuilderVersion,
    build_question_metadata,
    empty_question_metadata,
    normalize_question_metadata,
    question_metadata_to_dict,
)
from app.application.polish.question_patterns import QUESTION_PATTERNS, get_question_pattern
from app.application.polish.question_quality import fallback_question_text, validate_question_quality
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

INSUFFICIENT_PRIMARY_EVIDENCE_FALLBACK = (
    "当前材料不足以支撑具体业务场景。请先补充一个你真实参与的项目链路，"
    "包括业务入口、你的职责边界、一个失败案例和一个验证指标，再按技术深度和表达结构回答。"
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


def test_repeated_same_category_question_rotates_template_and_focus() -> None:
    title = "1GB 日志文件异步处理管道"
    evidence = "1GB 日志从上传入口进入异步处理，解析、切块、向量化、入库从 15 秒优化到 3 秒。"
    first = _build_question(
        title=title,
        evidence=evidence,
        polish_theme="technical",
        node_ref="node_large_log_repeat",
        expected_capability="能解释异步处理管道的性能、成本和可观测性。",
    )
    second = _build_question(
        title=title,
        evidence=evidence,
        polish_theme="technical",
        node_ref="node_large_log_repeat",
        expected_capability="能解释异步处理管道的性能、成本和可观测性。",
        turns=[
            {
                "question_id": "que_first_large_log",
                "progress_node_ref": "node_large_log_repeat",
                "question_text": first.question_text,
                "question_metadata": first.question_metadata,
            }
        ],
    )

    first_metadata = first.question_metadata
    second_metadata = second.question_metadata
    assert first_metadata["template_signature"] != second_metadata["template_signature"]
    assert first_metadata["blueprint_signature"] != second_metadata["blueprint_signature"]
    assert first_metadata["focus_key"] != second_metadata["focus_key"]
    assert second_metadata["duplicate_gate_result"] == "rotated"
    assert second_metadata["similarity_checked"] is True
    assert second_metadata["mastery_exception_used"] is False
    assert "15 秒到 3 秒" in first.question_text
    assert "15 秒到 3 秒" not in second.question_text


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


def test_primary_evidence_grounding_blocks_raw_dump_bad_question() -> None:
    strategy = resolve_polish_theme_strategy("technical")
    scenario = SimpleNamespace(
        business_constraint="1GB 日志上传、解析、切块、向量化、入库",
        failure_mode="日志解析失败或入库失败会导致链路卡住",
        scale_or_performance_constraint="1GB 日志从 15 秒优化到 3 秒",
        consistency_constraint="切块、向量化和入库状态必须一致",
        cost_constraint="向量化成本需要可控",
        observability_constraint="解析耗时、入库成功率和错误率",
        system_components=("日志上传", "解析", "切块", "向量化", "入库"),
        technical_entities=("日志", "向量化"),
        metrics=("1GB", "15 秒", "3 秒"),
        confidence_level="high",
        low_confidence_flags=(),
        evidence_refs=("match_gap_001",),
    )
    primary_question_evidence = {
        "ref": "resume_project_001",
        "source_type": "resume_project",
        "title": "物料库存处理工作流",
        "summary": "物料库存处理工作流：Redisson 分布式锁 + RocketMQ 事务消息",
        "claim_mode": "candidate_experience",
        "allowed_source_refs": ["resume_project_001"],
        "confidence_level": "high",
    }

    result = validate_question_quality(
        question_text=(
            "围绕「分布式锁与事务消息最终一致性设计」，业务约束是 1GB 日志上传、解析、切块、向量化、入库。"
            "请从 Owner 视角说明库存扣减链路中 Redisson 分布式锁、RocketMQ 事务消息和日志向量化管道的失败路径、"
            "性能或成本约束、验证指标、可观测指标和核心 trade-off。"
        ),
        selected_pattern=get_question_pattern("owner_tradeoff_system_design"),
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=("match_gap_001",),
        recent_question_texts=[],
        source_availability="available",
        confidence_level="high",
        question_metadata={"primary_question_evidence": primary_question_evidence},
    )

    assert result.allow_emit is False
    assert "primary_evidence_grounding_violation" in result.blocking_issues


def test_primary_evidence_grounding_accepts_candidate_project_experience() -> None:
    strategy = resolve_polish_theme_strategy("technical")
    scenario = SimpleNamespace(
        business_constraint="物料库存处理工作流需要在并发扣减下保持最终一致",
        failure_mode="锁等待、事务消息投递失败或重复消费",
        scale_or_performance_constraint="并发冲突率从23%降至2%",
        consistency_constraint="库存扣减、事务消息和对账补偿需要状态收敛",
        cost_constraint="锁粒度和消息重试成本需要权衡",
        observability_constraint="并发冲突率、消息触达率和对账差异",
        system_components=("物料库存", "Redisson", "RocketMQ", "对账"),
        technical_entities=("Redisson", "RocketMQ", "分布式锁", "事务消息"),
        metrics=("23%", "2%", "100%"),
        confidence_level="high",
        low_confidence_flags=(),
        evidence_refs=("resume_project_001",),
    )
    primary_question_evidence = {
        "ref": "resume_project_001",
        "source_type": "resume_project",
        "title": "物料库存处理工作流",
        "summary": "物料库存处理工作流：Redisson 分布式锁 + RocketMQ 事务消息，并发冲突率从23%降至2%",
        "claim_mode": "candidate_experience",
        "allowed_source_refs": ["resume_project_001"],
        "confidence_level": "high",
    }

    result = validate_question_quality(
        question_text=(
            "围绕物料库存处理工作流，业务约束是并发扣减下保持最终一致。"
            "请从 Owner 视角说明 Redisson 分布式锁与 RocketMQ 事务消息最终一致性的实现、失败路径、"
            "重复消费、补偿和对账，并覆盖性能或成本约束、验证指标和核心 trade-off。"
        ),
        selected_pattern=get_question_pattern("owner_tradeoff_system_design"),
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=("resume_project_001",),
        recent_question_texts=[],
        source_availability="available",
        confidence_level="high",
        question_metadata={"primary_question_evidence": primary_question_evidence},
    )

    assert "primary_evidence_grounding_violation" not in result.blocking_issues


def test_primary_evidence_grounding_accepts_job_gap_probe_without_candidate_claim() -> None:
    strategy = resolve_polish_theme_strategy("technical")
    scenario = SimpleNamespace(
        business_constraint="JD 要求分布式系统开发经验，但简历缺少明确证据",
        failure_mode="缺少真实案例会影响能力判断",
        scale_or_performance_constraint="需要给出验证指标和补齐计划",
        consistency_constraint="需要说明可迁移经验和验证思路",
        cost_constraint="补齐计划需要控制学习和实践成本",
        observability_constraint="用项目指标或压测结果验证",
        system_components=("分布式系统",),
        technical_entities=("分布式系统",),
        metrics=("验证指标",),
        confidence_level="medium",
        low_confidence_flags=(),
        evidence_refs=("match_gap_001",),
    )
    primary_question_evidence = {
        "ref": "match_gap_001",
        "source_type": "match_gap",
        "title": "分布式系统开发经验缺口",
        "summary": "JD 要求分布式系统开发经验，但简历缺少明确证据",
        "claim_mode": "job_gap_probe",
        "allowed_source_refs": ["match_gap_001"],
        "confidence_level": "medium",
    }

    result = validate_question_quality(
        question_text=(
            "围绕 JD 要求的分布式系统开发经验，业务约束是简历缺少明确证据。"
            "请从 Owner 视角说明你如何理解该能力要求、有哪些可迁移经验、如何验证失败路径下的性能或成本约束、"
            "验证指标和核心 trade-off，以及后续如何补齐。"
        ),
        selected_pattern=get_question_pattern("owner_tradeoff_system_design"),
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=("match_gap_001",),
        recent_question_texts=[],
        source_availability="available",
        confidence_level="medium",
        question_metadata={"primary_question_evidence": primary_question_evidence},
    )

    assert "primary_evidence_grounding_violation" not in result.blocking_issues


def test_insufficient_primary_evidence_fallback_asks_for_project_chain_details() -> None:
    text = fallback_question_text(
        focus="系统设计能力",
        selected_pattern=get_question_pattern("owner_tradeoff_system_design"),
        citations="[1]",
    )

    assert text == INSUFFICIENT_PRIMARY_EVIDENCE_FALLBACK
    assert "业务入口" in text
    assert "职责边界" in text
    assert "失败案例" in text
    assert "验证指标" in text
    for fabricated_context in ("库存", "日志", "RAG", "向量化", "秒杀"):
        assert fabricated_context not in text


def test_quality_validator_blocks_missing_pattern_required_elements() -> None:
    strategy = resolve_polish_theme_strategy("technical")
    scenario = build_scenario_constraints(
        progress_node_title="支付链路一致性",
        expected_capability="能说明接口幂等、失败补偿和成本取舍。",
        related_job_requirements=[],
        related_resume_evidence=[],
        missing_points=[],
        selected_evidence_chunks=[],
        history_feedback=[],
        custom_topic_text=None,
        polish_theme=strategy.theme,
    )

    result = validate_question_quality(
        question_text=(
            "围绕「支付链路一致性」，业务约束是支付链路需要稳定状态。"
            "请从 Owner 视角说明一个失败路径下的性能或成本约束和核心 trade-off。"
        ),
        selected_pattern=get_question_pattern("owner_tradeoff_system_design"),
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=[],
        recent_question_texts=[],
        source_availability="unavailable",
        confidence_level=scenario.confidence_level,
    )

    assert result.allow_emit is False
    assert "missing_pattern_required_elements" in result.blocking_issues


def test_quality_validator_blocks_missing_business_constraint_marker() -> None:
    strategy = resolve_polish_theme_strategy("technical")
    scenario = build_scenario_constraints(
        progress_node_title="双层库存状态机与对账机制",
        expected_capability="能说明状态机和对账收敛。",
        related_job_requirements=[],
        related_resume_evidence=[],
        missing_points=[],
        selected_evidence_chunks=[],
        history_feedback=[],
        custom_topic_text=None,
        polish_theme=strategy.theme,
    )

    result = validate_question_quality(
        question_text=(
            "围绕「双层库存状态机与对账机制」，请从 Owner 视角说明核心状态、状态流转、"
            "防重复扣减、防重复回补、对账口径和收敛判断，并覆盖失败路径和核心 trade-off。"
        ),
        selected_pattern=get_question_pattern("state_machine_and_reconciliation"),
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=[],
        recent_question_texts=[],
        source_availability="unavailable",
        confidence_level=scenario.confidence_level,
    )

    assert result.allow_emit is False
    assert "missing_business_constraint" in result.blocking_issues


def test_quality_validator_accepts_required_elements_and_business_marker_contract() -> None:
    strategy = resolve_polish_theme_strategy("technical")
    scenario = build_scenario_constraints(
        progress_node_title="支付链路一致性",
        expected_capability="能说明接口幂等、失败补偿和成本取舍。",
        related_job_requirements=[],
        related_resume_evidence=[],
        missing_points=[],
        selected_evidence_chunks=[],
        history_feedback=[],
        custom_topic_text=None,
        polish_theme=strategy.theme,
    )

    result = validate_question_quality(
        question_text=(
            "围绕「支付链路一致性」，业务约束是支付链路需要稳定状态。"
            "请从 Owner 视角说明一个失败路径下的性能或成本约束、验证指标和核心 trade-off。"
        ),
        selected_pattern=get_question_pattern("owner_tradeoff_system_design"),
        theme_strategy=strategy,
        scenario_constraint=scenario,
        evidence_refs=[],
        recent_question_texts=[],
        source_availability="unavailable",
        confidence_level=scenario.confidence_level,
    )

    assert "missing_pattern_required_elements" not in result.blocking_issues
    assert "missing_business_constraint" not in result.blocking_issues


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


def test_question_metadata_normalizes_legacy_unknown_and_malformed_payloads() -> None:
    empty = empty_question_metadata().to_dict()

    assert normalize_question_metadata(None) == empty
    assert normalize_question_metadata({}) == empty
    assert normalize_question_metadata(["not", "a", "dict"]) == empty
    assert normalize_question_metadata("{not valid json") == empty

    legacy_json = json.dumps(
        {
            "question_pattern": "mixed_technical_expression",
            "quality_score": 87,
            "confidence_level": "medium",
            "low_confidence_flags": ["weak_metric_evidence", "weak_metric_evidence"],
            "expected_answer_dimensions": ["技术深度", "表达结构"],
            "quality_warnings": ["metrics_not_specific"],
            "unknown_field": "must be dropped",
        }
    )
    normalized = normalize_question_metadata(legacy_json)

    assert normalized["schema_id"]
    assert normalized["schema_version"]
    assert normalized["question_pattern"] == "mixed_technical_expression"
    assert normalized["quality_score"] == 87
    assert normalized["confidence_level"] == "medium"
    assert normalized["low_confidence_flags"] == ["weak_metric_evidence"]
    assert normalized["expected_answer_dimensions"] == ["技术深度", "表达结构"]
    assert normalized["quality_warnings"] == ["metrics_not_specific"]
    assert normalized["generated_at"] is None
    assert "unknown_field" not in normalized
    assert question_metadata_to_dict(normalized) == normalized


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
    turns: list[dict] | None = None,
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
        "turns": turns or [],
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
