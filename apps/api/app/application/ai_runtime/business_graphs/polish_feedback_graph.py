"""Default-off PR5 Polish feedback business graph skeleton."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.application.agents.contracts import AgentRuntimeLoopPolicy, ToolDefinition
from app.application.agents.definitions.common import FORBIDDEN_DATA
from app.application.agents.registry import RegistryValidationError, ToolRegistry
from app.application.ai_runtime.contracts import (
    AgentCommandEnvelope,
    AgentReplayResult,
    AgentRunContext,
    AgentRunResult,
    GraphDisabledError,
    RuntimePolicyError,
    RuntimeValidationError,
    contains_sensitive_payload,
    sanitize_payload,
)
from app.application.ai_runtime.side_effect_guard import AgentSideEffectGuard
from app.application.ai_runtime.llm_trace import LlmTraceContext, PersistedLlmTransport
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.application.llm.provider_boundary import build_validated_transport_request
from app.application.llm.types import LlmTransportRequest

if TYPE_CHECKING:
    from app.application.ai_runtime.registry import GraphDescriptor


POLISH_FEEDBACK_GRAPH_NAME = "polish_feedback_graph"
POLISH_FEEDBACK_GRAPH_VERSION = "pr5-skeleton"
POLISH_FEEDBACK_FAKE_RUNTIME_VERSION = "pr6-fake-runtime"
POLISH_FEEDBACK_READONLY_PARITY_VERSION = "pr7-readonly-parity"
POLISH_FEEDBACK_TRACE_GATE_PROMPT_VERSION = "polish_feedback_trace_gate_v1"
POLISH_FEEDBACK_TRACE_GATE_SCHEMA_ID = "polish_feedback_trace_request.v1"
POLISH_FEEDBACK_TRACE_GATE_NODE_NAME = "polish_feedback_trace_gate"
POLISH_FEEDBACK_TRACE_TASK_TYPE = "polish_feedback_generation"
POLISH_FEEDBACK_GRAPH_FLAG = "AIFI_GRAPH_POLISH_FEEDBACK_ENABLED"
POLISH_FEEDBACK_AGENT_ID = "polish_feedback_agent"
_RUNTIME_TOOL_PERMISSION_SCOPE = "owner"
_RUNTIME_TOOL_OWNER_SCOPE = "owner"

_DEFAULT_ENTRYPOINTS = ("start", "replay", "timeline", "cancel")
_SUPPORTED_OUTPUTS = ("result_refs", "candidate_refs", "suggestion_refs", "interrupt_refs")
_PR6_INPUT_REF_PREFIXES = (
    ("session_ref", "session_ref_"),
    ("question_ref", "question_ref_"),
    ("answer_ref", "answer_ref_"),
)
_PR6_ALLOWED_METADATA_KEYS = frozenset(
    {
        "task_type",
        "graph_name",
        "graph_version",
        "request_digest",
        "idempotency_key_hash",
        "idempotency_digest",
        "idempotency_ref",
        "runtime_loop_policy",
    }
)
_PR6_HITL_TRIGGER_REF_KEYS = {
    "formal_write_attempt_ref": ("formal_write_attempt", ("formal_write_attempt_ref_",)),
    "asset_conflict_ref": ("asset_conflict", ("asset_conflict_ref_",)),
    "low_confidence_formal_update_ref": (
        "low_confidence_formal_update",
        ("low_confidence_ref_", "low_confidence_formal_update_ref_"),
    ),
    "ambiguous_ownership_ref": ("ambiguous_ownership", ("ambiguous_ownership_ref_",)),
    "validation_failed_partial_result_ref": (
        "validation_failed_partial_result",
        ("validation_ref_", "validation_failed_partial_result_ref_"),
    ),
}
_PR6_FORBIDDEN_METADATA_KEYS = frozenset(
    {
        "question" + "_text",
        "answer" + "_text",
        "raw" + "_prompt",
        "raw" + "_completion",
        "provider" + "_payload",
        "checkpoint" + "_payload",
        "full" + "_source_body",
        "full" + "_resume",
        "full" + "_jd",
        "full" + "_answer",
        "hidden" + "_rubric",
        "api" + "_key",
        "to" + "ken",
        "coo" + "kie",
        "sec" + "ret",
    }
)
_PR7_FORBIDDEN_INPUT_KEYS = frozenset(
    {
        "question" + "_text",
        "answer" + "_text",
        "raw" + "_prompt",
        "raw" + "_completion",
        "provider" + "_payload",
        "checkpoint" + "_payload",
        "full" + "_resume",
        "full" + "_jd",
        "full" + "_answer",
        "hidden" + "_rubric",
        "api" + "_key",
        "to" + "ken",
        "coo" + "kie",
        "sec" + "ret",
    }
)
_PR8_ALLOWED_EVIDENCE_BUNDLE_KEYS = frozenset(
    {
        "session_ref",
        "question_ref",
        "answer_ref",
        "prior_answer_refs",
        "prior_feedback_refs",
        "rubric_summary_ref",
        "idempotency_digest",
        "question_digest",
        "answer_digest",
        "evidence_ref_ids",
        "validation_ref_ids",
        "low_confidence_ref_ids",
        "parity_result_ref",
    }
)
_PR8_FORBIDDEN_INPUT_KEYS = _PR7_FORBIDDEN_INPUT_KEYS | frozenset(
    {
        "raw" + "_llm_messages",
        "raw" + "_provider" + "_response",
        "source" + "_payload",
    }
)


@dataclass(frozen=True)
class PolishFeedbackTraceRequestPlan:
    trace_context: LlmTraceContext
    transport_request: LlmTransportRequest


def build_polish_feedback_graph_descriptor() -> "GraphDescriptor":
    from app.application.ai_runtime.registry import GraphDescriptor

    return GraphDescriptor(
        graph_name=POLISH_FEEDBACK_GRAPH_NAME,
        graph_version=POLISH_FEEDBACK_GRAPH_VERSION,
        capability="polish_feedback",
        lifecycle_status="placeholder",
        runtime_flag_key=POLISH_FEEDBACK_GRAPH_FLAG,
        default_enabled=False,
        supported_entrypoints=_DEFAULT_ENTRYPOINTS,
        supported_outputs=_SUPPORTED_OUTPUTS,
        prompt_contract_ids=("P-POLISH-FEEDBACK-001",),
        eval_suite_ids=("EVAL-POLISH-FEEDBACK-001",),
        runtime_max_steps=5,
        runtime_max_retries=1,
        runtime_timeout_seconds=20,
        runtime_stop_conditions=(
            "max_steps_exceeded",
            "timeout",
            "validation_failed",
            "tool_not_allowed",
            "formal_write_requested",
            "interrupt_required",
            "provider_failed",
        ),
        runtime_allowed_tools=(POLISH_FEEDBACK_TRACE_GATE_NODE_NAME,),
        runtime_allowed_callers=(POLISH_FEEDBACK_AGENT_ID,),
        runtime_side_effect_policy="candidate_write",
        resume_schema_ids={},
        interrupt_types=(),
        required_permissions=("owner",),
        visibility="owner_only",
        health_summary_refs=("health.polish_feedback.pr5_skeleton",),
        config_schema_ref="graph_config.polish_feedback.pr5_skeleton",
        implementation_pr="PR5",
        migration_status="skeleton_default_off_direct_path_retained",
        provider_enabled=False,
        formal_write_targets=(),
        db_business_write_targets=(),
        rollback_safe=True,
        disabled_behavior="legacy_direct_path_retained",
    )


def _build_runtime_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            tool_id="runtime_polish_feedback_polish_feedback_trace_gate",
            tool_name=POLISH_FEEDBACK_TRACE_GATE_NODE_NAME,
            input_schema_id=POLISH_FEEDBACK_TRACE_GATE_SCHEMA_ID,
            output_schema_id="polish_feedback_trace_gate.output.v1",
            permission_scope=_RUNTIME_TOOL_PERMISSION_SCOPE,
            owner_scope=_RUNTIME_TOOL_OWNER_SCOPE,
            side_effect_policy="candidate_write",
            timeout_seconds=20,
            retry_policy="max_retries:1",
            allowed_callers=(POLISH_FEEDBACK_AGENT_ID,),
            forbidden_data=FORBIDDEN_DATA,
            trace_events=("provider_trace_gate_planned", "provider_trace_gate_failed"),
        )
    )
    return registry


_RUNTIME_TOOL_REGISTRY = _build_runtime_tool_registry()
_RUNTIME_SIDE_EFFECT_GUARD = AgentSideEffectGuard()


def _runtime_loop_policy() -> AgentRuntimeLoopPolicy:
    descriptor = build_polish_feedback_graph_descriptor()
    try:
        return AgentRuntimeLoopPolicy(
            max_steps=descriptor.runtime_max_steps,
            max_retries=descriptor.runtime_max_retries,
            timeout_seconds=descriptor.runtime_timeout_seconds,
            stop_conditions=descriptor.runtime_stop_conditions,
            allowed_tools=descriptor.runtime_allowed_tools,
            allowed_callers=descriptor.runtime_allowed_callers,
            side_effect_policy=descriptor.runtime_side_effect_policy,
        )
    except ValueError as exc:
        raise RuntimePolicyError(f"invalid polish feedback runtime loop policy: {exc}") from exc


def _runtime_tool_definition(tool_name: str) -> ToolDefinition:
    try:
        return _RUNTIME_TOOL_REGISTRY.get(f"runtime_polish_feedback_{tool_name}")
    except RegistryValidationError as exc:
        raise RuntimePolicyError(f"tool_not_allowed: {tool_name}") from exc


def _authorize_trace_gate_tool_call(
    *, owner_id: str, input_refs: tuple[str, ...], payload: dict[str, Any]
) -> None:
    tool_name = POLISH_FEEDBACK_TRACE_GATE_NODE_NAME
    loop_policy = _runtime_loop_policy()
    if tool_name not in loop_policy.allowed_tools:
        raise RuntimePolicyError(f"tool_not_allowed: {tool_name}")
    if POLISH_FEEDBACK_AGENT_ID not in loop_policy.allowed_callers:
        raise RuntimePolicyError("caller not allowed for tool")
    tool_definition = _runtime_tool_definition(tool_name)
    _RUNTIME_SIDE_EFFECT_GUARD.authorize_tool_call(
        owner_id=owner_id,
        tool_name=tool_name,
        input_refs=input_refs,
        tool=tool_definition,
        caller_id=POLISH_FEEDBACK_AGENT_ID,
        permission_scope=_RUNTIME_TOOL_PERMISSION_SCOPE,
        owner_scope=_RUNTIME_TOOL_OWNER_SCOPE,
        side_effect_policy=loop_policy.side_effect_policy,
        payload=payload,
    )


def run_polish_feedback_skeleton(
    *,
    context: AgentRunContext,
    command: AgentCommandEnvelope,
    flag_resolver: RuntimeFlagResolver | None = None,
) -> AgentRunResult:
    descriptor = build_polish_feedback_graph_descriptor()
    _validate_context(context, command, descriptor)
    resolver = flag_resolver or RuntimeFlagResolver()
    decision = resolver.resolve_graph_flag(descriptor, actor_id=context.actor_id, caller="runner_entry")
    if not decision.enabled:
        raise GraphDisabledError(f"graph disabled: {descriptor.graph_name}")

    output_refs, interrupt_refs = _build_output_refs(context=context, command=command)
    checkpoint_ref = "ackpt_" + _stable_id(context.owner_id, context.run_id, "checkpoint")
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
        "metadata_refs": _metadata_refs(command.metadata),
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


def build_polish_feedback_fake_runtime_payload(
    *,
    context: AgentRunContext,
    command: AgentCommandEnvelope,
    checkpoint_refs: tuple[str, ...],
) -> dict[str, Any]:
    descriptor = build_polish_feedback_graph_descriptor()
    _validate_context(context, command, descriptor)
    input_refs = _pr6_input_ref_map(command)
    _validate_pr6_metadata(command.metadata)
    if not checkpoint_refs or any(not ref.startswith("ackpt_") for ref in checkpoint_refs):
        raise RuntimeValidationError("PR6 fake runtime requires checkpoint refs")

    suffix = _stable_id(
        context.owner_id,
        context.run_id,
        context.ai_task_id,
        input_refs["session_ref"],
        input_refs["question_ref"],
        input_refs["answer_ref"],
        command.metadata.get("request_digest", ""),
    )
    asset_update_candidate_refs = _pr6_asset_update_candidate_refs(command.metadata)
    hitl_triggers = _pr6_hitl_triggers(command.metadata)
    low_confidence_refs = tuple(
        trigger["trigger_ref"]
        for trigger in hitl_triggers
        if trigger["interrupt_type"] == "low_confidence_formal_update"
    )
    payload = {
        "graph_name": POLISH_FEEDBACK_GRAPH_NAME,
        "graph_version": POLISH_FEEDBACK_FAKE_RUNTIME_VERSION,
        "status": "fake_runtime_succeeded",
        "input_refs": input_refs,
        "output_refs": {
            "result_refs": ["result_ref_" + suffix],
            "candidate_refs": ["feedback_candidate_ref_" + suffix, *asset_update_candidate_refs],
            "asset_update_candidate_refs": list(asset_update_candidate_refs),
            "suggestion_refs": [],
            "formal_refs": [],
        },
        "trace_refs": {
            "checkpoint_refs": list(checkpoint_refs),
            "validation_refs": ["validation_ref_" + suffix],
            "low_confidence_refs": list(low_confidence_refs),
        },
        "hitl_triggers": hitl_triggers,
        "counters": {
            "provider_calls": 0,
            "formal_business_writes": 0,
            "db_business_writes": 0,
        },
        "rollback": {
            "checkpoint_refs_are_business_facts": False,
            "legacy_direct_path_retained_when_disabled": True,
        },
    }
    return sanitize_payload(payload)


def build_polish_feedback_readonly_parity_gate(
    *,
    owner_id: str,
    actor_id: str,
    run_id: str,
    ai_task_id: str,
    session_ref: str,
    question_ref: str,
    answer_ref: str,
    prior_answer_refs: tuple[str, ...] | list[str] = (),
    prior_feedback_refs: tuple[str, ...] | list[str] = (),
    rubric_summary_ref: str | None = None,
    idempotency_digest: str | None = None,
    **raw_inputs: Any,
) -> dict[str, Any]:
    _validate_pr7_raw_inputs(raw_inputs)
    _validate_pr7_scoped_id("owner_id", owner_id)
    _validate_pr7_scoped_id("actor_id", actor_id)
    _validate_pr7_scoped_id("run_id", run_id)
    _validate_pr7_scoped_id("ai_task_id", ai_task_id)

    input_refs = _pr7_input_ref_map(
        session_ref=session_ref,
        question_ref=question_ref,
        answer_ref=answer_ref,
        prior_answer_refs=prior_answer_refs,
        prior_feedback_refs=prior_feedback_refs,
        rubric_summary_ref=rubric_summary_ref,
    )
    suffix = _stable_id(
        owner_id,
        actor_id,
        run_id,
        ai_task_id,
        input_refs["session_ref"],
        input_refs["question_ref"],
        input_refs["answer_ref"],
        json.dumps(input_refs["prior_answer_refs"], sort_keys=True),
        json.dumps(input_refs["prior_feedback_refs"], sort_keys=True),
        input_refs["rubric_summary_ref"] or "",
        idempotency_digest or "",
    )
    payload = {
        "graph_name": POLISH_FEEDBACK_GRAPH_NAME,
        "parity_gate_version": POLISH_FEEDBACK_READONLY_PARITY_VERSION,
        "mode": "readonly_contract_ref_parity",
        "input_refs": input_refs,
        "diagnostics": {
            "contract_parity": "refs_only",
            "semantic_payload_parity": "not_evaluated",
            "legacy_direct_path_retained": True,
            "legacy_writer_touched": False,
            "provider_path_touched": False,
        },
        "output_refs": {
            "result_refs": ["parity_result_ref_" + suffix],
            "candidate_refs": [],
            "formal_refs": [],
        },
        "counters": {
            "provider_calls": 0,
            "formal_business_writes": 0,
            "db_business_writes": 0,
        },
        "rollback": {
            "flag_only": True,
            "legacy_direct_path_is_only_writer": True,
            "checkpoint_refs_are_business_facts": False,
        },
    }
    return sanitize_payload(payload)


def build_polish_feedback_trace_request(
    *,
    owner_id: str,
    actor_id: str,
    ai_task_id: str,
    agent_run_id: str,
    agent_node_run_id: str,
    session_ref: str,
    question_ref: str,
    answer_ref: str,
    rubric_summary_ref: str,
    idempotency_digest: str,
    question_digest: str,
    answer_digest: str,
    parity_result_ref: str,
    prior_answer_refs: tuple[str, ...] | list[str] = (),
    prior_feedback_refs: tuple[str, ...] | list[str] = (),
    evidence_ref_ids: tuple[str, ...] | list[str] = (),
    validation_ref_ids: tuple[str, ...] | list[str] = (),
    low_confidence_ref_ids: tuple[str, ...] | list[str] = (),
    evidence_bundle_extra: dict[str, Any] | None = None,
    **raw_inputs: Any,
) -> PolishFeedbackTraceRequestPlan:
    _validate_pr8_raw_inputs(raw_inputs)
    _validate_pr8_scoped_id("owner_id", owner_id)
    _validate_pr8_scoped_id("actor_id", actor_id)
    _validate_pr8_scoped_id("ai_task_id", ai_task_id)
    _validate_pr8_scoped_id("agent_run_id", agent_run_id)
    _validate_pr8_scoped_id("agent_node_run_id", agent_node_run_id)

    evidence_bundle = _pr8_evidence_bundle(
        session_ref=session_ref,
        question_ref=question_ref,
        answer_ref=answer_ref,
        prior_answer_refs=prior_answer_refs,
        prior_feedback_refs=prior_feedback_refs,
        rubric_summary_ref=rubric_summary_ref,
        idempotency_digest=idempotency_digest,
        question_digest=question_digest,
        answer_digest=answer_digest,
        evidence_ref_ids=evidence_ref_ids,
        validation_ref_ids=validation_ref_ids,
        low_confidence_ref_ids=low_confidence_ref_ids,
        parity_result_ref=parity_result_ref,
    )
    if evidence_bundle_extra:
        evidence_bundle = evidence_bundle | dict(evidence_bundle_extra)
    _validate_pr8_evidence_bundle(evidence_bundle)

    input_refs = (
        evidence_bundle["session_ref"],
        evidence_bundle["question_ref"],
        evidence_bundle["answer_ref"],
    )
    _validate_pr8_input_refs(input_refs)
    _authorize_trace_gate_tool_call(owner_id=owner_id, input_refs=input_refs, payload=evidence_bundle)

    trace_context = LlmTraceContext(
        owner_id=owner_id,
        actor_id=actor_id,
        ai_task_id=ai_task_id,
        agent_run_id=agent_run_id,
        agent_node_run_id=agent_node_run_id,
        contract_ids=("P-POLISH-FEEDBACK-001",),
        replay_mode="production_resume",
    )
    transport_request = build_validated_transport_request(
        contract_ids=("P-POLISH-FEEDBACK-001",),
        task_type=POLISH_FEEDBACK_TRACE_TASK_TYPE,
        input_refs=input_refs,
        evidence_bundle=sanitize_payload(evidence_bundle),
        graph_name=POLISH_FEEDBACK_GRAPH_NAME,
        node_name=POLISH_FEEDBACK_TRACE_GATE_NODE_NAME,
        prompt_version=POLISH_FEEDBACK_TRACE_GATE_PROMPT_VERSION,
        schema_id=POLISH_FEEDBACK_TRACE_GATE_SCHEMA_ID,
        required_evidence_keys=_PR8_ALLOWED_EVIDENCE_BUNDLE_KEYS,
        allowed_evidence_keys=_PR8_ALLOWED_EVIDENCE_BUNDLE_KEYS,
    )
    return PolishFeedbackTraceRequestPlan(
        trace_context=trace_context,
        transport_request=transport_request,
    )


def plan_polish_feedback_provider_trace_gate(
    *,
    transport: PersistedLlmTransport,
    owner_id: str,
    actor_id: str,
    ai_task_id: str,
    agent_run_id: str,
    agent_node_run_id: str,
    session_ref: str,
    question_ref: str,
    answer_ref: str,
    rubric_summary_ref: str,
    idempotency_digest: str,
    question_digest: str,
    answer_digest: str,
    parity_result_ref: str,
    prior_answer_refs: tuple[str, ...] | list[str] = (),
    prior_feedback_refs: tuple[str, ...] | list[str] = (),
    evidence_ref_ids: tuple[str, ...] | list[str] = (),
    validation_ref_ids: tuple[str, ...] | list[str] = (),
    low_confidence_ref_ids: tuple[str, ...] | list[str] = (),
    evidence_bundle_extra: dict[str, Any] | None = None,
    **raw_inputs: Any,
) -> None:
    trace_request = build_polish_feedback_trace_request(
        owner_id=owner_id,
        actor_id=actor_id,
        ai_task_id=ai_task_id,
        agent_run_id=agent_run_id,
        agent_node_run_id=agent_node_run_id,
        session_ref=session_ref,
        question_ref=question_ref,
        answer_ref=answer_ref,
        prior_answer_refs=prior_answer_refs,
        prior_feedback_refs=prior_feedback_refs,
        rubric_summary_ref=rubric_summary_ref,
        idempotency_digest=idempotency_digest,
        question_digest=question_digest,
        answer_digest=answer_digest,
        evidence_ref_ids=evidence_ref_ids,
        validation_ref_ids=validation_ref_ids,
        low_confidence_ref_ids=low_confidence_ref_ids,
        parity_result_ref=parity_result_ref,
        evidence_bundle_extra=evidence_bundle_extra,
        **raw_inputs,
    )
    transport.generate(trace_request.transport_request, trace_request.trace_context)


def replay_polish_feedback_skeleton(*, context: AgentRunContext, checkpoint_ref: str) -> AgentReplayResult:
    if context.graph_name != POLISH_FEEDBACK_GRAPH_NAME:
        raise RuntimePolicyError("replay context graph does not match polish feedback skeleton")
    if not checkpoint_ref.startswith("ackpt_"):
        raise RuntimePolicyError("replay requires a checkpoint ref")
    return AgentReplayResult(
        run_id=context.run_id,
        status="skeleton_replayed",
        read_only=True,
        formal_write_blocked=True,
        output_refs=(),
        trace_refs=(checkpoint_ref,),
        timeline_refs=(),
    )


def _validate_context(
    context: AgentRunContext,
    command: AgentCommandEnvelope,
    descriptor: "GraphDescriptor",
) -> None:
    if command != context.command:
        raise RuntimePolicyError("command must match context command")
    if context.graph_name != descriptor.graph_name:
        raise RuntimePolicyError("context graph does not match polish feedback skeleton")
    if context.graph_version != descriptor.graph_version:
        raise RuntimePolicyError("context graph version does not match polish feedback skeleton")
    if command.entrypoint not in descriptor.supported_entrypoints:
        raise RuntimeValidationError(f"unsupported entrypoint: {command.entrypoint}")

    unsupported = tuple(output for output in command.requested_outputs if output not in descriptor.supported_outputs)
    if unsupported:
        raise RuntimeValidationError(f"unsupported output: {', '.join(unsupported)}")


def _build_output_refs(
    *, context: AgentRunContext, command: AgentCommandEnvelope
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    requested_outputs = command.requested_outputs or ("result_refs",)
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
        if requested_output == "result_refs":
            output_refs.append("result_ref_" + suffix)
        elif requested_output == "candidate_refs":
            output_refs.append("candidate_ref_" + suffix)
        elif requested_output == "suggestion_refs":
            output_refs.append("suggestion_ref_" + suffix)
        elif requested_output == "interrupt_refs":
            interrupt_refs.append("interrupt_ref_" + suffix)
    return tuple(output_refs), tuple(interrupt_refs)


def _pr6_input_ref_map(command: AgentCommandEnvelope) -> dict[str, str]:
    if len(command.input_refs) != len(_PR6_INPUT_REF_PREFIXES):
        raise RuntimeValidationError("PR6 fake runtime requires session, question, and answer refs")

    input_refs: dict[str, str] = {}
    for value, (key, prefix) in zip(command.input_refs, _PR6_INPUT_REF_PREFIXES, strict=True):
        ref = str(value)
        if not ref.startswith(prefix):
            raise RuntimeValidationError("PR6 fake runtime accepts refs only")
        input_refs[key] = ref
    return input_refs


def _pr6_asset_update_candidate_refs(metadata: dict[str, Any]) -> tuple[str, ...]:
    value = metadata.get("asset_update_candidate_refs", ())
    if value in (None, ""):
        return ()
    if not isinstance(value, (list, tuple)):
        raise RuntimeValidationError("PR6 fake runtime asset update candidates must be refs")

    refs: list[str] = []
    for item in value:
        ref = str(item).strip()
        if not ref.startswith("asset_update_candidate_ref_"):
            raise RuntimeValidationError("PR6 fake runtime asset update candidates must be refs")
        refs.append(ref)
    return tuple(dict.fromkeys(refs))


def _pr6_hitl_triggers(metadata: dict[str, Any]) -> tuple[dict[str, str], ...]:
    triggers: list[dict[str, str]] = []
    for metadata_key, (interrupt_type, prefixes) in _PR6_HITL_TRIGGER_REF_KEYS.items():
        value = metadata.get(metadata_key)
        if value in (None, ""):
            continue
        ref = str(value).strip()
        if not any(ref.startswith(prefix) for prefix in prefixes):
            raise RuntimeValidationError("PR6 fake runtime HITL trigger must be a ref")
        triggers.append({"interrupt_type": interrupt_type, "trigger_ref": ref})
    return tuple(triggers)


def _validate_pr6_metadata(metadata: dict[str, Any]) -> None:
    for key, value in metadata.items():
        normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in _PR6_FORBIDDEN_METADATA_KEYS:
            raise RuntimeValidationError("PR6 fake runtime metadata accepts refs and digests only")
        if (
            normalized not in _PR6_ALLOWED_METADATA_KEYS
            and not normalized.endswith("_ref")
            and not normalized.endswith("_refs")
            and not normalized.endswith("_digest")
            and not normalized.endswith("_hash")
        ):
            raise RuntimeValidationError("PR6 fake runtime metadata accepts refs and digests only")
        if isinstance(value, dict):
            _validate_pr6_metadata(value)


def _validate_pr7_raw_inputs(raw_inputs: dict[str, Any]) -> None:
    if not raw_inputs:
        return
    for key in raw_inputs:
        normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in _PR7_FORBIDDEN_INPUT_KEYS:
            raise RuntimePolicyError("PR7 readonly parity gate rejects raw inputs")
    raise RuntimePolicyError("PR7 readonly parity gate accepts only scoped ids, refs, and digests")


def _validate_pr8_raw_inputs(raw_inputs: dict[str, Any]) -> None:
    if not raw_inputs:
        return
    for key, value in raw_inputs.items():
        normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in _PR8_FORBIDDEN_INPUT_KEYS or contains_sensitive_payload({key: value}):
            raise RuntimePolicyError("PR8 polish trace gate rejects raw inputs")
    raise RuntimePolicyError("PR8 polish trace gate accepts only scoped ids, refs, and digests")


def _validate_pr8_scoped_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RuntimePolicyError(f"PR8 polish trace gate requires {name}")


def _pr8_evidence_bundle(
    *,
    session_ref: str,
    question_ref: str,
    answer_ref: str,
    prior_answer_refs: tuple[str, ...] | list[str],
    prior_feedback_refs: tuple[str, ...] | list[str],
    rubric_summary_ref: str,
    idempotency_digest: str,
    question_digest: str,
    answer_digest: str,
    evidence_ref_ids: tuple[str, ...] | list[str],
    validation_ref_ids: tuple[str, ...] | list[str],
    low_confidence_ref_ids: tuple[str, ...] | list[str],
    parity_result_ref: str,
) -> dict[str, Any]:
    return {
        "session_ref": _validate_pr8_ref("session_ref", session_ref, "session_ref_"),
        "question_ref": _validate_pr8_ref("question_ref", question_ref, "question_ref_"),
        "answer_ref": _validate_pr8_ref("answer_ref", answer_ref, "answer_ref_"),
        "prior_answer_refs": [
            _validate_pr8_ref("prior_answer_refs", ref, "answer_ref_") for ref in prior_answer_refs
        ],
        "prior_feedback_refs": [
            _validate_pr8_ref("prior_feedback_refs", ref, "feedback_ref_") for ref in prior_feedback_refs
        ],
        "rubric_summary_ref": _validate_pr8_ref(
            "rubric_summary_ref",
            rubric_summary_ref,
            "rubric_summary_ref_",
        ),
        "idempotency_digest": _validate_pr8_digest("idempotency_digest", idempotency_digest),
        "question_digest": _validate_pr8_digest("question_digest", question_digest),
        "answer_digest": _validate_pr8_digest("answer_digest", answer_digest),
        "evidence_ref_ids": [
            _validate_pr8_ref("evidence_ref_ids", ref, "evidence_ref_") for ref in evidence_ref_ids
        ],
        "validation_ref_ids": [
            _validate_pr8_ref("validation_ref_ids", ref, "validation_ref_") for ref in validation_ref_ids
        ],
        "low_confidence_ref_ids": [
            _validate_pr8_ref("low_confidence_ref_ids", ref, "low_confidence_ref_")
            for ref in low_confidence_ref_ids
        ],
        "parity_result_ref": _validate_pr8_ref("parity_result_ref", parity_result_ref, "parity_result_ref_"),
    }


def _validate_pr8_evidence_bundle(evidence_bundle: dict[str, Any]) -> None:
    extra_keys = set(evidence_bundle) - _PR8_ALLOWED_EVIDENCE_BUNDLE_KEYS
    if extra_keys:
        raise RuntimePolicyError("PR8 polish trace gate evidence bundle accepts only locked refs and digests")
    if contains_sensitive_payload(evidence_bundle):
        raise RuntimePolicyError("PR8 polish trace gate evidence bundle must be sanitized")


def _validate_pr8_input_refs(input_refs: tuple[str, ...]) -> None:
    if len(input_refs) != 3 or any(not isinstance(ref, str) or not ref.strip() for ref in input_refs):
        raise RuntimePolicyError("PR8 polish trace gate requires non-empty input refs")


def _validate_pr8_ref(name: str, value: str, prefix: str) -> str:
    if not isinstance(value, str) or not value.startswith(prefix):
        raise RuntimePolicyError(f"PR8 polish trace gate requires {name} as ref")
    return value


def _validate_pr8_digest(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise RuntimePolicyError(f"PR8 polish trace gate requires {name} as digest")
    return value


def _validate_pr7_scoped_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeValidationError(f"PR7 readonly parity gate requires {name}")


def _pr7_input_ref_map(
    *,
    session_ref: str,
    question_ref: str,
    answer_ref: str,
    prior_answer_refs: tuple[str, ...] | list[str],
    prior_feedback_refs: tuple[str, ...] | list[str],
    rubric_summary_ref: str | None,
) -> dict[str, str | list[str] | None]:
    input_refs: dict[str, str | list[str] | None] = {}
    for key, value, prefix in (
        ("session_ref", session_ref, "session_ref_"),
        ("question_ref", question_ref, "question_ref_"),
        ("answer_ref", answer_ref, "answer_ref_"),
    ):
        input_refs[key] = _validate_pr7_ref(key, value, prefix)
    input_refs["prior_answer_refs"] = [
        _validate_pr7_ref("prior_answer_refs", ref, "answer_ref_") for ref in prior_answer_refs
    ]
    input_refs["prior_feedback_refs"] = [
        _validate_pr7_ref("prior_feedback_refs", ref, "feedback_ref_") for ref in prior_feedback_refs
    ]
    input_refs["rubric_summary_ref"] = (
        _validate_pr7_ref("rubric_summary_ref", rubric_summary_ref, "rubric_summary_ref_")
        if rubric_summary_ref is not None
        else None
    )
    return input_refs


def _validate_pr7_ref(name: str, value: str, prefix: str) -> str:
    if not isinstance(value, str) or not value.startswith(prefix):
        raise RuntimeValidationError(f"PR7 readonly parity gate requires {name} as ref")
    return value


def _metadata_refs(metadata: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(value) for key, value in sorted(metadata.items()) if str(key).endswith("_ref"))


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:16]
