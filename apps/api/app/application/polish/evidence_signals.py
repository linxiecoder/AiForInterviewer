"""Deterministic evidence signal extraction for polish question building."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


SIGNAL_VERSION = "evidence-signals-v1"


@dataclass(frozen=True)
class EvidenceSignal:
    signal_type: str
    value: str
    evidence_ref: str
    source_type: str
    confidence_level: str = "high"

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "value": self.value,
            "evidence_ref": self.evidence_ref,
            "source_type": self.source_type,
            "confidence_level": self.confidence_level,
        }


@dataclass(frozen=True)
class MetricSignal:
    metric_type: str
    display: str
    evidence_ref: str
    source_type: str = "unknown"
    before: float | int | None = None
    after: float | int | None = None
    unit: str | None = None
    improvement_display: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_type": self.metric_type,
            "display": self.display,
            "evidence_ref": self.evidence_ref,
            "source_type": self.source_type,
            "before": self.before,
            "after": self.after,
            "unit": self.unit,
            "improvement_display": self.improvement_display,
        }


@dataclass(frozen=True)
class ComponentSignal:
    name: str
    category: str
    evidence_ref: str
    source_type: str = "unknown"
    confidence_level: str = "high"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "evidence_ref": self.evidence_ref,
            "source_type": self.source_type,
            "confidence_level": self.confidence_level,
        }


@dataclass(frozen=True)
class EvidenceSignalSet:
    project_entities: tuple[str, ...] = ()
    business_domains: tuple[str, ...] = ()
    technical_components: tuple[str, ...] = ()
    architecture_components: tuple[str, ...] = ()
    middleware_components: tuple[str, ...] = ()
    data_stores: tuple[str, ...] = ()
    message_queues: tuple[str, ...] = ()
    external_services: tuple[str, ...] = ()
    metrics: tuple[MetricSignal, ...] = ()
    scale_indicators: tuple[str, ...] = ()
    performance_indicators: tuple[str, ...] = ()
    failure_signals: tuple[str, ...] = ()
    consistency_signals: tuple[str, ...] = ()
    state_machine_signals: tuple[str, ...] = ()
    idempotency_signals: tuple[str, ...] = ()
    reconciliation_signals: tuple[str, ...] = ()
    cost_signals: tuple[str, ...] = ()
    observability_signals: tuple[str, ...] = ()
    ownership_signals: tuple[str, ...] = ()
    communication_signals: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    source_availability: str = "unavailable"
    confidence_level: str = "low"
    low_confidence_flags: tuple[str, ...] = ()
    component_signals: tuple[ComponentSignal, ...] = ()
    signals: tuple[EvidenceSignal, ...] = ()
    signal_version: str = SIGNAL_VERSION

    def all_components(self) -> tuple[str, ...]:
        return _dedupe(
            [
                *self.external_services,
                *self.message_queues,
                *self.data_stores,
                *self.middleware_components,
                *self.architecture_components,
                *self.technical_components,
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_entities": list(self.project_entities),
            "business_domains": list(self.business_domains),
            "technical_components": list(self.technical_components),
            "architecture_components": list(self.architecture_components),
            "middleware_components": list(self.middleware_components),
            "data_stores": list(self.data_stores),
            "message_queues": list(self.message_queues),
            "external_services": list(self.external_services),
            "metrics": [metric.to_dict() for metric in self.metrics],
            "scale_indicators": list(self.scale_indicators),
            "performance_indicators": list(self.performance_indicators),
            "failure_signals": list(self.failure_signals),
            "consistency_signals": list(self.consistency_signals),
            "state_machine_signals": list(self.state_machine_signals),
            "idempotency_signals": list(self.idempotency_signals),
            "reconciliation_signals": list(self.reconciliation_signals),
            "cost_signals": list(self.cost_signals),
            "observability_signals": list(self.observability_signals),
            "ownership_signals": list(self.ownership_signals),
            "communication_signals": list(self.communication_signals),
            "evidence_refs": list(self.evidence_refs),
            "source_availability": self.source_availability,
            "confidence_level": self.confidence_level,
            "low_confidence_flags": list(self.low_confidence_flags),
            "component_signals": [signal.to_dict() for signal in self.component_signals],
            "signals": [signal.to_dict() for signal in self.signals],
            "signal_version": self.signal_version,
        }


@dataclass(frozen=True)
class _EvidenceItem:
    ref_id: str
    source_type: str
    text: str
    material: bool


_COMPONENT_SPECS: tuple[tuple[str, str, str], ...] = (
    ("MinIO", "external_services", r"(?<![a-z0-9])minio(?![a-z0-9])"),
    ("RocketMQ", "message_queues", r"(?<![a-z0-9])rocketmq(?![a-z0-9])"),
    ("RabbitMQ", "message_queues", r"(?<![a-z0-9])rabbitmq(?![a-z0-9])"),
    ("Kafka", "message_queues", r"(?<![a-z0-9])kafka(?![a-z0-9])"),
    ("MQ", "message_queues", r"(?<![a-z0-9])mq(?![a-z0-9])|消息队列"),
    ("MySQL", "data_stores", r"(?<![a-z0-9])mysql(?![a-z0-9])"),
    ("PostgreSQL", "data_stores", r"(?<![a-z0-9])postgresql(?![a-z0-9])|(?<![a-z0-9])postgres(?![a-z0-9])"),
    ("Redis", "data_stores", r"(?<![a-z0-9])redis(?![a-z0-9])"),
    ("Elasticsearch", "data_stores", r"(?<![a-z0-9])elasticsearch(?![a-z0-9])|(?<![a-z0-9])es(?![a-z0-9])"),
    ("OSS", "external_services", r"(?<![a-z0-9])oss(?![a-z0-9])"),
    ("S3", "external_services", r"(?<![a-z0-9])s3(?![a-z0-9])"),
    ("向量化", "technical_components", r"向量化|(?<![a-z0-9])embedding(?![a-z0-9])|(?<![a-z0-9])vector(?![a-z0-9])"),
    ("RAG", "technical_components", r"(?<![a-z0-9])rag(?![a-z0-9])"),
    ("Agent", "technical_components", r"(?<![a-z0-9])agent(?![a-z0-9])"),
    ("工具调用", "technical_components", r"工具调用"),
    ("记忆", "technical_components", r"记忆"),
    ("分布式锁", "middleware_components", r"分布式锁"),
    ("状态机", "architecture_components", r"状态机"),
)

_COMPONENT_ALIASES = {
    "minio": "MinIO",
    "redis": "Redis",
    "mysql": "MySQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "es": "Elasticsearch",
    "elasticsearch": "Elasticsearch",
    "mq": "MQ",
    "消息队列": "MQ",
    "rocketmq": "RocketMQ",
    "kafka": "Kafka",
    "rabbitmq": "RabbitMQ",
    "oss": "OSS",
    "s3": "S3",
    "embedding": "向量化",
    "vector": "向量化",
    "向量化": "向量化",
    "rag": "RAG",
    "agent": "Agent",
    "工具调用": "工具调用",
    "记忆": "记忆",
}


def normalize_evidence_text(text: object | None) -> str:
    if text is None:
        return ""
    normalized = str(text)
    normalized = normalized.replace("，", "，").replace("；", "；")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def normalize_component_name(name: object | None) -> str:
    text = normalize_evidence_text(name)
    if not text:
        return ""
    return _COMPONENT_ALIASES.get(text.lower(), _COMPONENT_ALIASES.get(text, text))


def extract_metric_signals(
    text: object | None,
    *,
    evidence_ref: str = "unknown",
    source_type: str = "unknown",
) -> tuple[MetricSignal, ...]:
    normalized = normalize_evidence_text(text)
    if not normalized:
        return ()
    metrics: list[MetricSignal] = []

    latency_pattern = re.compile(
        r"(?P<before>\d+(?:\.\d+)?)\s*(?P<before_unit>秒|s|ms)\s*(?:到|->|→)\s*"
        r"(?P<after>\d+(?:\.\d+)?)\s*(?P<after_unit>秒|s|ms)?",
        flags=re.IGNORECASE,
    )
    for match in latency_pattern.finditer(normalized):
        before = _number(match.group("before"))
        after = _number(match.group("after"))
        unit = match.group("before_unit")
        after_unit = match.group("after_unit") or unit
        display = f"{match.group('before')}{'' if unit.lower() == 's' else ' '}{unit} {'->' if '->' in match.group(0) else '到'} {match.group('after')}{'' if after_unit.lower() == 's' else ' '}{after_unit}"
        if "->" not in match.group(0) and "→" not in match.group(0):
            display = f"{match.group('before')} {unit}到 {match.group('after')} {after_unit}"
        improvement = _improvement_display(before, after)
        metrics.append(
            MetricSignal(
                metric_type="latency_improvement",
                display=display,
                evidence_ref=evidence_ref,
                source_type=source_type,
                before=before,
                after=after,
                unit=unit,
                improvement_display=improvement,
            )
        )

    for match in re.finditer(r"(?<![a-z0-9])\d+(?:\.\d+)?\s*(?:GB|MB)(?![a-z0-9])", normalized, flags=re.IGNORECASE):
        metrics.append(
            MetricSignal(
                metric_type="scale",
                display=match.group(0).replace(" ", "").upper(),
                evidence_ref=evidence_ref,
                source_type=source_type,
                unit=re.sub(r"[^a-zA-Z]", "", match.group(0)).upper(),
            )
        )

    for token in ("QPS", "TPS", "RT", "P95", "P99"):
        if re.search(rf"(?<![a-z0-9]){token}(?![a-z0-9])", normalized, flags=re.IGNORECASE):
            metrics.append(
                MetricSignal(
                    metric_type="performance",
                    display=token,
                    evidence_ref=evidence_ref,
                    source_type=source_type,
                )
            )

    for term, metric_type in (
        ("耗时", "latency"),
        ("吞吐", "throughput"),
        ("错误率", "error_rate"),
        ("成功率", "success_rate"),
        ("成本", "cost"),
        ("消息堆积", "queue_backlog"),
    ):
        if term in normalized:
            metrics.append(
                MetricSignal(
                    metric_type=metric_type,
                    display=term,
                    evidence_ref=evidence_ref,
                    source_type=source_type,
                )
            )
    return _dedupe_metrics(metrics)


def extract_evidence_signals(
    *,
    progress_node: dict[str, Any] | None,
    selected_evidence_chunks: list[Any] | tuple[Any, ...] = (),
    session_context: dict[str, Any] | None = None,
    theme: str | None = None,
    custom_topic_text: str | None = None,
    recent_turns: list[Any] | tuple[Any, ...] | None = None,
) -> EvidenceSignalSet:
    items = _collect_evidence_items(
        progress_node=progress_node,
        selected_evidence_chunks=selected_evidence_chunks,
        session_context=session_context or {},
        custom_topic_text=custom_topic_text,
        recent_turns=recent_turns,
    )
    full_text = " ".join(item.text for item in items)
    material_refs = [item.ref_id for item in items if item.material]
    text_refs = [item.ref_id for item in items if item.text]

    component_signals = _extract_component_signals(items)
    metrics = _dedupe_metrics(
        metric
        for item in items
        for metric in extract_metric_signals(item.text, evidence_ref=item.ref_id, source_type=item.source_type)
    )
    domains = _detect_terms(
        full_text,
        (
            ("库存", r"库存|扣减|仓库维度|物料"),
            ("日志处理", r"日志|切块|入库"),
            ("知识库/检索", r"知识库|检索|rag|向量化|embedding|vector"),
            ("支付", r"支付"),
            ("Agent 执行", r"agent|工具调用|记忆|上下文污染"),
        ),
    )
    failures = _detect_terms(
        full_text,
        (
            ("部分成功", r"部分成功"),
            ("部分失败", r"部分失败"),
            ("超时", r"超时"),
            ("失败重试", r"失败重试|重试"),
            ("消息堆积", r"消息堆积"),
            ("工具调用失败", r"工具调用失败|工具失败"),
            ("上下文污染", r"上下文污染"),
            ("回滚失败", r"回滚失败"),
        ),
    )
    consistency = _detect_terms(
        full_text,
        (
            ("分布式锁", r"分布式锁"),
            ("事务消息", r"事务消息"),
            ("半事务消息", r"半事务消息"),
            ("本地事务", r"本地事务"),
            ("最终一致", r"最终一致"),
            ("总库存一致", r"总库存一致"),
            ("一致性", r"一致性"),
        ),
    )
    state_machine = _detect_terms(full_text, (("状态机", r"状态机"), ("状态流转", r"状态流转"), ("核心状态", r"核心状态")))
    idempotency = _detect_terms(full_text, (("幂等", r"幂等"), ("幂等键", r"幂等键")))
    reconciliation = _detect_terms(
        full_text,
        (
            ("对账", r"对账"),
            ("回补", r"回补"),
            ("补偿", r"补偿"),
            ("断点续跑", r"断点续跑"),
            ("重试收敛", r"重试收敛"),
            ("回滚", r"回滚"),
        ),
    )
    cost = _detect_terms(full_text, (("成本", r"成本|token"), ("成本控制", r"成本控制"), ("成本上限", r"成本上限")))
    observability = _detect_terms(full_text, (("可观测", r"可观测"), ("trace", r"trace"), ("监控", r"监控"), ("告警", r"告警"), ("指标", r"指标")))
    ownership = _detect_terms(full_text, (("Owner", r"owner"), ("职责边界", r"职责边界|个人职责"), ("负责", r"负责")))
    communication = _detect_terms(full_text, (("STAR", r"star"), ("背景压缩", r"背景压缩"), ("逻辑顺序", r"逻辑顺序"), ("复盘", r"复盘"), ("表达", r"表达")))

    metric_displays = tuple(metric.display for metric in metrics)
    scale = _dedupe([display for display in metric_displays if _is_scale_metric(display)] + list(_detect_terms(full_text, (("高峰期", r"高峰"), ("并发", r"并发"), ("消息堆积", r"消息堆积")))) )
    performance = _dedupe([display for display in metric_displays if _is_performance_metric(display)] + list(_detect_terms(full_text, (("异步处理", r"异步处理"), ("吞吐", r"吞吐"), ("耗时", r"耗时")))) )

    category_values = _component_values_by_category(component_signals)
    low_flags = _low_confidence_flags(
        theme=theme,
        has_material=bool(material_refs),
        has_text=bool(text_refs),
        has_metrics=_has_strong_metric(metrics),
        has_failure=bool(failures),
        has_components=bool(component_signals),
        text=full_text,
    )
    confidence = _confidence_level(
        has_material=bool(material_refs),
        has_components=bool(component_signals),
        has_metrics=_has_strong_metric(metrics),
        has_failure_or_consistency=bool(failures or consistency or state_machine or reconciliation),
        low_flags=low_flags,
    )
    source_availability = "available" if material_refs else ("partial" if text_refs else "unavailable")
    evidence_refs = _dedupe([*text_refs, *[signal.evidence_ref for signal in component_signals], *[metric.evidence_ref for metric in metrics]])
    signals = _build_evidence_signals(
        items=items,
        values=[
            *domains,
            *failures,
            *consistency,
            *state_machine,
            *idempotency,
            *reconciliation,
            *cost,
            *observability,
            *ownership,
            *communication,
        ],
    )
    return EvidenceSignalSet(
        project_entities=_project_entities(progress_node),
        business_domains=domains,
        technical_components=category_values["technical_components"],
        architecture_components=category_values["architecture_components"],
        middleware_components=category_values["middleware_components"],
        data_stores=category_values["data_stores"],
        message_queues=category_values["message_queues"],
        external_services=category_values["external_services"],
        metrics=metrics,
        scale_indicators=scale,
        performance_indicators=performance,
        failure_signals=failures,
        consistency_signals=consistency,
        state_machine_signals=state_machine,
        idempotency_signals=idempotency,
        reconciliation_signals=reconciliation,
        cost_signals=cost,
        observability_signals=observability,
        ownership_signals=ownership,
        communication_signals=communication,
        evidence_refs=evidence_refs,
        source_availability=source_availability,
        confidence_level=confidence,
        low_confidence_flags=low_flags,
        component_signals=component_signals,
        signals=signals,
    )


def _collect_evidence_items(
    *,
    progress_node: dict[str, Any] | None,
    selected_evidence_chunks: list[Any] | tuple[Any, ...],
    session_context: dict[str, Any],
    custom_topic_text: str | None,
    recent_turns: list[Any] | tuple[Any, ...] | None,
) -> tuple[_EvidenceItem, ...]:
    items: list[_EvidenceItem] = []

    def add(ref_id: str | None, source_type: str, text: object | None, *, material: bool) -> None:
        clean = normalize_evidence_text(text)
        if clean:
            items.append(_EvidenceItem(ref_id=ref_id or source_type, source_type=source_type, text=clean, material=material))

    if progress_node:
        node_ref = normalize_evidence_text(progress_node.get("progress_node_ref")) or "progress_node"
        add(node_ref, "progress_node", progress_node.get("title"), material=False)
        add(node_ref, "progress_node", progress_node.get("expected_capability"), material=False)
        for key in ("related_job_requirements", "related_resume_evidence", "missing_points", "related_match_gaps"):
            for value in _as_list(progress_node.get(key)):
                add(node_ref, "progress_node", value, material=False)

    for chunk in selected_evidence_chunks or ():
        ref_id = normalize_evidence_text(getattr(chunk, "chunk_id", None)) or "evidence_chunk"
        source_type = normalize_evidence_text(getattr(chunk, "source_type", None)) or "evidence_chunk"
        add(ref_id, source_type, f"{getattr(chunk, 'title', '')} {getattr(chunk, 'text', '')}", material=True)

    job = session_context.get("job_snapshot") if isinstance(session_context, dict) else None
    if isinstance(job, dict):
        job_ref = normalize_evidence_text(job.get("job_version_id") or job.get("job_id")) or "job_snapshot"
        for index, value in enumerate([* _as_list(job.get("requirements")), * _as_list(job.get("responsibilities")), * _as_list(job.get("other_notes"))], start=1):
            add(f"{job_ref}:job:{index}", "job_snapshot", value, material=True)

    resume = session_context.get("resume_snapshot") if isinstance(session_context, dict) else None
    if isinstance(resume, dict):
        resume_ref = normalize_evidence_text(resume.get("resume_version_id") or resume.get("resume_id")) or "resume_snapshot"
        add(f"{resume_ref}:summary", "resume_snapshot", resume.get("summary"), material=True)
        for index, value in enumerate([* _as_list(resume.get("project_experiences")), * _as_list(resume.get("skills")), * _as_list(resume.get("work_experiences"))], start=1):
            add(f"{resume_ref}:resume:{index}", "resume_snapshot", value, material=True)

    match_context = session_context.get("match_context") if isinstance(session_context, dict) else None
    if isinstance(match_context, dict):
        match_ref = normalize_evidence_text(match_context.get("analysis_id")) or "match_context"
        for index, value in enumerate([* _as_list(match_context.get("missing_points")), * _as_list(match_context.get("match_points")), * _as_list(match_context.get("suggested_questions"))], start=1):
            add(f"{match_ref}:match:{index}", "match_context", value, material=True)

    turns = recent_turns if recent_turns is not None else session_context.get("turns", []) if isinstance(session_context, dict) else []
    for index, turn in enumerate(_as_list(turns)[-5:], start=1):
        if isinstance(turn, dict):
            add(f"turn:{index}", "history_turn", turn.get("question_text"), material=True)
            add(f"turn:{index}", "history_turn", turn.get("answer_text"), material=True)
            add(f"turn:{index}", "history_turn", turn.get("feedback_text") or turn.get("feedback_summary"), material=True)

    add("custom_topic", "custom_topic", custom_topic_text, material=False)
    return tuple(_dedupe_items(items))


def _extract_component_signals(items: tuple[_EvidenceItem, ...]) -> tuple[ComponentSignal, ...]:
    signals: list[ComponentSignal] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        lower = item.text.lower()
        for name, category, pattern in _COMPONENT_SPECS:
            if re.search(pattern, lower, flags=re.IGNORECASE):
                key = (name, category)
                if key in seen:
                    continue
                seen.add(key)
                signals.append(ComponentSignal(name=name, category=category, evidence_ref=item.ref_id, source_type=item.source_type))
    return tuple(signals)


def _component_values_by_category(signals: tuple[ComponentSignal, ...]) -> dict[str, tuple[str, ...]]:
    categories = {
        "technical_components": [],
        "architecture_components": [],
        "middleware_components": [],
        "data_stores": [],
        "message_queues": [],
        "external_services": [],
    }
    for signal in signals:
        categories.setdefault(signal.category, []).append(signal.name)
    return {key: _dedupe(value) for key, value in categories.items()}


def _detect_terms(text: str, specs: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    lower = text.lower()
    result: list[str] = []
    for label, pattern in specs:
        if re.search(pattern, lower, flags=re.IGNORECASE):
            result.append(label)
    return _dedupe(result)


def _build_evidence_signals(*, items: tuple[_EvidenceItem, ...], values: list[str]) -> tuple[EvidenceSignal, ...]:
    signals: list[EvidenceSignal] = []
    for value in _dedupe(values):
        for item in items:
            if value.lower() in item.text.lower() or value in item.text:
                signals.append(EvidenceSignal(signal_type="keyword", value=value, evidence_ref=item.ref_id, source_type=item.source_type))
                break
    return tuple(signals)


def _project_entities(progress_node: dict[str, Any] | None) -> tuple[str, ...]:
    if not progress_node:
        return ()
    title = normalize_evidence_text(progress_node.get("title"))
    return (title,) if title else ()


def _low_confidence_flags(
    *,
    theme: str | None,
    has_material: bool,
    has_text: bool,
    has_metrics: bool,
    has_failure: bool,
    has_components: bool,
    text: str,
) -> tuple[str, ...]:
    flags: list[str] = []
    if not has_text:
        flags.append("evidence_missing")
    if not has_material:
        flags.append("abstract_node_only")
    if theme in {"technical", "mixed", None} and not has_metrics:
        flags.append("weak_metric_evidence")
    if theme in {"technical", "mixed", None} and not has_failure:
        flags.append("weak_failure_evidence")
    if not has_components and _has_component_like_need(text):
        flags.append("no_concrete_component_evidence")
    return tuple(dict.fromkeys(flags))


def _has_strong_metric(metrics: tuple[MetricSignal, ...]) -> bool:
    return any(metric.metric_type not in {"cost"} for metric in metrics)


def _confidence_level(
    *,
    has_material: bool,
    has_components: bool,
    has_metrics: bool,
    has_failure_or_consistency: bool,
    low_flags: tuple[str, ...],
) -> str:
    if not has_material:
        return "low"
    if has_components and (has_metrics or has_failure_or_consistency):
        return "high"
    if has_failure_or_consistency or has_metrics:
        return "medium"
    if low_flags:
        return "low"
    return "medium"


def _has_component_like_need(text: str) -> bool:
    return bool(re.search(r"系统组件|链路|架构|存储|消息|缓存|索引|服务", text))


def _as_list(value: object) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _dedupe(items: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for item in items:
        text = normalize_evidence_text(item)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _dedupe_items(items: list[_EvidenceItem]) -> list[_EvidenceItem]:
    result: list[_EvidenceItem] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item.ref_id, item.text)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _dedupe_metrics(metrics: Any) -> tuple[MetricSignal, ...]:
    result: list[MetricSignal] = []
    seen: set[tuple[str, str, str]] = set()
    for metric in metrics:
        key = (metric.metric_type, metric.display, metric.evidence_ref)
        if key in seen:
            continue
        seen.add(key)
        result.append(metric)
    return tuple(result)


def _number(value: str) -> int | float:
    numeric = float(value)
    return int(numeric) if numeric.is_integer() else numeric


def _improvement_display(before: int | float, after: int | float) -> str | None:
    if after == 0:
        return None
    ratio = before / after
    if ratio <= 0:
        return None
    rounded = round(ratio, 1)
    return f"{int(rounded) if rounded.is_integer() else rounded}x"


def _is_scale_metric(display: str) -> bool:
    return bool(re.search(r"\d+(?:\.\d+)?(?:GB|MB)", display, flags=re.IGNORECASE)) or display in {"高峰期", "并发", "消息堆积"}


def _is_performance_metric(display: str) -> bool:
    return display in {"QPS", "TPS", "RT", "P95", "P99", "耗时", "吞吐", "异步处理"} or "到" in display or "->" in display
