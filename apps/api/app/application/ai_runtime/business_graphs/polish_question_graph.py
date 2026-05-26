"""Polish question business graph orchestration contract."""

from __future__ import annotations

import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import asdict, dataclass
from time import perf_counter, sleep
from typing import TYPE_CHECKING, Any

from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentCommandEnvelope,
    AgentRunContext,
    AgentRunResult,
    GraphDisabledError,
    RuntimePolicyError,
    RuntimeValidationError,
    contains_sensitive_payload,
    sanitize_payload,
)
from app.application.ai_runtime.handoff import QuestionResultWritePlan, build_question_result_write_plan
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.application.common.logging import LogUtil

if TYPE_CHECKING:
    from app.application.ai_runtime.registry import GraphDescriptor


POLISH_QUESTION_GRAPH_NAME = "polish_question_graph"
POLISH_QUESTION_GRAPH_VERSION = "pr9-agent-orchestration"
POLISH_QUESTION_GRAPH_FLAG = "AIFI_GRAPH_POLISH_QUESTION_ENABLED"
POLISH_QUESTION_PROVIDER_FLAG = "AIFI_REAL_PROVIDER_ENABLED"
POLISH_QUESTION_TRACE_TASK_TYPE = "polish_question_generation"
POLISH_QUESTION_RUNTIME_DEFAULT = False
POLISH_QUESTION_PROVIDER_GATE = False
MAX_AGENT_STEPS = 7
MAX_RETRIES = 2
QUESTION_AGENT_TIMEOUT_SECONDS = 20
QUESTION_AGENT_BACKOFF_SECONDS = 0.25

_DEFAULT_ENTRYPOINTS = ("start", "replay")
_SUPPORTED_OUTPUTS = ("result_refs", "candidate_refs", "suggestion_refs", "interrupt_refs")
_LEGACY_PROMPT_CONTRACT_IDS = ("P-POLISH-002", "P-SHARED-001", "P-SHARED-003")
POLISH_QUESTION_READONLY_PARITY_VERSION = "pr5-q3-readonly-parity"
POLISH_QUESTION_PERSISTENCE_VERSION = "pr5-q4-persistence-handoff"
POLISH_QUESTION_AGENT_PHASES = (
    "plan_task",
    "retrieve_context",
    "draft_question",
    "validate_grounding",
    "repair_or_retry",
    "persist_candidate",
    "finalize",
)

_FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        "raw_prompt",  # sensitive payload denylist marker
        "raw_completion",
        "raw_provider_payload",  # sensitive payload denylist marker
        "provider_payload",  # sensitive payload denylist marker
        "checkpoint_payload",
        "full_resume",
        "full_jd",
        "full_answer",
        "hidden_rubric",
        "system_prompt",  # sensitive payload denylist marker
    }
)
_GENERIC_TERM_STOPWORDS = frozenset(
    {
        "项目",
        "系统",
        "平台",
        "经验",
        "要求",
        "候选人",
        "说明",
        "回答",
        "场景",
        "能力",
        "业务",
        "技术",
        "方案",
        "问题",
        "风险",
        "指标",
    }
)
_JOB_GAP_CLAIM_PHRASES = ("你负责过", "你做过", "你在项目中", "你曾经负责", "你落地过")


@dataclass(frozen=True)
class PolishQuestionToolSchema:
    tool_name: str
    input_schema_id: str
    output_schema_id: str
    max_retries: int = MAX_RETRIES
    timeout_seconds: int = QUESTION_AGENT_TIMEOUT_SECONDS


TOOL_SCHEMAS = (
    PolishQuestionToolSchema("context_retrieval", "polish_question.context_retrieval.input.v1", "polish_question.context_retrieval.output.v1"),
    PolishQuestionToolSchema("evidence_selection", "polish_question.evidence_selection.input.v1", "polish_question.evidence_selection.output.v1"),
    PolishQuestionToolSchema("question_drafting", "polish_question.question_drafting.input.v1", "polish_question.question_drafting.output.v1"),
    PolishQuestionToolSchema("grounding_validation", "polish_question.grounding_validation.input.v1", "polish_question.grounding_validation.output.v1"),
    PolishQuestionToolSchema("candidate_persistence", "polish_question.candidate_persistence.input.v1", "polish_question.candidate_persistence.output.v1"),
)


@dataclass(frozen=True)
class PolishQuestionAgentConfig:
    max_agent_steps: int = MAX_AGENT_STEPS
    max_retries: int = MAX_RETRIES
    timeout_seconds: float = QUESTION_AGENT_TIMEOUT_SECONDS
    backoff_seconds: float = QUESTION_AGENT_BACKOFF_SECONDS


@dataclass(frozen=True)
class PolishQuestionAgentExecution:
    status: str
    candidate: dict[str, Any]
    result_ref: str
    candidate_ref: str
    trace_refs: tuple[str, ...]
    metadata: dict[str, Any]


