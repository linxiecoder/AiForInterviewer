from __future__ import annotations

from dataclasses import dataclass

from app.application.polish.evidence_signals import (
    extract_evidence_signals,
    extract_metric_signals,
    normalize_component_name,
)
from app.application.polish.question_patterns import select_question_pattern
from app.application.polish.scenario_constraints import build_scenario_constraints
from app.application.polish.theme_strategy import resolve_polish_theme_strategy


@dataclass(frozen=True)
class _Chunk:
    chunk_id: str
    source_type: str
    title: str
    text: str


def test_component_name_normalization() -> None:
    assert normalize_component_name("minio") == "MinIO"
    assert normalize_component_name("Minio") == "MinIO"
    assert normalize_component_name("MINIO") == "MinIO"
    assert normalize_component_name("redis") == "Redis"
    assert normalize_component_name("mysql") == "MySQL"
    assert normalize_component_name("postgres") == "PostgreSQL"
    assert normalize_component_name("postgresql") == "PostgreSQL"
    assert normalize_component_name("es") == "Elasticsearch"
    assert normalize_component_name("elasticsearch") == "Elasticsearch"
    assert normalize_component_name("mq") == "MQ"
    assert normalize_component_name("消息队列") == "MQ"
    assert normalize_component_name("rocketmq") == "RocketMQ"
    assert normalize_component_name("kafka") == "Kafka"
    assert normalize_component_name("rabbitmq") == "RabbitMQ"


def test_metric_signal_extraction_normalizes_sizes_latency_and_runtime_indicators() -> None:
    metrics = extract_metric_signals(
        "1GB 日志和 1024MB 附件需要把耗时从 15 秒到 3 秒，15s -> 3s；关注 QPS、RT、P95、P99、消息堆积。",
        evidence_ref="chunk_metric_001",
    )

    displays = {metric.display for metric in metrics}
    assert {"1GB", "1024MB", "15 秒到 3 秒", "15s -> 3s", "QPS", "RT", "P95", "P99", "消息堆积"}.issubset(displays)
    latency = next(metric for metric in metrics if metric.display == "15 秒到 3 秒")
    assert latency.before == 15
    assert latency.after == 3
    assert latency.unit in {"秒", "s"}
    assert latency.improvement_display == "5x"


def test_extracts_minio_mq_vector_storage_and_partial_success_signals() -> None:
    signals = extract_evidence_signals(
        progress_node={
            "progress_node_ref": "node_minio_vector",
            "title": "MinIO / MQ / 向量化部分成功不一致",
            "expected_capability": "能说明多组件链路的失败恢复。",
        },
        selected_evidence_chunks=[
            _Chunk(
                chunk_id="resume_project_001",
                source_type="resume_project",
                title="知识库导入",
                text="MinIO 上传后通过 MQ 触发向量化，MySQL / Redis / ES 出现部分成功，需要断点续跑。",
            )
        ],
        session_context={},
        theme="technical",
    )

    assert signals.source_availability == "available"
    assert signals.confidence_level in {"high", "medium"}
    assert ("MinIO", "MQ", "向量化") == (
        signals.external_services[0],
        signals.message_queues[0],
        signals.technical_components[0],
    )
    assert {"MySQL", "Redis", "Elasticsearch"}.issubset(set(signals.data_stores))
    assert "部分成功" in signals.failure_signals
    assert "断点续跑" in signals.reconciliation_signals
    assert "resume_project_001" in signals.evidence_refs


def test_extracts_inventory_consistency_state_machine_and_reconciliation_signals() -> None:
    signals = extract_evidence_signals(
        progress_node={"progress_node_ref": "node_inventory", "title": "双层库存状态机与对账"},
        selected_evidence_chunks=[
            _Chunk(
                chunk_id="job_requirement_001",
                source_type="job_requirement",
                title="库存一致性",
                text="分布式锁、事务消息和最终一致用于库存扣减；双层库存通过状态机、对账和回补收敛。",
            )
        ],
        session_context={},
        theme="technical",
    )

    assert "库存" in signals.business_domains
    assert "分布式锁" in signals.middleware_components
    assert "事务消息" in signals.consistency_signals
    assert "最终一致" in signals.consistency_signals
    assert "状态机" in signals.state_machine_signals
    assert "对账" in signals.reconciliation_signals
    assert "回补" in signals.reconciliation_signals


