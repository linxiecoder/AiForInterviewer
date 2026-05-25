"""Deterministic question pattern library for polish question generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QuestionPattern:
    pattern_id: str
    title: str
    applicable_themes: tuple[str, ...]
    required_signals: tuple[str, ...]
    required_question_elements: tuple[str, ...]
    forbidden_question_elements: tuple[str, ...]
    expected_answer_dimensions: tuple[str, ...]
    interview_intent: str
    quality_rules: tuple[str, ...]
    golden_case_ids: tuple[str, ...]


_LEGACY_TEMPLATE_ELEMENTS = (
    "请选一个你实际参与的具体场景",
    "讲清楚当时要解决的问题",
    "你负责的技术改造或决策",
    "为什么这样取舍",
    "上线后如何验证效果",
)


QUESTION_PATTERN_LIST: tuple[QuestionPattern, ...] = (
    QuestionPattern(
        pattern_id="real_request_trace_deep_dive",
        title="真实请求链路深挖",
        applicable_themes=("technical", "mixed"),
        required_signals=("分布式锁", "事务消息", "最终一致", "库存", "请求链路"),
        required_question_elements=("完整请求链路", "锁在哪一层", "本地事务", "半事务消息", "失败兜底", "trade-off"),
        forbidden_question_elements=_LEGACY_TEMPLATE_ELEMENTS,
        expected_answer_dimensions=("链路边界", "锁粒度", "事务边界", "消息确认", "失败兜底", "替代方案取舍"),
        interview_intent="验证候选人能否把一致性方案落到真实请求链路和异常分支。",
        quality_rules=("必须出现链路顺序", "必须追问失败兜底", "必须要求替代方案 trade-off"),
        golden_case_ids=("distributed_lock_transaction_message",),
    ),
    QuestionPattern(
        pattern_id="constraint_change_refactor",
        title="约束变化下的重构取舍",
        applicable_themes=("technical", "mixed"),
        required_signals=("仓库维度", "并发扣减", "吞吐", "总库存一致", "物料"),
        required_question_elements=("新业务约束", "仓库维度", "吞吐提升", "总库存一致", "超卖风险", "对账复杂度"),
        forbidden_question_elements=_LEGACY_TEMPLATE_ELEMENTS,
        expected_answer_dimensions=("旧约束", "新约束", "并发模型", "一致性口径", "对账成本", "上线验证"),
        interview_intent="观察候选人是否能把业务约束变化转成并发和一致性设计。",
        quality_rules=("必须说明约束变化", "必须出现一致性风险", "必须控制对账复杂度"),
        golden_case_ids=("warehouse_concurrent_deduction",),
    ),
    QuestionPattern(
        pattern_id="state_machine_and_reconciliation",
        title="状态机与对账收敛",
        applicable_themes=("technical", "mixed"),
        required_signals=("状态机", "对账", "扣减", "回补", "库存"),
        required_question_elements=("核心状态", "状态流转", "防重复扣减", "防重复回补", "对账口径", "收敛判断"),
        forbidden_question_elements=_LEGACY_TEMPLATE_ELEMENTS,
        expected_answer_dimensions=("状态定义", "合法流转", "幂等键", "对账口径", "补偿策略", "收敛判定"),
        interview_intent="验证候选人是否能用状态机和对账机制解释系统最终收敛。",
        quality_rules=("必须要求状态列表", "必须追问重复扣减/回补", "必须给出收敛判断"),
        golden_case_ids=("two_layer_inventory_state_machine",),
    ),
    QuestionPattern(
        pattern_id="partial_success_failure_recovery",
        title="部分成功与失败恢复",
        applicable_themes=("technical", "mixed"),
        required_signals=("MinIO", "MQ", "向量化", "部分成功", "MySQL", "Redis", "ES"),
        required_question_elements=("部分成功", "部分失败", "状态机", "重试收敛", "断点续跑", "幂等", "成本上限"),
        forbidden_question_elements=_LEGACY_TEMPLATE_ELEMENTS,
        expected_answer_dimensions=("组件边界", "状态机", "幂等与断点", "重试策略", "堆积治理", "成本上限"),
        interview_intent="验证候选人能否处理多组件链路中的部分成功和恢复收敛。",
        quality_rules=("必须出现部分成功/失败", "必须要求断点续跑", "必须追问成本上限"),
        golden_case_ids=("minio_mq_vector_partial_success",),
    ),
    QuestionPattern(
        pattern_id="agent_tool_failure_context_contamination",
        title="Agent 工具调用失败与上下文污染",
        applicable_themes=("technical", "mixed"),
        required_signals=("Agent", "工具调用", "RAG", "记忆", "上下文污染", "回滚", "成本"),
        required_question_elements=("Agent", "工具调用", "RAG", "记忆", "上下文污染", "回滚", "成本"),
        forbidden_question_elements=_LEGACY_TEMPLATE_ELEMENTS,
        expected_answer_dimensions=("任务边界", "工具调用链路", "上下文隔离", "回滚策略", "成本控制", "可观测性"),
        interview_intent="验证候选人能否把 Agent 执行链路中的工具失败、记忆污染和回滚成本讲清楚。",
        quality_rules=("必须说明工具调用失败", "必须追问上下文污染", "必须包含回滚和成本控制"),
        golden_case_ids=("agent_tool_context_contamination",),
    ),
    QuestionPattern(
        pattern_id="owner_tradeoff_system_design",
        title="Owner 视角系统设计取舍",
        applicable_themes=("technical", "mixed"),
        required_signals=("业务约束", "失败路径", "性能", "成本", "可观测性"),
        required_question_elements=("业务约束", "失败路径", "性能或成本约束", "验证指标", "trade-off"),
        forbidden_question_elements=_LEGACY_TEMPLATE_ELEMENTS,
        expected_answer_dimensions=("业务边界", "核心链路", "失败路径", "资源约束", "验证指标", "后续补材料"),
        interview_intent="在证据不足或主题抽象时，仍保持有压力的工程系统设计追问。",
        quality_rules=("不得退回旧模板", "低置信时必须要求补材料", "不得编造具体组件"),
        golden_case_ids=("abstract_node_degraded",),
    ),
    QuestionPattern(
        pattern_id="performance_cost_observability",
        title="性能、成本与可观测性",
        applicable_themes=("technical", "mixed"),
        required_signals=("1GB", "日志", "异步处理", "向量化", "入库"),
        required_question_elements=("上传入口", "解析", "切块", "向量化", "入库", "并行度控制", "失败重试", "成本权衡"),
        forbidden_question_elements=_LEGACY_TEMPLATE_ELEMENTS,
        expected_answer_dimensions=("入口限流", "管道拆分", "并行度", "资源隔离", "重试策略", "成本与指标"),
        interview_intent="验证候选人是否能解释异步管道性能优化背后的资源和成本边界。",
        quality_rules=("必须出现管道步骤", "必须要求削峰填谷", "必须追问成本与观测"),
        golden_case_ids=("large_log_async_pipeline",),
    ),
    QuestionPattern(
        pattern_id="star_communication_refactor",
        title="STAR 表达重构",
        applicable_themes=("communication",),
        required_signals=("STAR", "背景压缩", "个人职责边界", "逻辑顺序", "复盘"),
        required_question_elements=("STAR", "背景压缩", "个人职责边界", "逻辑顺序", "复盘总结"),
        forbidden_question_elements=("半事务消息", "锁在哪一层", "线程池", "消息堆积"),
        expected_answer_dimensions=("Situation", "Task", "Action", "Result", "职责边界", "复盘口径"),
        interview_intent="训练候选人把已有项目材料转成清晰、可信、可复盘的面试表达。",
        quality_rules=("必须出现 STAR", "不得过度技术深挖", "必须要求职责边界和复盘"),
        golden_case_ids=("communication_theme",),
    ),
    QuestionPattern(
        pattern_id="mixed_technical_expression",
        title="技术深度与表达结构混合题",
        applicable_themes=("mixed",),
        required_signals=("显性技术", "隐性表达", "权重", "技术深度", "表达结构"),
        required_question_elements=("显性技术", "隐性表达", "权重比例", "技术深度", "表达结构"),
        forbidden_question_elements=_LEGACY_TEMPLATE_ELEMENTS,
        expected_answer_dimensions=("技术链路", "失败处理", "权重意识", "表达结构", "复盘收束"),
        interview_intent="同时评估技术判断和表达组织能力，并让候选人知道两类评分权重。",
        quality_rules=("必须明示权重", "必须兼顾技术深度和表达结构", "不得退化成单纯项目介绍"),
        golden_case_ids=("mixed_theme",),
    ),
)


QUESTION_PATTERNS: dict[str, QuestionPattern] = {
    pattern.pattern_id: pattern for pattern in QUESTION_PATTERN_LIST
}


def get_question_pattern(pattern_id: str) -> QuestionPattern:
    return QUESTION_PATTERNS[pattern_id]


def select_question_pattern(
    *,
    theme_strategy: Any,
    scenario_constraint: Any,
    progress_node_title: str,
    evidence_signals: Any | None = None,
) -> QuestionPattern:
    theme = getattr(theme_strategy, "theme", "mixed")
    if theme == "communication":
        return get_question_pattern("star_communication_refactor")

    if evidence_signals is not None:
        signal_pattern = _pattern_from_evidence_signals(evidence_signals)
        if signal_pattern is not None:
            return get_question_pattern(signal_pattern)
        if theme == "mixed":
            return get_question_pattern("mixed_technical_expression")
        return get_question_pattern("owner_tradeoff_system_design")

    signal_text = _joined_signals(scenario_constraint, progress_node_title)
    if _has_any(signal_text, ("minio", "mq", "部分成功", "部分失败")):
        return get_question_pattern("partial_success_failure_recovery")
    if _has_any(signal_text, ("1gb", "日志", "异步处理", "向量化", "入库")):
        return get_question_pattern("performance_cost_observability")
    if _has_any(signal_text, ("agent", "工具调用", "rag", "记忆", "上下文污染")):
        return get_question_pattern("agent_tool_failure_context_contamination")
    if _has_any(signal_text, ("分布式锁", "事务消息", "半事务消息", "最终一致")):
        return get_question_pattern("real_request_trace_deep_dive")
    if _has_any(signal_text, ("仓库维度", "并发扣减", "总库存")):
        return get_question_pattern("constraint_change_refactor")
    if _has_any(signal_text, ("双层库存", "状态机", "对账")):
        return get_question_pattern("state_machine_and_reconciliation")
    if theme == "mixed":
        return get_question_pattern("mixed_technical_expression")
    return get_question_pattern("owner_tradeoff_system_design")


def _pattern_from_evidence_signals(evidence_signals: Any) -> str | None:
    technical = set(getattr(evidence_signals, "technical_components", ()))
    components = set(getattr(evidence_signals, "all_components", lambda: ())())
    data_stores = set(getattr(evidence_signals, "data_stores", ()))
    queues = set(getattr(evidence_signals, "message_queues", ()))
    external = set(getattr(evidence_signals, "external_services", ()))
    failures = set(getattr(evidence_signals, "failure_signals", ()))
    consistency = set(getattr(evidence_signals, "consistency_signals", ()))
    states = set(getattr(evidence_signals, "state_machine_signals", ()))
    reconciliation = set(getattr(evidence_signals, "reconciliation_signals", ()))
    domains = set(getattr(evidence_signals, "business_domains", ()))
    scale = set(getattr(evidence_signals, "scale_indicators", ()))
    performance = set(getattr(evidence_signals, "performance_indicators", ()))
    cost = set(getattr(evidence_signals, "cost_signals", ()))
    metrics = tuple(getattr(evidence_signals, "metrics", ()))

    if (
        {"Agent", "工具调用"}.issubset(technical)
        and ({"RAG", "记忆"} & technical)
        and ({"上下文污染", "工具调用失败"} & failures or {"回滚"} & reconciliation or cost)
    ):
        return "agent_tool_failure_context_contamination"
    if ({"部分成功", "部分失败"} & failures) and {"MinIO"} & external and queues and "向量化" in technical and data_stores:
        return "partial_success_failure_recovery"
    if _has_size_metric(metrics) and (_has_latency_improvement(metrics) or "异步处理" in performance):
        return "performance_cost_observability"
    if "分布式锁" in consistency and ({"事务消息", "半事务消息", "最终一致"} & consistency):
        return "real_request_trace_deep_dive"
    if "仓库维度" in " ".join([*domains, *scale, *performance, *components]) or ({"并发", "吞吐"} & (scale | performance) and "库存" in domains):
        return "constraint_change_refactor"
    if states and ({"对账", "回补"} & reconciliation):
        return "state_machine_and_reconciliation"
    return None


def _has_size_metric(metrics: tuple[Any, ...]) -> bool:
    return any(getattr(metric, "metric_type", "") == "scale" for metric in metrics)


def _has_latency_improvement(metrics: tuple[Any, ...]) -> bool:
    return any(getattr(metric, "metric_type", "") == "latency_improvement" for metric in metrics)

def _joined_signals(scenario_constraint: Any, progress_node_title: str) -> str:
    parts: list[str] = [progress_node_title]
    for attr in (
        "business_constraint",
        "failure_mode",
        "scale_or_performance_constraint",
        "consistency_constraint",
        "cost_constraint",
        "observability_constraint",
    ):
        value = getattr(scenario_constraint, attr, None)
        if value:
            parts.append(str(value))
    for attr in ("system_components", "technical_entities", "metrics", "low_confidence_flags"):
        value = getattr(scenario_constraint, attr, ())
        if value:
            parts.extend(str(item) for item in value)
    return " ".join(parts).lower()


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term.lower() in text for term in terms)