def build_polish_question_graph_descriptor() -> "GraphDescriptor":
    from app.application.ai_runtime.registry import GraphDescriptor

    return GraphDescriptor(
        graph_name=POLISH_QUESTION_GRAPH_NAME,
        graph_version=POLISH_QUESTION_GRAPH_VERSION,
        capability="polish_question",
        lifecycle_status="active",
        runtime_flag_key=POLISH_QUESTION_GRAPH_FLAG,
        default_enabled=POLISH_QUESTION_RUNTIME_DEFAULT,
        supported_entrypoints=_DEFAULT_ENTRYPOINTS,
        supported_outputs=_SUPPORTED_OUTPUTS,
        prompt_contract_ids=_LEGACY_PROMPT_CONTRACT_IDS,
        eval_suite_ids=("EVAL-POLISH-QUESTION-001",),
        resume_schema_ids={},
        interrupt_types=(),
        required_permissions=("owner",),
        visibility="owner_only",
        health_summary_refs=("health.polish_question.agent_orchestration",),
        config_schema_ref="graph_config.polish_question.agent_orchestration",
        implementation_pr="Goal0526",
        migration_status="agent_orchestration_with_deterministic_fallback",
        provider_enabled=POLISH_QUESTION_PROVIDER_GATE,
        formal_write_targets=(),
        db_business_write_targets=(),
        rollback_safe=True,
        disabled_behavior="deterministic_fallback_with_reason",
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
        "agent_phases": POLISH_QUESTION_AGENT_PHASES,
        "tool_schema_refs": tuple(schema.input_schema_id for schema in TOOL_SCHEMAS),
        "max_agent_steps": MAX_AGENT_STEPS,
        "max_retries": MAX_RETRIES,
        "timeout_seconds": QUESTION_AGENT_TIMEOUT_SECONDS,
        "backoff_seconds": QUESTION_AGENT_BACKOFF_SECONDS,
        "runtime_flag_key": descriptor.runtime_flag_key,
        "runtime_flag_source": decision.source,
        "provider_calls": 0,
        "provider_status": "not_invoked",
        "formal_business_writes": 0,
        "db_business_writes": 0,
        "checkpoint_refs_only": True,
        "checkpoint_refs_are_business_facts": False,
        "rollback_safe": True,
        "legacy_direct_path_retained_when_disabled": True,
        "sanitized": True,
        "input_refs": command.input_refs,
        "requested_outputs": command.requested_outputs,
        "request_digest": _stable_id(context.owner_id, context.run_id, context.ai_task_id, command.input_refs),
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


def run_polish_question_agent(
    context: AgentRunContext,
    command: AgentCommandEnvelope,
    flag_resolver: RuntimeFlagResolver | None = None,
) -> AgentRunResult:
    descriptor = build_polish_question_graph_descriptor()
    _validate_context(context, command, descriptor)
    resolver = flag_resolver or RuntimeFlagResolver()
    graph_decision = resolver.resolve_graph_flag(descriptor, actor_id=context.actor_id, caller="runner_entry")
    if not graph_decision.enabled:
        raise GraphDisabledError(f"graph disabled: {descriptor.graph_name}")
    provider_decision = resolver.is_real_provider_enabled(actor_id=context.actor_id)
    execution = execute_polish_question_agent(
        context=context,
        command=command,
        runtime_flag_source=graph_decision.source,
        provider_enabled=provider_decision.enabled,
        provider_flag_source=provider_decision.source,
    )
    payload = AgentCandidatePayload(
        candidate_ref=execution.candidate_ref,
        candidate_type="polish_question_candidate",
        payload_schema_id="polish_question_candidate.v1",
        payload=execution.candidate,
        status="accepted" if execution.metadata["validator_result"]["passed"] is True else "blocked",
        trace_refs=execution.trace_refs,
        validation_refs=tuple(ref for ref in execution.trace_refs if ref.startswith("validation_ref_")),
        low_confidence_flags=tuple(execution.candidate.get("low_confidence_flags", ())),
    )
    return AgentRunResult(
        run_id=context.run_id,
        status=execution.status,
        output_refs=(execution.result_ref, execution.candidate_ref),
        trace_refs=execution.trace_refs,
        interrupt_refs=(),
        formal_refs=(),
        candidate_payloads=(payload,),
        metadata=execution.metadata,
    )


def execute_polish_question_agent(
    *,
    context: AgentRunContext,
    command: AgentCommandEnvelope,
    runtime_flag_source: str,
    provider_enabled: bool,
    provider_flag_source: str,
    config: PolishQuestionAgentConfig | None = None,
    provider_draft_operation: Any | None = None,
) -> PolishQuestionAgentExecution:
    resolved_config = config or PolishQuestionAgentConfig()
    started_at = perf_counter()
    deadline_at = started_at + resolved_config.timeout_seconds
    phase_results: list[dict[str, Any]] = []
    tool_results: list[dict[str, Any]] = []
    request_digest = _stable_id(context.owner_id, context.run_id, context.ai_task_id, command.input_refs)
    provider_status = "enabled" if provider_enabled else "disabled"
    fallback_reason = None if provider_enabled else "provider_disabled_deterministic_drafting_tool"

    retrieved_context = _execute_agent_tool(
        phase="plan_task",
        tool_name="context_retrieval",
        input_payload={"request_digest": request_digest, "input_ref_count": len(command.input_refs)},
        operation=lambda: _tool_context_retrieval(command),
        config=resolved_config,
        deadline_at=deadline_at,
        phase_results=phase_results,
        tool_results=tool_results,
    )
    selected_evidence = _execute_agent_tool(
        phase="retrieve_context",
        tool_name="evidence_selection",
        input_payload={"context_ref": retrieved_context["output_ref"]},
        operation=lambda: _tool_evidence_selection(
            session_ref=str(retrieved_context["session_ref"]),
            context_payload=retrieved_context,
        ),
        config=resolved_config,
        deadline_at=deadline_at,
        phase_results=phase_results,
        tool_results=tool_results,
    )
    drafted_question = _execute_agent_tool(
        phase="draft_question",
        tool_name="question_drafting",
        input_payload={"scenario_ref": selected_evidence["scenario_ref"]},
        operation=lambda: _tool_question_drafting(
            context=context,
            command=command,
            session_ref=str(retrieved_context["session_ref"]),
            progress_node_ref=_optional_text(retrieved_context.get("progress_node_ref")),
            context_digest=_optional_text(retrieved_context.get("context_digest")),
            scenario=selected_evidence["scenario"],
            retrieved_context=retrieved_context,
            provider_enabled=provider_enabled,
            provider_draft_operation=provider_draft_operation,
        ),
        config=resolved_config,
        deadline_at=deadline_at,
        phase_results=phase_results,
        tool_results=tool_results,
    )
    validation = _execute_agent_tool(
        phase="validate_grounding",
        tool_name="grounding_validation",
        input_payload={"candidate_ref": drafted_question["candidate"]["candidate_ref"]},
        operation=lambda: _tool_grounding_validation(drafted_question["candidate"]),
        config=resolved_config,
        deadline_at=deadline_at,
        phase_results=phase_results,
        tool_results=tool_results,
    )
    repaired = _execute_repair_or_retry_phase(
        validation=validation,
        candidate=drafted_question["candidate"],
        config=resolved_config,
        deadline_at=deadline_at,
        phase_results=phase_results,
    )
    validation = repaired["validation"]
    persisted_candidate = _execute_agent_tool(
        phase="persist_candidate",
        tool_name="candidate_persistence",
        input_payload={"candidate_ref": repaired["candidate"]["candidate_ref"]},
        operation=lambda: _tool_candidate_persistence(repaired["candidate"], validation["validator_result"]),
        config=resolved_config,
        deadline_at=deadline_at,
        phase_results=phase_results,
        tool_results=tool_results,
    )
    finalized = _execute_finalize_phase(
        candidate=persisted_candidate["candidate"],
        config=resolved_config,
        deadline_at=deadline_at,
        phase_results=phase_results,
    )

    validator_result = validation["validator_result"]
    candidate = dict(finalized["candidate"])
    question_metadata = dict(candidate.get("question_metadata") if isinstance(candidate.get("question_metadata"), dict) else {})
    question_metadata.update(
        {
            "llm_generation_mode": "deterministic_agent_fallback" if not provider_enabled else "agent_provider_path",
            "fallback_reason": fallback_reason,
            "fallback_visible": fallback_reason is not None,
            "provider_status": provider_status,
            "phase_results": phase_results,
            "tool_results": tool_results,
            "validator_result": validator_result,
            "max_agent_steps": resolved_config.max_agent_steps,
            "max_retries": resolved_config.max_retries,
            "timeout_seconds": resolved_config.timeout_seconds,
            "backoff_seconds": resolved_config.backoff_seconds,
        }
    )
    candidate["question_metadata"] = sanitize_payload(question_metadata)
    trace_refs = tuple(
        _unique(
            [
                *[str(ref) for ref in candidate.get("trace_refs", ()) if str(ref).strip()],
                finalized["finalize_ref"],
            ]
        )
    )
    result_ref = "question_result_ref_" + _stable_id(context.owner_id, context.run_id, candidate["candidate_ref"])
    status = "agent_orchestration_succeeded" if validator_result.get("passed") is True else "agent_orchestration_blocked"
    metadata = {
        "graph_name": POLISH_QUESTION_GRAPH_NAME,
        "graph_version": POLISH_QUESTION_GRAPH_VERSION,
        "status": status,
        "runtime_flag_key": POLISH_QUESTION_GRAPH_FLAG,
        "runtime_flag_source": runtime_flag_source,
        "provider_flag_key": POLISH_QUESTION_PROVIDER_FLAG,
        "provider_status": provider_status,
        "provider_flag_source": provider_flag_source,
        "provider_calls": 0 if not provider_enabled else 1,
        "fallback_reason": fallback_reason,
        "fallback_visible": fallback_reason is not None,
        "request_digest": request_digest,
        "agent_phases": POLISH_QUESTION_AGENT_PHASES,
        "tool_schema_refs": tuple(schema.input_schema_id for schema in TOOL_SCHEMAS),
        "phase_results": phase_results,
        "tool_results": tool_results,
        "validator_result": validator_result,
        "max_agent_steps": resolved_config.max_agent_steps,
        "max_retries": resolved_config.max_retries,
        "timeout_seconds": resolved_config.timeout_seconds,
        "backoff_seconds": resolved_config.backoff_seconds,
        "latency_ms": round((perf_counter() - started_at) * 1000, 3),
        "output_refs": {"result_refs": [result_ref], "candidate_refs": [candidate["candidate_ref"]], "formal_refs": []},
        "trace_refs": {"validation_refs": [ref for ref in trace_refs if ref.startswith("validation_ref_")]},
        "db_business_writes": 0,
        "formal_business_writes": 0,
        "counters": {
            "provider_calls": 0 if not provider_enabled else 1,
            "db_business_writes": 0,
            "formal_business_writes": 0,
        },
        "checkpoint_refs_are_business_facts": False,
        "sanitized": True,
        "accepted_candidate_payload": validator_result.get("passed") is True,
    }
    return PolishQuestionAgentExecution(
        status=status,
        candidate=sanitize_payload(candidate),
        result_ref=result_ref,
        candidate_ref=str(candidate["candidate_ref"]),
        trace_refs=trace_refs,
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
    progress_node_ref: str | None = None,
    context_digest: str | None = None,
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
        "question_sources": _question_sources_from_scenario(scenario, evidence_refs),
        "progress_node_ref": progress_node_ref,
        "evidence_refs": evidence_refs,
        "context_digest": context_digest
        or _stable_id(session_ref, scenario_title, json.dumps(evidence_refs, sort_keys=True)),
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


def build_polish_question_candidate_from_draft(
    *,
    owner_id: str,
    run_id: str,
    ai_task_id: str,
    session_ref: str,
    draft: Any,
    scenario: dict[str, Any],
    provider_trace_refs: tuple[str, ...] = (),
) -> dict[str, Any]:
    evidence_refs = tuple(str(ref) for ref in draft.evidence_refs if str(ref).strip())
    scenario_payload = {
        **scenario,
        "source_refs": evidence_refs or tuple(scenario.get("source_refs", ())),
    }
    candidate_ref = "question_candidate_ref_" + _stable_id(
        owner_id,
        run_id,
        ai_task_id,
        session_ref,
        draft.progress_node_ref,
        draft.context_digest,
        draft.question_text,
        evidence_refs,
    )
    validation_ref = "validation_ref_" + _stable_id(candidate_ref, evidence_refs)
    question_metadata = dict(draft.question_metadata)
    question_metadata.update(
        {
            "provider_path": "graph_question_generation_service",
            "context_source": scenario.get("context_source"),
            "context_source_version": scenario.get("context_source_version"),
            "repository_backed_context": bool(scenario.get("repository_backed_context")),
            "provider_calls": 1,
        }
    )
    candidate = {
        "candidate_ref": candidate_ref,
        "scenario": scenario_payload,
        "question_text": draft.question_text,
        "question_pattern": draft.question_pattern or "provider_structured_json",
        "question_sources": tuple(_source_payload(source) for source in draft.question_sources),
        "progress_node_ref": draft.progress_node_ref,
        "evidence_refs": evidence_refs,
        "context_digest": draft.context_digest
        or _stable_id(session_ref, draft.progress_node_ref, evidence_refs),
        "source_availability": question_metadata.get("source_availability"),
        "confidence_level": draft.confidence_level or question_metadata.get("confidence_level") or "medium",
        "low_confidence_flags": tuple(draft.low_confidence_flags),
        "trace_refs": tuple(_unique((*provider_trace_refs, candidate_ref, validation_ref))),
        "question_metadata": question_metadata,
        "sanitized": True,
    }
    candidate["quality_gate"] = question_candidate_quality_gate(candidate)
    return sanitize_payload(candidate)


def build_polish_question_persistence_plan(
    *,
    owner_id: str,
    actor_id: str,
    session_id: str,
    ai_task_id: str,
    agent_run_id: str,
    candidate: dict[str, Any],
    progress_node_ref: str | None,
    trace_refs: tuple[str, ...],
) -> QuestionResultWritePlan:
    return build_question_result_write_plan(
        owner_id=owner_id,
        actor_id=actor_id,
        session_id=session_id,
        ai_task_id=ai_task_id,
        agent_run_id=agent_run_id,
        candidate=candidate,
        progress_node_ref=progress_node_ref,
        trace_refs=trace_refs,
        contract_ids=_LEGACY_PROMPT_CONTRACT_IDS,
    )


def question_candidate_quality_gate(candidate: dict[str, Any]) -> dict[str, Any]:
    blocking_reasons: list[str] = []
    low_confidence_reasons: list[str] = []
    scenario = candidate.get("scenario") if isinstance(candidate.get("scenario"), dict) else {}
    question_text = str(candidate.get("question_text", ""))
    evidence_refs = tuple(candidate.get("evidence_refs", ()))
    allowed_entities = tuple(str(entity) for entity in scenario.get("allowed_entities", ()) if str(entity).strip())
    forbidden_entities = tuple(str(entity) for entity in scenario.get("forbidden_entities", ()) if str(entity).strip())
    detected_entities = tuple(
        entity for entity in (*allowed_entities, *forbidden_entities) if _contains_entity(question_text, entity)
    )

    if not evidence_refs:
        blocking_reasons.append("missing_evidence_refs")
    if _has_raw_payload_leak(candidate):
        blocking_reasons.append("raw_payload_leak")
    if any(_contains_entity(question_text, entity) for entity in forbidden_entities):
        blocking_reasons.append("cross_evidence_scenario_mixing")
    if _has_unsupported_business_entity(detected_entities, allowed_entities):
        blocking_reasons.append("unsupported_business_entity")
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
            "source_contamination",
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
        progress_node_ref=_progress_node_ref_from_command(command),
        context_digest=str(metadata.get("context_digest") or ""),
    )
    quality_gate = candidate["quality_gate"]
    output_refs = (candidate["candidate_ref"],) if quality_gate["passed"] else ()
    result_metadata = {
        "graph_name": descriptor.graph_name,
        "graph_version": descriptor.graph_version,
        "readonly_parity_version": POLISH_QUESTION_READONLY_PARITY_VERSION,
        "persistence_handoff_version": POLISH_QUESTION_PERSISTENCE_VERSION,
        "runtime_flag_key": descriptor.runtime_flag_key,
        "runtime_flag_source": decision.source,
        "agent_phases": POLISH_QUESTION_AGENT_PHASES,
        "tool_schema_refs": tuple(schema.input_schema_id for schema in TOOL_SCHEMAS),
        "max_agent_steps": MAX_AGENT_STEPS,
        "max_retries": MAX_RETRIES,
        "timeout_seconds": QUESTION_AGENT_TIMEOUT_SECONDS,
        "backoff_seconds": QUESTION_AGENT_BACKOFF_SECONDS,
        "readonly_parity": True,
        "provider_calls": 0,
        "provider_status": "not_invoked",
        "db_business_writes": 0,
        "formal_business_writes": 0,
        "scenario_derivation": "dynamic_evidence_based",
        "request_digest": _stable_id(context.owner_id, context.run_id, context.ai_task_id, command.input_refs),
        "validator_result": quality_gate,
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


def _execute_agent_tool(
    *,
    phase: str,
    tool_name: str,
    input_payload: dict[str, Any],
    operation: Any,
    config: PolishQuestionAgentConfig,
    deadline_at: float,
    phase_results: list[dict[str, Any]],
    tool_results: list[dict[str, Any]],
) -> dict[str, Any]:
    _ensure_agent_can_continue(phase_results, config=config, deadline_at=deadline_at)
    schema = _tool_schema(tool_name)
    started_at = perf_counter()
    attempts = 0
    last_error: str | None = None
    while attempts <= config.max_retries:
        attempts += 1
        input_ref = _stable_id(phase, input_payload)
        LogUtil.agent_runtime_step(
            task_type=POLISH_QUESTION_TRACE_TASK_TYPE,
            graph_name=POLISH_QUESTION_GRAPH_NAME,
            phase=phase,
            tool_name=tool_name,
            status="started",
            attempt=attempts,
            max_attempts=config.max_retries + 1,
            max_agent_steps=config.max_agent_steps,
            timeout_seconds=config.timeout_seconds,
            input_ref=input_ref,
        )
        try:
            output = _run_operation_with_timeout(
                operation,
                tool_name=tool_name,
                deadline_at=deadline_at,
                timeout_seconds=float(schema.timeout_seconds),
            )
            if not isinstance(output, dict):
                raise RuntimeValidationError(f"{tool_name} returned invalid output")
            output_ref = str(output.get("output_ref") or f"{tool_name}_ref_{attempts}")
            latency_ms = round((perf_counter() - started_at) * 1000, 3)
            tool_result = {
                "tool_name": tool_name,
                "status": "succeeded",
                "input_schema_id": schema.input_schema_id,
                "output_schema_id": schema.output_schema_id,
                "input_ref": input_ref,
                "output_ref": output_ref,
                "attempts": attempts,
                "latency_ms": latency_ms,
            }
            tool_results.append(tool_result)
            phase_results.append(
                {
                    "phase": phase,
                    "status": "succeeded",
                    "tool_name": tool_name,
                    "input_ref": input_ref,
                    "output_ref": output_ref,
                    "attempts": attempts,
                    "latency_ms": latency_ms,
                    "error": None,
                }
            )
            LogUtil.agent_runtime_step(
                task_type=POLISH_QUESTION_TRACE_TASK_TYPE,
                graph_name=POLISH_QUESTION_GRAPH_NAME,
                phase=phase,
                tool_name=tool_name,
                status="succeeded",
                attempt=attempts,
                max_attempts=config.max_retries + 1,
                max_agent_steps=config.max_agent_steps,
                timeout_seconds=config.timeout_seconds,
                duration_ms=latency_ms,
                input_ref=input_ref,
                output_ref=output_ref,
            )
            return output
        except Exception as exc:
            last_error = exc.__class__.__name__
            if isinstance(exc, RuntimePolicyError):
                _record_tool_failure(
                    phase=phase,
                    tool_name=tool_name,
                    schema=schema,
                    input_ref=input_ref,
                    attempts=attempts,
                    started_at=started_at,
                    error_type=last_error,
                    phase_results=phase_results,
                    tool_results=tool_results,
                    config=config,
                )
                raise
            if attempts > config.max_retries or perf_counter() >= deadline_at:
                latency_ms = round((perf_counter() - started_at) * 1000, 3)
                _record_tool_failure(
                    phase=phase,
                    tool_name=tool_name,
                    schema=schema,
                    input_ref=input_ref,
                    attempts=attempts,
                    started_at=started_at,
                    error_type=last_error,
                    phase_results=phase_results,
                    tool_results=tool_results,
                    config=config,
                    latency_ms=latency_ms,
                )
                if last_error == "TimeoutError":
                    raise RuntimeValidationError(f"{tool_name} timed out") from exc
                raise RuntimeValidationError(f"{tool_name} failed after {attempts} attempt(s): {last_error}") from exc
            LogUtil.agent_runtime_step(
                task_type=POLISH_QUESTION_TRACE_TASK_TYPE,
                graph_name=POLISH_QUESTION_GRAPH_NAME,
                phase=phase,
                tool_name=tool_name,
                status="retry_scheduled",
                attempt=attempts,
                max_attempts=config.max_retries + 1,
                max_agent_steps=config.max_agent_steps,
                timeout_seconds=config.timeout_seconds,
                retry_delay_seconds=config.backoff_seconds,
                duration_ms=round((perf_counter() - started_at) * 1000, 3),
                input_ref=input_ref,
                error_type=last_error,
            )
            sleep(config.backoff_seconds)

    raise RuntimeValidationError(f"{tool_name} exhausted retry attempts")


def _run_operation_with_timeout(
    operation: Any,
    *,
    tool_name: str,
    deadline_at: float,
    timeout_seconds: float,
) -> dict[str, Any]:
    remaining_seconds = min(timeout_seconds, max(0.0, deadline_at - perf_counter()))
    if remaining_seconds <= 0:
        raise TimeoutError(f"{tool_name} timed out")
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(operation)
    try:
        result = future.result(timeout=remaining_seconds)
    except FutureTimeoutError as exc:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise TimeoutError(f"{tool_name} timed out") from exc
    except BaseException:
        executor.shutdown(wait=True, cancel_futures=False)
        raise
    else:
        executor.shutdown(wait=True, cancel_futures=False)
        return result


def _record_tool_failure(
    *,
    phase: str,
    tool_name: str,
    schema: PolishQuestionToolSchema,
    input_ref: str,
    attempts: int,
    started_at: float,
    error_type: str,
    phase_results: list[dict[str, Any]],
    tool_results: list[dict[str, Any]],
    config: PolishQuestionAgentConfig,
    latency_ms: float | None = None,
) -> None:
    duration_ms = latency_ms if latency_ms is not None else round((perf_counter() - started_at) * 1000, 3)
    tool_results.append(
        {
            "tool_name": tool_name,
            "status": "failed",
            "input_schema_id": schema.input_schema_id,
            "output_schema_id": schema.output_schema_id,
            "input_ref": input_ref,
            "output_ref": None,
            "attempts": attempts,
            "latency_ms": duration_ms,
            "error": error_type,
        }
    )
    phase_results.append(
        {
            "phase": phase,
            "status": "failed",
            "tool_name": tool_name,
            "input_ref": input_ref,
            "output_ref": None,
            "attempts": attempts,
            "latency_ms": duration_ms,
            "retry_delay_seconds": config.backoff_seconds,
            "error": error_type,
        }
    )
    LogUtil.agent_runtime_step(
        task_type=POLISH_QUESTION_TRACE_TASK_TYPE,
        graph_name=POLISH_QUESTION_GRAPH_NAME,
        phase=phase,
        tool_name=tool_name,
        status="failed",
        attempt=attempts,
        max_attempts=config.max_retries + 1,
        max_agent_steps=config.max_agent_steps,
        timeout_seconds=config.timeout_seconds,
        duration_ms=duration_ms,
        input_ref=input_ref,
        error_type=error_type,
    )


def _execute_repair_or_retry_phase(
    *,
    validation: dict[str, Any],
    candidate: dict[str, Any],
    config: PolishQuestionAgentConfig,
    deadline_at: float,
    phase_results: list[dict[str, Any]],
) -> dict[str, Any]:
    _ensure_agent_can_continue(phase_results, config=config, deadline_at=deadline_at)
    validator_result = validation["validator_result"]
    if validator_result.get("passed") is True:
        status = "skipped"
        output_ref = "repair_ref_" + _stable_id(candidate.get("candidate_ref"), validator_result)
        phase_results.append(
            {
                "phase": "repair_or_retry",
                "status": status,
                "tool_name": None,
                "input_ref": str(validation.get("output_ref") or ""),
                "output_ref": output_ref,
                "attempts": 0,
                "latency_ms": 0.0,
                "retry_delay_seconds": config.backoff_seconds,
                "error": None,
            }
        )
        LogUtil.agent_runtime_step(
            task_type=POLISH_QUESTION_TRACE_TASK_TYPE,
            graph_name=POLISH_QUESTION_GRAPH_NAME,
            phase="repair_or_retry",
            status=status,
            attempt=0,
            max_attempts=config.max_retries + 1,
            max_agent_steps=config.max_agent_steps,
            timeout_seconds=config.timeout_seconds,
            retry_delay_seconds=config.backoff_seconds,
            input_ref=str(validation.get("output_ref") or ""),
            output_ref=output_ref,
            error_type=None,
        )
        return {"candidate": candidate, "validation": validation, "output_ref": output_ref}

    started_at = perf_counter()
    repaired_candidate = candidate
    repaired_validation = validation
    last_validator_result = validator_result
    max_attempts = max(0, config.max_retries)
    for attempt in range(1, max_attempts + 1):
        _ensure_agent_can_continue(phase_results, config=config, deadline_at=deadline_at)
        repaired_candidate = _repair_question_candidate(
            repaired_candidate,
            validator_result=last_validator_result,
            attempt=attempt,
        )
        last_validator_result = question_candidate_quality_gate(repaired_candidate)
        repaired_candidate["quality_gate"] = last_validator_result
        repaired_validation = {
            "output_ref": "validation_ref_"
            + _stable_id(repaired_candidate.get("candidate_ref"), last_validator_result),
            "validator_result": last_validator_result,
        }
        if last_validator_result.get("passed") is True:
            output_ref = "repair_ref_" + _stable_id(
                candidate.get("candidate_ref"), repaired_candidate.get("candidate_ref"), attempt
            )
            latency_ms = round((perf_counter() - started_at) * 1000, 3)
            phase_results.append(
                {
                    "phase": "repair_or_retry",
                    "status": "repaired",
                    "tool_name": None,
                    "input_ref": str(validation.get("output_ref") or ""),
                    "output_ref": output_ref,
                    "attempts": attempt,
                    "latency_ms": latency_ms,
                    "retry_delay_seconds": config.backoff_seconds,
                    "error": None,
                    "repair_strategy": "safe_grounding_transform",
                }
            )
            LogUtil.agent_runtime_step(
                task_type=POLISH_QUESTION_TRACE_TASK_TYPE,
                graph_name=POLISH_QUESTION_GRAPH_NAME,
                phase="repair_or_retry",
                status="repaired",
                attempt=attempt,
                max_attempts=config.max_retries + 1,
                max_agent_steps=config.max_agent_steps,
                timeout_seconds=config.timeout_seconds,
                retry_delay_seconds=config.backoff_seconds,
                duration_ms=latency_ms,
                input_ref=str(validation.get("output_ref") or ""),
                output_ref=output_ref,
            )
            return {
                "candidate": sanitize_payload(repaired_candidate),
                "validation": repaired_validation,
                "output_ref": output_ref,
            }
        sleep(config.backoff_seconds)

    status = "failed"
    output_ref = "repair_ref_" + _stable_id(candidate.get("candidate_ref"), validator_result)
    phase_results.append(
        {
            "phase": "repair_or_retry",
            "status": status,
            "tool_name": None,
            "input_ref": str(validation.get("output_ref") or ""),
            "output_ref": output_ref,
            "attempts": 0,
            "latency_ms": 0.0,
            "retry_delay_seconds": config.backoff_seconds,
            "error": "validator_blocked_candidate",
            "blocking_reasons": tuple(last_validator_result.get("blocking_reasons", ())),
        }
    )
    LogUtil.agent_runtime_step(
        task_type=POLISH_QUESTION_TRACE_TASK_TYPE,
        graph_name=POLISH_QUESTION_GRAPH_NAME,
        phase="repair_or_retry",
        status=status,
        attempt=0,
        max_attempts=config.max_retries + 1,
        max_agent_steps=config.max_agent_steps,
        timeout_seconds=config.timeout_seconds,
        retry_delay_seconds=config.backoff_seconds,
        input_ref=str(validation.get("output_ref") or ""),
        output_ref=output_ref,
        error_type="validator_blocked_candidate",
    )
    raise RuntimeValidationError("polish question candidate failed grounding validation after repair attempts")


def _execute_finalize_phase(
    *,
    candidate: dict[str, Any],
    config: PolishQuestionAgentConfig,
    deadline_at: float,
    phase_results: list[dict[str, Any]],
) -> dict[str, Any]:
    _ensure_agent_can_continue(phase_results, config=config, deadline_at=deadline_at)
    finalize_ref = "finalize_ref_" + _stable_id(candidate.get("candidate_ref"), candidate.get("context_digest"))
    phase_results.append(
        {
            "phase": "finalize",
            "status": "succeeded",
            "tool_name": None,
            "input_ref": str(candidate.get("candidate_ref") or ""),
            "output_ref": finalize_ref,
            "attempts": 1,
            "latency_ms": 0.0,
            "error": None,
        }
    )
    LogUtil.agent_runtime_step(
        task_type=POLISH_QUESTION_TRACE_TASK_TYPE,
        graph_name=POLISH_QUESTION_GRAPH_NAME,
        phase="finalize",
        status="succeeded",
        attempt=1,
        max_attempts=config.max_retries + 1,
        max_agent_steps=config.max_agent_steps,
        timeout_seconds=config.timeout_seconds,
        input_ref=str(candidate.get("candidate_ref") or ""),
        output_ref=finalize_ref,
    )
    return {"candidate": candidate, "finalize_ref": finalize_ref}


def _tool_context_retrieval(command: AgentCommandEnvelope) -> dict[str, Any]:
    snapshot = command.metadata.get("polish_question_context_snapshot")
    if isinstance(snapshot, dict):
        return _tool_context_retrieval_from_snapshot(command, snapshot)

    session_ref = str(command.input_refs[0]).strip()
    progress_node_ref = _progress_node_ref_from_command(command)
    completed_focus_refs = tuple(str(ref).strip() for ref in command.input_refs[2:] if str(ref).strip())
    metadata = command.metadata
    context_digest = str(metadata.get("context_digest") or metadata.get("request_digest") or "").strip()
    selected_summary = _safe_agent_summary(
        metadata.get("selected_progress_node_summary"),
        fallback="候选人项目表达场景" if progress_node_ref else "证据不足的打磨题场景",
    )
    selected_refs = _metadata_tuple(metadata.get("selected_evidence_refs"))
    if not selected_refs and progress_node_ref:
        selected_refs = (progress_node_ref,)
    output_ref = "context_ref_" + _stable_id(session_ref, progress_node_ref, context_digest, selected_refs)
    return {
        "output_ref": output_ref,
        "session_ref": session_ref,
        "progress_node_ref": progress_node_ref,
        "completed_focus_refs": completed_focus_refs,
        "selected_progress_node_summary": selected_summary,
        "selected_evidence_refs": selected_refs,
        "resume_evidence_summaries": _metadata_tuple(metadata.get("resume_evidence_summaries")),
        "job_requirement_summaries": _metadata_tuple(metadata.get("job_requirement_summaries")),
        "match_gap_summaries": _metadata_tuple(metadata.get("match_gap_summaries")),
        "history_feedback_summaries": _metadata_tuple(metadata.get("history_feedback_summaries")),
        "context_digest": context_digest,
    }


def _tool_context_retrieval_from_snapshot(
    command: AgentCommandEnvelope,
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    session_ref = str(command.input_refs[0]).strip()
    session_payload = snapshot.get("session") if isinstance(snapshot.get("session"), dict) else {}
    if session_payload and str(session_payload.get("session_id") or "").strip() != session_ref:
        raise RuntimeValidationError("polish question context snapshot session mismatch")
    progress_node_ref = (
        str(snapshot.get("requested_progress_node_ref") or "").strip()
        or _progress_node_ref_from_command(command)
    )
    progress_context = snapshot.get("progress_context") if isinstance(snapshot.get("progress_context"), dict) else {}
    progress_tree_plan = (
        snapshot.get("progress_tree_plan") if isinstance(snapshot.get("progress_tree_plan"), dict) else {}
    )
    progress_tree_state = (
        snapshot.get("progress_tree_state") if isinstance(snapshot.get("progress_tree_state"), dict) else {}
    )
    selected_summary = _snapshot_progress_node_summary(progress_tree_plan, progress_tree_state, progress_node_ref)
    evidence_summaries = tuple(
        item
        for item in snapshot.get("selected_evidence_summaries", ())
        if isinstance(item, dict) and str(item.get("ref") or "").strip()
    )
    selected_refs = tuple(str(item.get("ref")) for item in evidence_summaries)
    output_ref = "context_ref_" + _stable_id(
        session_ref,
        progress_node_ref,
        snapshot.get("context_digest"),
        selected_refs,
        snapshot.get("context_source"),
    )
    return {
        "output_ref": output_ref,
        "session_ref": session_ref,
        "progress_node_ref": progress_node_ref,
        "completed_focus_refs": tuple(
            str(ref).strip() for ref in snapshot.get("completed_focus_refs", ()) if str(ref).strip()
        ),
        "selected_progress_node_summary": selected_summary,
        "selected_evidence_refs": selected_refs,
        "resume_evidence_summaries": tuple(
            item for item in evidence_summaries if str(item.get("source_type") or "").startswith("resume")
        ),
        "job_requirement_summaries": tuple(
            item for item in evidence_summaries if item.get("source_type") == "job_requirement"
        ),
        "match_gap_summaries": tuple(
            item for item in evidence_summaries if item.get("source_type") in {"match_gap", "match_focus"}
        ),
        "history_feedback_summaries": tuple(
            item for item in evidence_summaries if item.get("source_type") in {"history_feedback", "turn_feedback"}
        ),
        "context_digest": str(
            snapshot.get("context_digest")
            or progress_tree_plan.get("context_digest")
            or progress_context.get("content_digest")
            or ""
        ),
        "context_source": str(snapshot.get("context_source") or "use_case_repository_snapshot"),
        "context_source_version": str(snapshot.get("context_source_version") or ""),
        "repository_backed": True,
        "source_refs": {
            "session_ref": session_ref,
            "resume_version_id": str(session_payload.get("resume_version_id") or ""),
            "job_version_id": str(session_payload.get("job_version_id") or ""),
        },
    }


def _tool_evidence_selection(*, session_ref: str, context_payload: dict[str, Any]) -> dict[str, Any]:
    progress_node_ref = _optional_text(context_payload.get("progress_node_ref"))
    selected_refs = tuple(context_payload.get("selected_evidence_refs") or ())
    selected_summary = _safe_agent_summary(
        context_payload.get("selected_progress_node_summary"),
        fallback="候选人项目表达场景",
    )
    resume_summaries = tuple(context_payload.get("resume_evidence_summaries") or ())
    if not resume_summaries and selected_refs:
        resume_summaries = (
            {
                "ref": selected_refs[0],
                "summary": selected_summary,
                "source_type": "resume_project",
            },
        )
    scenario = derive_question_scenario(
        session_ref=session_ref,
        selected_progress_node_summary=selected_summary,
        selected_evidence_refs=selected_refs,
        resume_evidence_summaries=resume_summaries,
        job_requirement_summaries=tuple(context_payload.get("job_requirement_summaries") or ()),
        match_gap_summaries=tuple(context_payload.get("match_gap_summaries") or ()),
        history_feedback_summaries=tuple(context_payload.get("history_feedback_summaries") or ()),
        completed_focus_refs=tuple(context_payload.get("completed_focus_refs") or ()),
    )
    if context_payload.get("context_source"):
        scenario = {
            **scenario,
            "context_source": context_payload.get("context_source"),
            "context_source_version": context_payload.get("context_source_version"),
            "repository_backed_context": bool(context_payload.get("repository_backed")),
            "source_refs": context_payload.get("source_refs") or {},
        }
    return {
        "output_ref": "scenario_ref_" + _stable_id(session_ref, progress_node_ref, selected_refs),
        "scenario_ref": "scenario_ref_" + _stable_id(session_ref, progress_node_ref, scenario.get("scenario_title")),
        "scenario": scenario,
    }


def _tool_question_drafting(
    *,
    context: AgentRunContext,
    command: AgentCommandEnvelope,
    session_ref: str,
    progress_node_ref: str | None,
    context_digest: str | None,
    scenario: dict[str, Any],
    retrieved_context: dict[str, Any],
    provider_enabled: bool,
    provider_draft_operation: Any | None = None,
) -> dict[str, Any]:
    if provider_enabled:
        if provider_draft_operation is None:
            raise RuntimeValidationError("polish question provider path is enabled but no provider is configured")
        provider_output = provider_draft_operation(
            context=context,
            command=command,
            retrieved_context=retrieved_context,
            scenario=scenario,
        )
        if not isinstance(provider_output, dict):
            raise RuntimeValidationError("polish question provider returned invalid candidate")
        candidate = dict(provider_output.get("candidate") or provider_output)
        if not isinstance(candidate, dict) or not str(candidate.get("candidate_ref") or "").strip():
            raise RuntimeValidationError("polish question provider candidate_ref is required")
        candidate["quality_gate"] = question_candidate_quality_gate(candidate)
        return {
            "output_ref": str(candidate["candidate_ref"]),
            "candidate": sanitize_payload(candidate),
        }

    candidate = build_polish_question_candidate_readonly(
        owner_id=context.owner_id,
        run_id=context.run_id,
        ai_task_id=context.ai_task_id,
        session_ref=session_ref,
        scenario=scenario,
        progress_node_ref=progress_node_ref,
        context_digest=context_digest or "",
    )
    return {
        "output_ref": str(candidate["candidate_ref"]),
        "candidate": candidate,
    }


def _tool_grounding_validation(candidate: dict[str, Any]) -> dict[str, Any]:
    validator_result = question_candidate_quality_gate(candidate)
    candidate["quality_gate"] = validator_result
    return {
        "output_ref": "validation_ref_" + _stable_id(candidate.get("candidate_ref"), validator_result),
        "validator_result": validator_result,
    }


def _tool_candidate_persistence(candidate: dict[str, Any], validator_result: dict[str, Any]) -> dict[str, Any]:
    quality_gate = dict(validator_result)
    quality_gate.setdefault("status", "accepted" if validator_result.get("passed") is True else "blocked")
    persisted_candidate = sanitize_payload({**candidate, "quality_gate": quality_gate})
    return {
        "output_ref": "candidate_persistence_ref_" + _stable_id(candidate.get("candidate_ref"), quality_gate),
        "candidate": persisted_candidate,
    }


def _repair_question_candidate(
    candidate: dict[str, Any],
    *,
    validator_result: dict[str, Any],
    attempt: int,
) -> dict[str, Any]:
    scenario = dict(candidate.get("scenario") if isinstance(candidate.get("scenario"), dict) else {})
    repaired = sanitize_payload(dict(candidate))
    repaired["scenario"] = scenario
    source_refs = tuple(str(ref) for ref in scenario.get("source_refs", ()) if str(ref).strip())
    if not repaired.get("evidence_refs") and source_refs:
        repaired["evidence_refs"] = source_refs
    blocking_reasons = set(str(reason) for reason in validator_result.get("blocking_reasons", ()))
    if blocking_reasons & {
        "cross_evidence_scenario_mixing",
        "unsupported_business_entity",
        "job_gap_claimed_as_project_experience",
        "raw_payload_leak",
    }:
        repaired["question_text"] = _candidate_question_text(scenario)
    repaired["candidate_ref"] = "question_candidate_ref_" + _stable_id(
        candidate.get("candidate_ref"),
        "repair",
        attempt,
        repaired.get("question_text"),
        repaired.get("evidence_refs"),
    )
    trace_refs = tuple(str(ref) for ref in repaired.get("trace_refs", ()) if str(ref).strip())
    repaired["trace_refs"] = _unique((*trace_refs, "repair_ref_" + _stable_id(repaired["candidate_ref"], attempt)))
    metadata = dict(
        repaired.get("question_metadata") if isinstance(repaired.get("question_metadata"), dict) else {}
    )
    metadata.update(
        {
            "repair_strategy": "safe_grounding_transform",
            "repair_attempts": attempt,
            "repaired_from_candidate_ref": str(candidate.get("candidate_ref") or ""),
            "repair_blocking_reasons": tuple(blocking_reasons),
        }
    )
    repaired["question_metadata"] = metadata
    return sanitize_payload(repaired)


def _ensure_agent_can_continue(
    phase_results: list[dict[str, Any]],
    *,
    config: PolishQuestionAgentConfig,
    deadline_at: float,
) -> None:
    if len(phase_results) >= config.max_agent_steps:
        raise RuntimeValidationError("polish question agent exceeded max_agent_steps")
    if perf_counter() > deadline_at:
        raise RuntimeValidationError("polish question agent deadline exceeded")


def _tool_schema(tool_name: str) -> PolishQuestionToolSchema:
    for schema in TOOL_SCHEMAS:
        if schema.tool_name == tool_name:
            return schema
    raise RuntimeValidationError(f"unknown polish question tool: {tool_name}")


def _metadata_tuple(value: object) -> tuple[Any, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()


def _snapshot_progress_node_summary(
    progress_tree_plan: dict[str, Any],
    progress_tree_state: dict[str, Any],
    progress_node_ref: str | None,
) -> str:
    node = _find_snapshot_progress_node(progress_tree_plan.get("nodes"), progress_node_ref)
    if node is None:
        priority = progress_tree_state.get("current_priority")
        node = priority if isinstance(priority, dict) else {}
    return _safe_agent_summary(
        "；".join(
            str(part)
            for part in (
                node.get("display_title"),
                node.get("title"),
                node.get("exam_point"),
                node.get("expected_capability"),
            )
            if str(part or "").strip()
        ),
        fallback="证据不足的打磨题场景",
    )


def _find_snapshot_progress_node(nodes: object, progress_node_ref: str | None) -> dict[str, Any] | None:
    if not isinstance(nodes, list):
        return None
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if progress_node_ref and str(node.get("progress_node_ref") or "").strip() == progress_node_ref:
            return node
        child = _find_snapshot_progress_node(node.get("children"), progress_node_ref)
        if child is not None:
            return child
    return None


def _source_payload(source: Any) -> dict[str, Any]:
    if isinstance(source, dict):
        return source
    try:
        return asdict(source)
    except TypeError:
        return {}


def _safe_agent_summary(value: object, *, fallback: str) -> str:
    text = str(value or "").strip()
    if not text or contains_sensitive_payload(text):
        return fallback
    return text[:240]


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _validate_context(
    context: AgentRunContext,
    command: AgentCommandEnvelope,
    descriptor: "GraphDescriptor",
) -> None:
    if command != context.command:
        raise RuntimePolicyError("command must match context command")
    if context.graph_name != descriptor.graph_name:
        raise RuntimePolicyError("context graph does not match polish question agent")
    if context.graph_version != descriptor.graph_version:
        raise RuntimePolicyError("context graph version does not match polish question agent")
    if command.entrypoint not in descriptor.supported_entrypoints:
        raise RuntimeValidationError(f"unsupported entrypoint: {command.entrypoint}")
    if not command.input_refs:
        raise RuntimeValidationError("polish question agent requires a session ref")
    session_ref = str(command.input_refs[0]).strip()
    if not session_ref.startswith("session_"):
        raise RuntimeValidationError("polish question agent accepts refs only")
    if contains_sensitive_payload(command.input_refs) or contains_sensitive_payload(command.metadata):
        raise RuntimeValidationError("polish question agent accepts refs and sanitized metadata only")

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


def _progress_node_ref_from_command(command: AgentCommandEnvelope) -> str | None:
    if len(command.input_refs) < 2:
        return None
    value = str(command.input_refs[1]).strip()
    return value or None


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
        if str(item.get("source_type", "")).startswith(("history", "turn_")):
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


def _question_sources_from_scenario(
    scenario: dict[str, Any], evidence_refs: tuple[str, ...]
) -> tuple[dict[str, Any], ...]:
    source_types = tuple(str(value) for value in scenario.get("source_types", ()) if str(value).strip())
    summary = str(scenario.get("scenario_summary") or "").strip()
    return tuple(
        {
            "index": index,
            "source_type": source_types[index - 1] if index <= len(source_types) else "evidence",
            "title": str(scenario.get("scenario_title") or ref),
            "excerpt": summary,
            "ref_id": ref,
            "availability": "available",
        }
        for index, ref in enumerate(evidence_refs, start=1)
    )


def _extract_entities(text: object) -> tuple[str, ...]:
    value = str(text)
    found: list[str] = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_+.-]{1,}|[\u4e00-\u9fff]{2,18}", value):
        for normalized in _candidate_entity_terms(token):
            if normalized in _GENERIC_TERM_STOPWORDS:
                continue
            found.append(normalized)
            if len(found) >= 8:
                break
        if len(found) >= 8:
            break
    return tuple(_unique(found))


def _candidate_entity_terms(token: str) -> tuple[str, ...]:
    normalized = token.strip()
    normalized = re.sub(r"^(我|本人|我们)?(负责|参与|主导|做过|实现|落地|要求|具备|需要|覆盖)", "", normalized)
    normalized = normalized.replace("系统中的", "、").replace("项目中的", "、").replace("场景下的", "、")
    parts = re.split(r"[、和与及/，。；,;]+", normalized)
    result: list[str] = []
    for part in parts:
        clean = part.strip()
        if len(clean) < 2:
            continue
        result.append(clean[:18])
    return tuple(result)


def _primary_group(entities: tuple[str, ...]) -> str:
    return _normalize_entity(entities[0]) if entities else ""


def _has_unsupported_business_entity(detected_entities: tuple[str, ...], allowed_entities: tuple[str, ...]) -> bool:
    allowed = {_normalize_entity(entity) for entity in allowed_entities}
    for entity in detected_entities:
        if _normalize_entity(entity) in allowed:
            continue
        if len(entity.strip()) >= 2:
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


def _normalize_entity(value: object) -> str:
    return re.sub(r"\s+", "", str(value).strip().lower())


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