def test_extracts_agent_tool_rag_memory_context_pollution_rollback_and_cost_signals() -> None:
    signals = extract_evidence_signals(
        progress_node={"progress_node_ref": "node_agent", "title": "Agent 工具调用与上下文污染"},
        selected_evidence_chunks=[
            _Chunk(
                chunk_id="asset_summary_001",
                source_type="asset_summary",
                title="Agent 执行链路",
                text="Agent 使用工具调用和 RAG / 记忆，需要处理上下文污染、计划回滚和 token 成本。",
            )
        ],
        session_context={},
        theme="technical",
    )

    assert {"Agent", "工具调用", "RAG", "记忆"}.issubset(set(signals.technical_components))
    assert "上下文污染" in signals.failure_signals
    assert "回滚" in signals.reconciliation_signals
    assert "成本" in signals.cost_signals


def test_signal_aware_pattern_routing_prefers_evidence_signals() -> None:
    strategy = resolve_polish_theme_strategy("technical")

    def routed_pattern(title: str, text: str) -> str:
        signals = extract_evidence_signals(
            progress_node={"progress_node_ref": "node", "title": title},
            selected_evidence_chunks=[_Chunk("chunk_001", "resume_project", title, text)],
            session_context={},
            theme=strategy.theme,
        )
        scenario = build_scenario_constraints(
            progress_node_title=title,
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
        return select_question_pattern(
            theme_strategy=strategy,
            scenario_constraint=scenario,
            progress_node_title=title,
            evidence_signals=signals,
        ).pattern_id

    assert routed_pattern("库存一致性", "库存扣减使用分布式锁和事务消息保持最终一致。") == "real_request_trace_deep_dive"
    assert routed_pattern("仓库库存", "库存从全局改成仓库维度并发扣减，需要吞吐提升。") == "constraint_change_refactor"
    assert routed_pattern("双层库存", "双层库存通过状态机、对账和回补收敛。") == "state_machine_and_reconciliation"
    assert routed_pattern("向量化链路", "MinIO、MQ、向量化、MySQL、Redis、ES 存在部分成功。") == "partial_success_failure_recovery"
    assert routed_pattern("日志处理", "1GB 日志异步处理，切块入库，15 秒到 3 秒，关注成本和 P95。") == "performance_cost_observability"
    assert routed_pattern("Agent 链路", "Agent 工具调用结合 RAG 和记忆，需要处理上下文污染和回滚。") == "agent_tool_failure_context_contamination"
    assert routed_pattern("Agent 工具调用", "Agent 工具调用失败后需要处理上下文污染和成本。") == "owner_tradeoff_system_design"


def test_low_confidence_flags_when_evidence_is_missing_or_weak() -> None:
    missing = extract_evidence_signals(
        progress_node={"progress_node_ref": "node_missing", "title": "系统设计能力"},
        selected_evidence_chunks=[],
        session_context={},
        theme="technical",
    )
    assert missing.confidence_level == "low"
    assert "abstract_node_only" in missing.low_confidence_flags
    assert "weak_metric_evidence" in missing.low_confidence_flags
    assert "weak_failure_evidence" in missing.low_confidence_flags

    weak_metric = extract_evidence_signals(
        progress_node={"progress_node_ref": "node_weak_metric", "title": "性能优化"},
        selected_evidence_chunks=[_Chunk("chunk_weak", "resume_project", "性能优化", "做过性能优化和成本控制，但没有指标。")],
        session_context={},
        theme="technical",
    )
    assert "weak_metric_evidence" in weak_metric.low_confidence_flags
    assert {metric.metric_type for metric in weak_metric.metrics} == {"cost"}
