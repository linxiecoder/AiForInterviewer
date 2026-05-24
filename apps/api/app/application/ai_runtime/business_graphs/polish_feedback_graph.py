"""Default-off PR5 Polish feedback business graph skeleton."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

from app.application.ai_runtime.contracts import (
    AgentCommandEnvelope,
    AgentReplayResult,
    AgentRunContext,
    AgentRunResult,
    GraphDisabledError,
    RuntimePolicyError,
    RuntimeValidationError,
    sanitize_payload,
)
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver

if TYPE_CHECKING:
    from app.application.ai_runtime.registry import GraphDescriptor


POLISH_FEEDBACK_GRAPH_NAME = "polish_feedback_graph"
POLISH_FEEDBACK_GRAPH_VERSION = "pr5-skeleton"
POLISH_FEEDBACK_GRAPH_FLAG = "AIFI_GRAPH_POLISH_FEEDBACK_ENABLED"

_DEFAULT_ENTRYPOINTS = ("start", "replay")
_SUPPORTED_OUTPUTS = ("result_refs", "candidate_refs", "suggestion_refs", "interrupt_refs")


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


def _metadata_refs(metadata: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(value) for key, value in sorted(metadata.items()) if str(key).endswith("_ref"))


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:16]
