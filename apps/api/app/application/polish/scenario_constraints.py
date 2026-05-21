"""Evidence-aware scenario constraints for deterministic polish questions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.application.polish.evidence_signals import EvidenceSignalSet


@dataclass(frozen=True)
class ScenarioConstraint:
    business_constraint: str
    failure_mode: str
    scale_or_performance_constraint: str
    consistency_constraint: str
    cost_constraint: str
    observability_constraint: str
    ownership_constraint: str
    system_components: tuple[str, ...]
    technical_entities: tuple[str, ...]
    metrics: tuple[str, ...]
    confidence_level: str
    low_confidence_flags: tuple[str, ...]
    evidence_refs: tuple[str, ...]


def build_scenario_constraints(
    *,
    progress_node_title: str,
    expected_capability: str | None,
    related_job_requirements: list[str],
    related_resume_evidence: list[str],
    missing_points: list[str],
    selected_evidence_chunks: list[Any],
    history_feedback: list[str],
    custom_topic_text: str | None,
    polish_theme: str,
    evidence_signals: EvidenceSignalSet | None = None,
) -> ScenarioConstraint:
    if evidence_signals is not None:
        return _constraints_from_signals(evidence_signals, polish_theme=polish_theme)

    evidence_refs = tuple(
        str(chunk.chunk_id)
        for chunk in selected_evidence_chunks
        if getattr(chunk, "chunk_id", None)
    )
    evidence_text = _join_text(
        progress_node_title,
        expected_capability,
        related_job_requirements,
        related_resume_evidence,
        missing_points,
        history_feedback,
        custom_topic_text,
        [getattr(chunk, "title", "") for chunk in selected_evidence_chunks],
        [getattr(chunk, "text", "") for chunk in selected_evidence_chunks],
    )
    entities = _detected_entities(evidence_text)
    lower = evidence_text.lower()
    has_evidence = bool(evidence_refs or related_job_requirements or related_resume_evidence)

    if _contains_any(lower, ("minio", "mq", "部分成功", "部分失败")):
        return _partial_success_constraints(entities, evidence_refs, has_evidence)
    if _contains_any(lower, ("1gb", "日志", "异步处理")) and _contains_any(lower, ("向量化", "入库", "切块")):
        return _large_log_pipeline_constraints(entities, evidence_refs, has_evidence)
    if _contains_any(lower, ("分布式锁", "事务消息", "半事务消息", "最终一致")):
        return _distributed_lock_constraints(entities, evidence_refs, has_evidence)
    if _contains_any(lower, ("仓库维度", "并发扣减", "总库存")):
        return _warehouse_deduction_constraints(entities, evidence_refs, has_evidence)
    if _contains_any(lower, ("双层库存", "状态机", "对账")):
        return _inventory_state_machine_constraints(entities, evidence_refs, has_evidence)
    if _contains_any(lower, ("agent", "工具调用", "rag", "记忆")):
        return _agent_constraints(entities, evidence_refs, has_evidence)
    return _abstract_constraints(entities, evidence_refs, has_evidence, polish_theme=polish_theme)


def _constraints_from_signals(
    evidence_signals: EvidenceSignalSet,
    *,
    polish_theme: str,
) -> ScenarioConstraint:
    entities = _signal_entities(evidence_signals)
    evidence_refs = evidence_signals.evidence_refs
    has_evidence = evidence_signals.source_availability == "available"
    failures = set(evidence_signals.failure_signals)
    technical = set(evidence_signals.technical_components)
    external = set(evidence_signals.external_services)
    queues = set(evidence_signals.message_queues)
    data_stores = set(evidence_signals.data_stores)
    consistency = set(evidence_signals.consistency_signals)
    states = set(evidence_signals.state_machine_signals)
    reconciliation = set(evidence_signals.reconciliation_signals)
    domains = set(evidence_signals.business_domains)
    scale = set(evidence_signals.scale_indicators)
    performance = set(evidence_signals.performance_indicators)
    cost = set(evidence_signals.cost_signals)

    if (
        {"Agent", "工具调用"}.issubset(technical)
        and ({"RAG", "记忆"} & technical)
        and ({"上下文污染", "工具调用失败"} & failures or {"回滚"} & reconciliation or cost)
    ):
        return _agent_constraints(entities, evidence_refs, has_evidence, signal_flags=evidence_signals.low_confidence_flags)
    if ({"部分成功", "部分失败"} & failures) and {"MinIO"} & external and queues and "向量化" in technical and data_stores:
        return _partial_success_constraints(entities, evidence_refs, has_evidence, signal_flags=evidence_signals.low_confidence_flags)
    if _has_signal_metric(evidence_signals, "scale") and (
        _has_signal_metric(evidence_signals, "latency_improvement") or "异步处理" in performance
    ):
        return _large_log_pipeline_constraints(entities, evidence_refs, has_evidence, signal_flags=evidence_signals.low_confidence_flags)
    if "分布式锁" in consistency and ({"事务消息", "半事务消息", "最终一致"} & consistency):
        return _distributed_lock_constraints(entities, evidence_refs, has_evidence, signal_flags=evidence_signals.low_confidence_flags)
    if "库存" in domains and ({"并发", "消息堆积"} & scale or {"吞吐", "耗时"} & performance):
        return _warehouse_deduction_constraints(entities, evidence_refs, has_evidence, signal_flags=evidence_signals.low_confidence_flags)
    if states and ({"对账", "回补"} & reconciliation):
        return _inventory_state_machine_constraints(entities, evidence_refs, has_evidence, signal_flags=evidence_signals.low_confidence_flags)
    return _abstract_constraints(
        entities,
        evidence_refs,
        has_evidence,
        polish_theme=polish_theme,
        signal_flags=evidence_signals.low_confidence_flags,
        confidence_level=evidence_signals.confidence_level,
    )


def _signal_entities(evidence_signals: EvidenceSignalSet) -> tuple[str, ...]:
    return _dedupe_strings(
        [
            *evidence_signals.all_components(),
            *evidence_signals.failure_signals,
            *evidence_signals.consistency_signals,
            *evidence_signals.state_machine_signals,
            *evidence_signals.idempotency_signals,
            *evidence_signals.reconciliation_signals,
            *evidence_signals.cost_signals,
            *evidence_signals.observability_signals,
            *evidence_signals.performance_indicators,
            *evidence_signals.scale_indicators,
        ]
    )


def _has_signal_metric(evidence_signals: EvidenceSignalSet, metric_type: str) -> bool:
    return any(metric.metric_type == metric_type for metric in evidence_signals.metrics)


def _merge_flags(base: tuple[str, ...], extra: tuple[str, ...] = ()) -> tuple[str, ...]:
    return tuple(dict.fromkeys([*base, *extra]))


def _dedupe_strings(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return tuple(result)


def _partial_success_constraints(
    entities: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    has_evidence: bool,
    signal_flags: tuple[str, ...] = (),
) -> ScenarioConstraint:
    storage_text = " / ".join(_ordered_supported(entities, ("MySQL", "Redis", "Elasticsearch", "ES"))) or "下游存储"
    return ScenarioConstraint(
        business_constraint="业务约束：文件上传、消息触发、向量化和多存储写入必须给用户一个一致的处理结果。",
        failure_mode=f"向量化超时、消息堆积或 {storage_text} 只有部分写入成功，形成部分成功 / 部分失败。",
        scale_or_performance_constraint="高峰期需要控制线程池、消费并行度和消息堆积，避免拖垮在线请求。",
        consistency_constraint="用状态机、幂等键、断点续跑和重试收敛把多组件状态拉回一致。",
        cost_constraint="设置成本上限，避免高峰期无限重试和向量化资源失控。",
        observability_constraint="按对象、消息、向量化任务和存储写入记录 trace，暴露堆积、超时、重试和失败率。",
        ownership_constraint="要求候选人从 owner 视角说明边界、降级和最终收敛口径。",
        system_components=_ordered_supported(entities, ("MinIO", "MQ", "向量化", "向量化服务", "MySQL", "Redis", "Elasticsearch", "ES")),
        technical_entities=_ordered_supported(entities, ("状态机", "幂等", "断点续跑", "线程池", "消息堆积", "重试收敛")),
        metrics=("向量化超时率", "消息堆积长度", "重试收敛时长", "成本上限"),
        confidence_level="high" if has_evidence else "low",
        low_confidence_flags=_merge_flags(() if has_evidence else ("source_unavailable",), signal_flags),
        evidence_refs=evidence_refs,
    )


def _large_log_pipeline_constraints(
    entities: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    has_evidence: bool,
    signal_flags: tuple[str, ...] = (),
) -> ScenarioConstraint:
    return ScenarioConstraint(
        business_constraint="业务约束：1GB 日志从上传入口进入异步处理管道，用户需要看到可追踪的处理进度。",
        failure_mode="解析、切块、向量化或入库任一步失败时，需要失败重试和可恢复进度。",
        scale_or_performance_constraint="将端到端处理从 15 秒优化到 3 秒，同时用削峰填谷、并行度控制和资源隔离保护主链路。",
        consistency_constraint="切块、向量化和入库结果需要按任务状态收敛，避免重复写入或漏处理。",
        cost_constraint="控制向量化批量、并行度和重试次数，说明成本权衡。",
        observability_constraint="按上传入口、解析、切块、向量化、入库暴露耗时、失败重试和队列水位。",
        ownership_constraint="要求候选人从 owner 视角解释性能收益、资源边界和降级策略。",
        system_components=_ordered_supported(entities, ("上传入口", "解析服务", "切块服务", "向量化服务", "入库服务")),
        technical_entities=_ordered_supported(entities, ("异步处理", "削峰填谷", "并行度控制", "资源隔离", "失败重试")),
        metrics=("1GB 日志", "15 秒到 3 秒", "队列水位", "资源成本"),
        confidence_level="high" if has_evidence else "low",
        low_confidence_flags=_merge_flags(() if has_evidence else ("source_unavailable",), signal_flags),
        evidence_refs=evidence_refs,
    )


def _distributed_lock_constraints(
    entities: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    has_evidence: bool,
    signal_flags: tuple[str, ...] = (),
) -> ScenarioConstraint:
    return ScenarioConstraint(
        business_constraint="业务约束：库存扣减请求链路需要在并发下保持最终一致，并且不能让锁和消息边界互相掩盖失败。",
        failure_mode="锁获取、锁释放、本地事务提交、半事务消息发送或消费任一步都可能失败。",
        scale_or_performance_constraint="并发请求下要控制锁粒度和等待时间，避免吞吐被串行化。",
        consistency_constraint="明确本地事务、半事务消息、消费幂等、失败兜底和最终一致收敛口径。",
        cost_constraint="对比本地消息表、纯补偿方案和事务消息的实现复杂度与运维成本。",
        observability_constraint="按请求、锁、事务、消息和消费结果记录链路 trace 和补偿结果。",
        ownership_constraint="要求候选人从 owner 视角解释锁放在哪一层以及替代方案 trade-off。",
        system_components=_ordered_supported(entities, ("请求入口", "分布式锁", "本地事务", "半事务消息", "库存服务")),
        technical_entities=_ordered_supported(entities, ("分布式锁", "本地事务", "半事务消息", "最终一致", "幂等")),
        metrics=("锁等待时间", "消息确认延迟", "失败兜底成功率"),
        confidence_level="high" if has_evidence else "low",
        low_confidence_flags=_merge_flags(() if has_evidence else ("source_unavailable",), signal_flags),
        evidence_refs=evidence_refs,
    )


def _warehouse_deduction_constraints(
    entities: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    has_evidence: bool,
    signal_flags: tuple[str, ...] = (),
) -> ScenarioConstraint:
    return ScenarioConstraint(
        business_constraint="新业务约束：物料库存从全局扣减扩展为仓库维度并发扣减。",
        failure_mode="单仓扣减成功但总库存未同步、跨仓并发竞争或回滚失败会带来超卖风险。",
        scale_or_performance_constraint="需要通过仓库维度拆分热点来获得吞吐提升。",
        consistency_constraint="总库存一致必须有明确口径，同时控制对账复杂度。",
        cost_constraint="比较拆分锁、分桶库存和异步对账带来的实现与运维成本。",
        observability_constraint="按仓库、物料、扣减请求和总库存差异暴露指标。",
        ownership_constraint="要求候选人从 owner 视角解释新旧约束、并发模型和上线验证。",
        system_components=_ordered_supported(entities, ("仓库维度", "物料库存", "扣减服务", "对账任务")),
        technical_entities=_ordered_supported(entities, ("并发扣减", "总库存一致", "超卖风险", "对账复杂度")),
        metrics=("吞吐提升", "总库存差异", "超卖风险", "对账复杂度"),
        confidence_level="high" if has_evidence else "low",
        low_confidence_flags=_merge_flags(() if has_evidence else ("source_unavailable",), signal_flags),
        evidence_refs=evidence_refs,
    )


def _inventory_state_machine_constraints(
    entities: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    has_evidence: bool,
    signal_flags: tuple[str, ...] = (),
) -> ScenarioConstraint:
    return ScenarioConstraint(
        business_constraint="业务约束：双层库存需要通过状态机表达预占、扣减、回补和完成等核心状态。",
        failure_mode="重复消息、超时回调或人工修正可能造成重复扣减和重复回补。",
        scale_or_performance_constraint="状态流转要支持并发请求和批量对账，不把主链路完全串行化。",
        consistency_constraint="定义核心状态、状态流转、防重复扣减、防重复回补、对账口径和收敛判断。",
        cost_constraint="控制状态数量、对账频率和人工介入成本。",
        observability_constraint="按状态、流转事件、对账差异和收敛结果暴露监控。",
        ownership_constraint="要求候选人从 owner 视角解释系统什么时候算真正收敛。",
        system_components=_ordered_supported(entities, ("双层库存", "状态机", "对账任务", "扣减服务", "回补服务")),
        technical_entities=_ordered_supported(entities, ("核心状态", "状态流转", "防重复扣减", "防重复回补", "对账口径", "收敛判断")),
        metrics=("状态滞留时长", "对账差异", "重复扣减次数", "重复回补次数"),
        confidence_level="high" if has_evidence else "low",
        low_confidence_flags=_merge_flags(() if has_evidence else ("source_unavailable",), signal_flags),
        evidence_refs=evidence_refs,
    )


def _agent_constraints(
    entities: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    has_evidence: bool,
    signal_flags: tuple[str, ...] = (),
) -> ScenarioConstraint:
    return ScenarioConstraint(
        business_constraint="业务约束：Agent 需要在任务规划、工具调用和上下文记忆之间保持可解释、可回滚的执行链路。",
        failure_mode="工具调用失败、计划回滚不完整、上下文污染或 RAG 召回错误会让结果不可控。",
        scale_or_performance_constraint="需要限制工具调用轮次、上下文长度和重试次数。",
        consistency_constraint="用计划状态、工具调用结果、幂等执行和回滚策略收敛。",
        cost_constraint="按 token、工具调用和重试次数设置成本控制。",
        observability_constraint="记录计划、工具调用、记忆写入和回滚事件的 trace。",
        ownership_constraint="要求候选人从 owner 视角说明技术深度与表达结构。",
        system_components=_ordered_supported(entities, ("Agent", "工具调用", "RAG", "记忆", "计划器")),
        technical_entities=_ordered_supported(entities, ("工具调用失败", "计划回滚", "上下文污染", "成本控制")),
        metrics=("工具调用成功率", "回滚成功率", "token 成本", "重试次数"),
        confidence_level="high" if has_evidence else "medium",
        low_confidence_flags=_merge_flags(() if has_evidence else ("evidence_partial",), signal_flags),
        evidence_refs=evidence_refs,
    )


def _abstract_constraints(
    entities: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    has_evidence: bool,
    *,
    polish_theme: str,
    signal_flags: tuple[str, ...] = (),
    confidence_level: str | None = None,
) -> ScenarioConstraint:
    flags = () if has_evidence else ("evidence_insufficient", "need_project_chain_metrics_failure_case")
    resolved_confidence = confidence_level if confidence_level is not None else ("medium" if has_evidence else "low")
    return ScenarioConstraint(
        business_constraint="业务约束：当前材料较抽象，需要先限定业务入口、上下游依赖和用户可见结果。",
        failure_mode="失败路径：上游输入缺失、处理超时、结果不一致或降级策略不清会导致方案无法落地。",
        scale_or_performance_constraint="性能或成本约束：需要给出吞吐、时延、资源成本或调用次数中的至少一个验证指标。",
        consistency_constraint="如果涉及多步骤处理，需要说明状态收敛、幂等或补偿口径。",
        cost_constraint="成本约束较弱时，需要补充关键资源消耗或调用成本上限。",
        observability_constraint="验证指标：至少说明成功率、耗时、错误率、成本或人工复核量。",
        ownership_constraint="低置信度：请补充项目链路、关键指标、失败案例和系统组件后再做更具体追问。",
        system_components=("业务入口", "处理服务", "结果存储", "监控告警") if polish_theme != "communication" else (),
        technical_entities=entities,
        metrics=("验证指标", "性能或成本约束"),
        confidence_level=resolved_confidence,
        low_confidence_flags=_merge_flags(flags, signal_flags),
        evidence_refs=evidence_refs,
    )


def _detected_entities(text: str) -> tuple[str, ...]:
    candidates = (
        ("MinIO", r"\bminio\b"),
        ("MQ", r"\bmq\b|消息队列"),
        ("MySQL", r"\bmysql\b"),
        ("Redis", r"\bredis\b"),
        ("ES", r"\bes\b|elasticsearch"),
        ("向量化服务", r"向量化"),
        ("状态机", r"状态机"),
        ("幂等", r"幂等"),
        ("断点续跑", r"断点续跑"),
        ("线程池", r"线程池"),
        ("消息堆积", r"消息堆积"),
        ("重试收敛", r"重试收敛|重试"),
        ("上传入口", r"上传入口|上传"),
        ("解析服务", r"解析"),
        ("切块服务", r"切块"),
        ("入库服务", r"入库"),
        ("异步处理", r"异步处理"),
        ("削峰填谷", r"削峰填谷"),
        ("并行度控制", r"并行度"),
        ("资源隔离", r"资源隔离"),
        ("失败重试", r"失败重试|重试"),
        ("分布式锁", r"分布式锁"),
        ("本地事务", r"本地事务"),
        ("半事务消息", r"半事务消息|事务消息"),
        ("最终一致", r"最终一致"),
        ("请求入口", r"请求链路|请求入口"),
        ("库存服务", r"库存"),
        ("仓库维度", r"仓库维度"),
        ("物料库存", r"物料|库存"),
        ("扣减服务", r"扣减"),
        ("并发扣减", r"并发扣减"),
        ("总库存一致", r"总库存一致"),
        ("超卖风险", r"超卖"),
        ("对账复杂度", r"对账复杂度"),
        ("双层库存", r"双层库存"),
        ("对账任务", r"对账"),
        ("回补服务", r"回补"),
        ("核心状态", r"核心状态"),
        ("状态流转", r"状态流转"),
        ("防重复扣减", r"防重复扣减|重复扣减"),
        ("防重复回补", r"防重复回补|重复回补"),
        ("对账口径", r"对账口径"),
        ("收敛判断", r"收敛判断|收敛"),
        ("Agent", r"\bagent\b"),
        ("工具调用", r"工具调用"),
        ("RAG", r"\brag\b"),
        ("记忆", r"记忆"),
        ("计划器", r"任务规划|计划"),
        ("工具调用失败", r"工具调用失败"),
        ("计划回滚", r"计划回滚|回滚"),
        ("上下文污染", r"上下文污染"),
        ("成本控制", r"成本控制"),
    )
    lower = text.lower()
    result: list[str] = []
    for label, pattern in candidates:
        if re.search(pattern, lower, flags=re.IGNORECASE) and label not in result:
            result.append(label)
    return tuple(result)


def _ordered_supported(entities: tuple[str, ...], labels: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(label for label in labels if label in entities)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term.lower() in text for term in terms)


def _join_text(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        if isinstance(value, (list, tuple)):
            parts.append(_join_text(*value))
            continue
        if value is None:
            continue
        text = " ".join(str(value).split())
        if text:
            parts.append(text)
    return " ".join(parts)
