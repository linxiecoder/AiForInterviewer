"""Default-off PR5 Polish question business graph skeleton."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

from app.application.ai_runtime.contracts import (
    AgentCommandEnvelope,
    AgentRunContext,
    AgentRunResult,
    GraphDisabledError,
    RuntimePolicyError,
    RuntimeValidationError,
    contains_sensitive_payload,
    sanitize_payload,
)
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver

if TYPE_CHECKING:
    from app.application.ai_runtime.registry import GraphDescriptor


POLISH_QUESTION_GRAPH_NAME = "polish_question_graph"
POLISH_QUESTION_GRAPH_VERSION = "pr5-skeleton"
POLISH_QUESTION_GRAPH_FLAG = "AIFI_GRAPH_POLISH_QUESTION_ENABLED"
POLISH_QUESTION_TRACE_TASK_TYPE = "polish_question_generation"

_DEFAULT_ENTRYPOINTS = ("start", "replay")
_SUPPORTED_OUTPUTS = ("result_refs", "candidate_refs", "suggestion_refs", "interrupt_refs")
_LEGACY_PROMPT_CONTRACT_IDS = ("P-POLISH-002", "P-SHARED-001", "P-SHARED-003")
POLISH_QUESTION_READONLY_PARITY_VERSION = "pr5-q3-readonly-parity"

_FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        "raw" + "_prompt",
        "raw" + "_completion",
        "raw" + "_provider" + "_payload",
        "provider" + "_payload",
        "checkpoint" + "_payload",
        "full" + "_resume",
        "full" + "_jd",
        "full" + "_answer",
        "hidden" + "_rubric",
        "system" + "_prompt",
    }
)
_ENTITY_PATTERNS = (
    ("订单履约", ("订单履约", "履约系统")),
    ("库存预占", ("库存预占",)),
    ("支付回调", ("支付回调",)),
    ("超时取消", ("超时取消",)),
    ("状态流转", ("状态流转", "状态机")),
    ("库存扣减", ("库存扣减", "扣减库存")),
    ("事务消息", ("事务消息",)),
    ("仓库", ("仓库",)),
    ("物料", ("物料",)),
    ("超卖", ("超卖",)),
    ("1GB 文件上传", ("1GB 文件上传", "1GB文件上传", "文件上传")),
    ("1GB", ("1GB",)),
    ("异步解析", ("异步解析",)),
    ("日志", ("日志", "log")),
    ("高并发接口设计", ("高并发接口设计", "高并发接口", "高并发")),
    ("限流降级", ("限流降级", "限流", "降级")),
    ("压测", ("压测", "压力测试")),
    ("可观测性", ("可观测性", "观测性")),
    ("RAG", ("RAG", "检索增强")),
    ("LLM", ("LLM", "大模型")),
    ("Agent", ("Agent", "智能体")),
    ("AI模拟面试工作台", ("AI模拟面试工作台", "AI 模拟面试工作台")),
)
_ENTITY_GROUPS = {
    "订单履约": "order_fulfillment",
    "库存预占": "order_fulfillment",
    "支付回调": "order_fulfillment",
    "超时取消": "order_fulfillment",
    "状态流转": "order_fulfillment",
    "库存扣减": "inventory_consistency",
    "事务消息": "inventory_consistency",
    "仓库": "inventory_consistency",
    "物料": "inventory_consistency",
    "超卖": "inventory_consistency",
    "1GB 文件上传": "file_upload",
    "1GB": "file_upload",
    "异步解析": "file_upload",
    "日志": "log_processing",
    "高并发接口设计": "job_high_concurrency",
    "限流降级": "job_high_concurrency",
    "压测": "job_high_concurrency",
    "可观测性": "job_high_concurrency",
    "RAG": "fixed_template_ai",
    "LLM": "fixed_template_ai",
    "Agent": "fixed_template_ai",
    "AI模拟面试工作台": "fixed_template_ai",
}
_INVENTORY_ENTITIES = frozenset({"库存预占", "库存扣减", "仓库", "物料", "超卖"})
_FIXED_TEMPLATE_DOMAIN_ENTITIES = frozenset({"日志", "RAG", "LLM", "Agent", "AI模拟面试工作台"})
_JOB_GAP_CLAIM_PHRASES = ("你负责过", "你做过", "你在项目中", "你曾经负责", "你落地过")


def build_polish_question_graph_descriptor() -> "GraphDescriptor":
    from app.application.ai_runtime.registry import GraphDescriptor

    return GraphDescriptor(
        graph_name=POLISH_QUESTION_GRAPH_NAME,
        graph_version=POLISH_QUESTION_GRAPH_VERSION,
        capability="polish_question",
        lifecycle_status="placeholder",
        runtime_flag_key=POLISH_QUESTION_GRAPH_FLAG,
        default_enabled=False,
        supported_entrypoints=_DEFAULT_ENTRYPOINTS,
        supported_outputs=_SUPPORTED_OUTPUTS,
        prompt_contract_ids=_LEGACY_PROMPT_CONTRACT_IDS,
        eval_suite_ids=("EVAL-POLISH-QUESTION-001",),
        resume_schema_ids={},
        interrupt_types=(),
        required_permissions=("owner",),
        visibility="owner_only",
        health_summary_refs=("health.polish_question.pr5_skeleton",),
        config_schema_ref="graph_config.polish_question.pr5_skeleton",
        implementation_pr="PR5",
        migration_status="skeleton_default_off_direct_path_retained",
        provider_enabled=False,
        formal_write_targets=(),
        db_business_write_targets=(),
        rollback_safe=True,
        disabled_behavior="legacy_direct_path_retained",
    )


def run_polish_question_skeleton(
    context: AgentRunContext,
    command: AgentCommandEnvelope,
    flag_resolver: RuntimeFlagResolver | None = None,
) -> AgentRunResult:
    descriptor = build_polish_question_graph_descriptor()
    _validate_context(context, command, descriptor)
    resolver = flag_resolver or RuntimeFlagResolver()
    decision = resolver.resolve_graph_flag(descriptor, actor_id=context.actor_id, caller="runner_entry")
    if not decision.enabled:
        raise GraphDisabledError(f"graph disabled: {descriptor.graph_name}")

    output_refs, interrupt_refs = _build_output_refs(context=context, command=command)
    checkpoint_ref = "ackpt_" + _stable_id(context.owner_id, context.run_id, "question_checkpoint")
    metadata = {
        "graph_name": descriptor.graph_name,
        "graph_version": descriptor.graph_version,
        "runtime_flag_key": descriptor.runtime_flag_key,
        "runtime_flag_source": decision.source,
        "provider_calls": 0,
        "formal_business_writes": 0,
        "db_business_writes": 0,
        "checkpoint_refs_only": True,
        "checkpoint_refs_are_business_facts": False,
        "rollback_safe": True,
        "legacy_direct_path_retained_when_disabled": True,
        "sanitized": True,
        "input_refs": command.input_refs,
        "requested_outputs": command.requested_outputs,
    }
    return AgentRunResult(
        run_id=context.run_id,
        status="skeleton_succeeded",
        output_refs=output_refs,
        trace_refs=(checkpoint_ref,),
        interrupt_refs=interrupt_refs,
        formal_refs=(),
        metadata=sanitize_payload(metadata),
    )


def derive_question_scenario(
    *,
    session_ref: str,
    selected_progress_node_summary: str | None = None,
    selected_evidence_refs: tuple[str, ...] | list[str] = (),
    resume_evidence_summaries: tuple[object, ...] | list[object] = (),
    job_requirement_summaries: tuple[object, ...] | list[object] = (),
    match_gap_summaries: tuple[object, ...] | list[object] = (),
    history_feedback_summaries: tuple[object, ...] | list[object] = (),
    completed_focus_refs: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    if contains_sensitive_payload(
        {
            "session_ref": session_ref,
            "selected_progress_node_summary": selected_progress_node_summary,
            "resume_evidence_summaries": resume_evidence_summaries,
            "job_requirement_summaries": job_requirement_summaries,
            "match_gap_summaries": match_gap_summaries,
            "history_feedback_summaries": history_feedback_summaries,
        }
    ):
        raise RuntimePolicyError("polish question scenario derivation accepts summaries only")

    selected_refs = tuple(str(ref) for ref in selected_evidence_refs if str(ref).strip())
    resume_items = _coerce_evidence_items(resume_evidence_summaries, source_type="resume_project")
    job_items = _coerce_evidence_items(job_requirement_summaries, source_type="job_requirement")
    match_items = _coerce_evidence_items(match_gap_summaries, source_type="match_gap")
    history_items = _coerce_evidence_items(history_feedback_summaries, source_type="history_feedback")
    evidence_items = (*resume_items, *match_items, *job_items, *history_items)
    primary = _choose_primary_evidence(evidence_items, selected_refs)
    primary_entities = tuple(primary["entities"]) if primary else ()
    primary_group = _primary_group(primary_entities)
    forbidden_entities = _forbidden_entities(evidence_items, primary_ref=primary["ref"] if primary else "", primary_group=primary_group)
    scenario_mode = _scenario_mode(primary, primary_entities, resume_items)
    low_confidence_flags = _low_confidence_flags(
        primary=primary,
        primary_entities=primary_entities,
        scenario_mode=scenario_mode,
        forbidden_entities=forbidden_entities,
    )
    confidence_level = _confidence_level(primary=primary, primary_entities=primary_entities, scenario_mode=scenario_mode)
    source_refs = tuple([primary["ref"]] if primary and primary["ref"] else selected_refs[:1])
    source_types = tuple(_unique([str(primary["source_type"])]) if primary else ())
    scenario_title = _scenario_title(primary_entities, scenario_mode, selected_progress_node_summary)
    primary_resume = _primary_summary(resume_items, primary_entities)
    primary_job = _primary_summary(job_items, primary_entities)
    primary_match_gap = _primary_summary(match_items, primary_entities)
    history_feedback_summary = "；".join(str(item["summary"]) for item in history_items if item.get("summary"))

    scenario = {
        "session_ref": session_ref,
        "scenario_title": scenario_title,
        "scenario_summary": str(primary["summary"]) if primary else (selected_progress_node_summary or "证据不足的打磨题场景"),
        "scenario_mode": scenario_mode,
        "source_refs": source_refs,
        "source_types": source_types,
        "selected_progress_node_summary": selected_progress_node_summary or "",
        "selected_evidence_refs": selected_refs,
        "completed_focus_refs": tuple(str(ref) for ref in completed_focus_refs if str(ref).strip()),
        "primary_resume_evidence": primary_resume,
        "primary_job_requirement": primary_job,
        "primary_match_gap": primary_match_gap,
        "history_feedback_summary": history_feedback_summary,
        "allowed_entities": primary_entities,
        "forbidden_entities": forbidden_entities,
        "confidence_level": confidence_level,
        "low_confidence_flags": low_confidence_flags,
    }
    return sanitize_payload(scenario)


def build_polish_question_candidate_readonly(
    *,
    owner_id: str,
    run_id: str,
    ai_task_id: str,
    session_ref: str,
    scenario: dict[str, Any],
) -> dict[str, Any]:
    scenario_title = str(scenario.get("scenario_title") or "候选人项目表达场景")
    evidence_refs = tuple(str(ref) for ref in scenario.get("source_refs", ()) if str(ref).strip())
    suffix = _stable_id(
        owner_id,
        run_id,
        ai_task_id,
        session_ref,
        scenario_title,
        json.dumps(evidence_refs, sort_keys=True),
    )
    candidate_ref = "question_candidate_ref_" + suffix
    scenario_ref = "scenario_ref_" + suffix
    validation_ref = "validation_ref_" + suffix
    question_text = _candidate_question_text(scenario)
    candidate = {
        "candidate_ref": candidate_ref,
        "scenario": scenario,
        "question_text": question_text,
        "question_pattern": "polish_structured_experience",
        "evidence_refs": evidence_refs,
        "source_availability": {
            "resume": bool(scenario.get("primary_resume_evidence")),
            "job_requirement": bool(scenario.get("primary_job_requirement")),
            "match_gap": bool(scenario.get("primary_match_gap")),
            "history_feedback": bool(scenario.get("history_feedback_summary")),
        },
        "confidence_level": scenario.get("confidence_level", "low"),
        "low_confidence_flags": tuple(scenario.get("low_confidence_flags", ())),
        "trace_refs": (scenario_ref, candidate_ref, validation_ref),
        "sanitized": True,
    }
    gate = question_candidate_quality_gate(candidate)
    candidate["quality_gate"] = gate
    return sanitize_payload(candidate)


def question_candidate_quality_gate(candidate: dict[str, Any]) -> dict[str, Any]:
    blocking_reasons: list[str] = []
    low_confidence_reasons: list[str] = []
    scenario = candidate.get("scenario") if isinstance(candidate.get("scenario"), dict) else {}
    question_text = str(candidate.get("question_text", ""))
    evidence_refs = tuple(candidate.get("evidence_refs", ()))
    allowed_entities = tuple(str(entity) for entity in scenario.get("allowed_entities", ()) if str(entity).strip())
    forbidden_entities = tuple(str(entity) for entity in scenario.get("forbidden_entities", ()) if str(entity).strip())
    detected_entities = _extract_entities(question_text)

    if not evidence_refs:
        blocking_reasons.append("missing_evidence_refs")
    if _has_raw_payload_leak(candidate):
        blocking_reasons.append("raw_payload_leak")
    if any(_contains_entity(question_text, entity) for entity in forbidden_entities):
        blocking_reasons.append("cross_evidence_scenario_mixing")
    if _has_unsupported_business_entity(detected_entities, allowed_entities):
        blocking_reasons.append("unsupported_business_entity")
    if _has_fixed_template_domain_leak(detected_entities, allowed_entities):
        blocking_reasons.append("fixed_template_domain_leak")
    if str(scenario.get("scenario_mode", "")) in {"job_gap", "learning_gap"} and any(
        phrase in question_text for phrase in _JOB_GAP_CLAIM_PHRASES
    ):
        blocking_reasons.append("job_gap_claimed_as_project_experience")

    if candidate.get("confidence_level") == "low":
        low_confidence_reasons.append("low_confidence_candidate")
    low_confidence_reasons.extend(str(flag) for flag in candidate.get("low_confidence_flags", ()) if str(flag).strip())

    return {
        "passed": not blocking_reasons,
        "blocking_reasons": tuple(_unique(blocking_reasons)),
        "low_confidence_reasons": tuple(_unique(low_confidence_reasons)),
        "checked_rules": (
            "cross_evidence_scenario_mixing",
            "unsupported_business_entity",
            "fixed_template_domain_leak",
            "job_gap_claimed_as_project_experience",
            "missing_evidence_refs",
            "raw_payload_leak",
        ),
    }


def run_polish_question_readonly_parity(
    context: AgentRunContext,
    command: AgentCommandEnvelope,
    flag_resolver: RuntimeFlagResolver | None = None,
) -> AgentRunResult:
    descriptor = build_polish_question_graph_descriptor()
    _validate_context(context, command, descriptor)
    resolver = flag_resolver or RuntimeFlagResolver()
    decision = resolver.resolve_graph_flag(descriptor, actor_id=context.actor_id, caller="runner_entry")
    if not decision.enabled:
        raise GraphDisabledError(f"graph disabled: {descriptor.graph_name}")

    metadata = command.metadata
    scenario = derive_question_scenario(
        session_ref=str(command.input_refs[0]),
        selected_progress_node_summary=str(metadata.get("selected_progress_node_summary", "")),
        selected_evidence_refs=tuple(metadata.get("selected_evidence_refs", command.input_refs[1:])),
        resume_evidence_summaries=tuple(metadata.get("resume_evidence_summaries", ())),
        job_requirement_summaries=tuple(metadata.get("job_requirement_summaries", ())),
        match_gap_summaries=tuple(metadata.get("match_gap_summaries", ())),
        history_feedback_summaries=tuple(metadata.get("history_feedback_summaries", ())),
        completed_focus_refs=tuple(metadata.get("completed_focus_refs", ())),
    )
    candidate = build_polish_question_candidate_readonly(
        owner_id=context.owner_id,
        run_id=context.run_id,
        ai_task_id=context.ai_task_id,
        session_ref=str(command.input_refs[0]),
        scenario=scenario,
    )
    quality_gate = candidate["quality_gate"]
    output_refs = (candidate["candidate_ref"],) if quality_gate["passed"] else ()
    result_metadata = {
        "graph_name": descriptor.graph_name,
        "graph_version": descriptor.graph_version,
        "readonly_parity_version": POLISH_QUESTION_READONLY_PARITY_VERSION,
        "runtime_flag_key": descriptor.runtime_flag_key,
        "runtime_flag_source": decision.source,
        "readonly_parity": True,
        "provider_calls": 0,
        "db_business_writes": 0,
        "formal_business_writes": 0,
        "scenario_derivation": "dynamic_evidence_based",
        "checkpoint_refs_are_business_facts": False,
        "candidate_ref": candidate["candidate_ref"],
        "scenario": scenario,
        "candidate": candidate,
        "quality_gate": quality_gate,
        "sanitized": True,
    }
    return AgentRunResult(
        run_id=context.run_id,
        status="readonly_parity_succeeded" if quality_gate["passed"] else "readonly_parity_blocked",
        output_refs=output_refs,
        trace_refs=tuple(candidate["trace_refs"]),
        interrupt_refs=(),
        formal_refs=(),
        metadata=sanitize_payload(result_metadata),
    )


def _validate_context(
    context: AgentRunContext,
    command: AgentCommandEnvelope,
    descriptor: "GraphDescriptor",
) -> None:
    if command != context.command:
        raise RuntimePolicyError("command must match context command")
    if context.graph_name != descriptor.graph_name:
        raise RuntimePolicyError("context graph does not match polish question skeleton")
    if context.graph_version != descriptor.graph_version:
        raise RuntimePolicyError("context graph version does not match polish question skeleton")
    if command.entrypoint not in descriptor.supported_entrypoints:
        raise RuntimeValidationError(f"unsupported entrypoint: {command.entrypoint}")
    if not command.input_refs:
        raise RuntimeValidationError("polish question skeleton requires a session ref")
    session_ref = str(command.input_refs[0]).strip()
    if not session_ref.startswith("session_"):
        raise RuntimeValidationError("polish question skeleton accepts refs only")
    if contains_sensitive_payload(command.input_refs) or contains_sensitive_payload(command.metadata):
        raise RuntimeValidationError("polish question skeleton accepts refs and sanitized metadata only")

    unsupported = tuple(output for output in command.requested_outputs if output not in descriptor.supported_outputs)
    if unsupported:
        raise RuntimeValidationError(f"unsupported output: {', '.join(unsupported)}")


def _build_output_refs(
    *, context: AgentRunContext, command: AgentCommandEnvelope
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    requested_outputs = command.requested_outputs or ("candidate_refs",)
    suffix = _stable_id(
        context.owner_id,
        context.run_id,
        context.ai_task_id,
        command.entrypoint,
        json.dumps(command.input_refs, sort_keys=True),
        json.dumps(requested_outputs, sort_keys=True),
    )
    output_refs: list[str] = []
    interrupt_refs: list[str] = []
    for requested_output in requested_outputs:
        if requested_output == "candidate_refs":
            output_refs.append("question_candidate_ref_" + suffix)
        elif requested_output == "result_refs":
            output_refs.append("question_result_ref_" + suffix)
        elif requested_output == "suggestion_refs":
            output_refs.append("question_suggestion_ref_" + suffix)
        elif requested_output == "interrupt_refs":
            interrupt_refs.append("question_interrupt_ref_" + suffix)
    return tuple(output_refs), tuple(interrupt_refs)


def _coerce_evidence_items(items: tuple[object, ...] | list[object], *, source_type: str) -> tuple[dict[str, Any], ...]:
    coerced: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if isinstance(item, dict):
            summary = str(item.get("summary") or item.get("text") or item.get("title") or "").strip()
            ref = str(
                item.get("ref")
                or item.get("source_ref")
                or item.get("evidence_ref")
                or f"{source_type}_summary_ref_{index}"
            ).strip()
            item_source_type = str(item.get("source_type") or source_type).strip()
        else:
            summary = str(item).strip()
            ref = f"{source_type}_summary_ref_{_stable_id(source_type, index, summary)}"
            item_source_type = source_type
        if not summary:
            continue
        entities = _extract_entities(summary)
        coerced.append(
            {
                "ref": ref,
                "summary": summary,
                "source_type": item_source_type,
                "entities": entities,
                "group": _primary_group(entities),
                "index": index,
            }
        )
    return tuple(coerced)


def _choose_primary_evidence(
    evidence_items: tuple[dict[str, Any], ...], selected_refs: tuple[str, ...]
) -> dict[str, Any] | None:
    if not evidence_items:
        return None
    selected = [item for item in evidence_items if item["ref"] in selected_refs and item["entities"]]
    if selected:
        return selected[0]
    priority = {
        "resume_project": 0,
        "resume": 0,
        "match_gap": 1,
        "job_requirement": 2,
        "history_feedback": 3,
    }
    with_entities = [item for item in evidence_items if item["entities"]]
    candidates = with_entities or list(evidence_items)
    return sorted(candidates, key=lambda item: (priority.get(str(item["source_type"]), 9), int(item["index"])))[0]


def _scenario_mode(
    primary: dict[str, Any] | None, primary_entities: tuple[str, ...], resume_items: tuple[dict[str, Any], ...]
) -> str:
    if primary is None:
        return "learning_gap"
    source_type = str(primary["source_type"])
    if source_type.startswith("job") or source_type == "match_gap":
        primary_group = _primary_group(primary_entities)
        resume_supports_group = any(item["group"] == primary_group and primary_group for item in resume_items)
        return "job_gap" if not resume_supports_group else "resume_project"
    if source_type.startswith("history"):
        return "learning_gap"
    return "resume_project"


def _low_confidence_flags(
    *,
    primary: dict[str, Any] | None,
    primary_entities: tuple[str, ...],
    scenario_mode: str,
    forbidden_entities: tuple[str, ...],
) -> tuple[str, ...]:
    flags: list[str] = []
    if primary is None or not primary_entities:
        flags.append("missing_domain_evidence")
    if scenario_mode == "job_gap":
        flags.append("job_gap_without_resume_project_evidence")
    if forbidden_entities:
        flags.append("multiple_evidence_domains_primary_selected")
    return tuple(_unique(flags))


def _confidence_level(
    *, primary: dict[str, Any] | None, primary_entities: tuple[str, ...], scenario_mode: str
) -> str:
    if primary is None or not primary_entities:
        return "low"
    if scenario_mode == "job_gap":
        return "medium"
    if len(primary_entities) >= 2:
        return "high"
    return "medium"


def _forbidden_entities(
    evidence_items: tuple[dict[str, Any], ...], *, primary_ref: str, primary_group: str
) -> tuple[str, ...]:
    forbidden: list[str] = []
    for item in evidence_items:
        if item["ref"] == primary_ref:
            continue
        if item["group"] and item["group"] != primary_group:
            forbidden.extend(str(entity) for entity in item["entities"])
    return tuple(_unique(forbidden))


def _scenario_title(
    primary_entities: tuple[str, ...], scenario_mode: str, selected_progress_node_summary: str | None
) -> str:
    if primary_entities:
        base = " / ".join(primary_entities[:3])
    elif selected_progress_node_summary:
        base = str(selected_progress_node_summary).strip()[:32]
    else:
        base = "候选人项目表达"
    if scenario_mode == "job_gap":
        return f"{base}补齐场景"
    if scenario_mode == "learning_gap":
        return f"{base}学习迁移场景"
    return base


def _primary_summary(items: tuple[dict[str, Any], ...], primary_entities: tuple[str, ...]) -> str:
    primary_group = _primary_group(primary_entities)
    for item in items:
        if item["group"] == primary_group and primary_group:
            return str(item["summary"])
    return str(items[0]["summary"]) if items else ""


def _candidate_question_text(scenario: dict[str, Any]) -> str:
    scenario_title = str(scenario.get("scenario_title") or "候选人项目表达场景")
    if scenario.get("scenario_mode") in {"job_gap", "learning_gap"}:
        return (
            f"请围绕「{scenario_title}」回答。先说明你对该岗位要求的理解、已有可迁移经验、补齐计划和验证方式，"
            "再讲清可能的约束、方案取舍、风险兜底和阶段性指标。表达上按理解、差距、计划、验证、复盘组织。"
        )
    return (
        f"请围绕「{scenario_title}」回答。先说明业务背景、你的职责边界和目标，再讲清核心链路、关键技术取舍、"
        "失败处理或风险兜底、验证指标。表达上按背景、约束、方案、结果、复盘组织。"
    )


def _extract_entities(text: object) -> tuple[str, ...]:
    value = str(text)
    found: list[str] = []
    for entity, aliases in _ENTITY_PATTERNS:
        if any(_contains_entity(value, alias) for alias in aliases):
            found.append(entity)
    return tuple(_unique(found))


def _primary_group(entities: tuple[str, ...]) -> str:
    for entity in entities:
        group = _ENTITY_GROUPS.get(entity)
        if group:
            return group
    return ""


def _has_unsupported_business_entity(detected_entities: tuple[str, ...], allowed_entities: tuple[str, ...]) -> bool:
    allowed_groups = {_ENTITY_GROUPS.get(entity, "") for entity in allowed_entities}
    for entity in detected_entities:
        if entity in allowed_entities:
            continue
        group = _ENTITY_GROUPS.get(entity, "")
        if entity in _INVENTORY_ENTITIES or entity == "日志" or group not in allowed_groups:
            return True
    return False


def _has_fixed_template_domain_leak(detected_entities: tuple[str, ...], allowed_entities: tuple[str, ...]) -> bool:
    for entity in detected_entities:
        if entity in _FIXED_TEMPLATE_DOMAIN_ENTITIES and entity not in allowed_entities:
            return True
    return False


def _has_raw_payload_leak(value: object) -> bool:
    if contains_sensitive_payload(value):
        return True
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
            if normalized in _FORBIDDEN_PAYLOAD_KEYS:
                return True
            if _has_raw_payload_leak(item):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_has_raw_payload_leak(item) for item in value)
    return False


def _contains_entity(text: object, term: str) -> bool:
    value = str(text).lower()
    target = term.lower()
    return target in value or target.replace(" ", "") in value.replace(" ", "")


def _unique(values: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _stable_id(*parts: object) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(str(part).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:16]
