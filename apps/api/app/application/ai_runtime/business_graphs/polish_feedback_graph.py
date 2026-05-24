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
POLISH_FEEDBACK_FAKE_RUNTIME_VERSION = "pr6-fake-runtime"
POLISH_FEEDBACK_READONLY_PARITY_VERSION = "pr7-readonly-parity"
POLISH_FEEDBACK_GRAPH_FLAG = "AIFI_GRAPH_POLISH_FEEDBACK_ENABLED"

_DEFAULT_ENTRYPOINTS = ("start", "replay")
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
    }
)
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
    payload = {
        "graph_name": POLISH_FEEDBACK_GRAPH_NAME,
        "graph_version": POLISH_FEEDBACK_FAKE_RUNTIME_VERSION,
        "status": "fake_runtime_succeeded",
        "input_refs": input_refs,
        "output_refs": {
            "result_refs": ["result_ref_" + suffix],
            "candidate_refs": ["candidate_ref_" + suffix],
            "suggestion_refs": [],
            "formal_refs": [],
        },
        "trace_refs": {
            "checkpoint_refs": list(checkpoint_refs),
            "validation_refs": ["validation_ref_" + suffix],
            "low_confidence_refs": [],
        },
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
