from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.application.agents.contracts import (
    AgentExecutionPlan,
    AgentExecutionResult,
    AgentExecutionStatus,
    AgentExecutionTimeline,
    AgentExecutionTrace,
    CROSS_AGENT_ALLOWED_RESUME_ACTIONS,
    CROSS_AGENT_HITL_TRIGGER_TYPES,
)
from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentCommandEnvelope,
    AgentGraphRunner,
    AgentReplayResult,
    AgentRunContext,
    AgentRunResult,
    AgentRunStatus,
    AgentRunTimelinePage,
    RuntimeValidationError,
    validate_agent_runtime_status,
)

_CROSS_AGENT_FORBIDDEN_METADATA_KEY_PARTS = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "checkpoint_payload",
    "full_source_body",
    "full_resume",
    "full_jd",
    "full_answer",
    "full_asset_body",
    "api_key",
    "token",
    "cookie",
    "secret",
)

_CROSS_AGENT_REPLAY_COUNTER_KEYS = (
    "provider_calls",
    "provider_call_count",
    "tool_calls",
    "external_tool_calls",
    "external_tool_call_count",
    "repository_calls",
    "repository_writes",
    "repository_write_count",
    "db_business_writes",
    "database_business_writes",
    "database_write_count",
    "formal_business_writes",
    "formal_write_count",
    "formal_writes",
)

_CROSS_AGENT_REQUIRED_TIMELINE_REF_KEYS = (
    "plan_refs",
    "handoff_refs",
    "validation_refs",
    "candidate_refs",
)

_CROSS_AGENT_OPTIONAL_TIMELINE_REF_KEYS = (
    "policy_refs",
    "tool_refs",
    "low_confidence_flags",
    "interrupt_refs",
)

_FORMAL_METADATA_KEY_EXCEPTIONS = {
    "formal_write_blocked",
    "formal_write_blocked_until",
}


def validate_cross_agent_resume_payload(
    resume_payload: dict[str, object],
    *,
    expected_owner_id: str = "",
    interrupt_ref: str = "",
    allowed_actions: tuple[str, ...] = CROSS_AGENT_ALLOWED_RESUME_ACTIONS,
) -> dict[str, object]:
    """Validate refs-only cross-agent resume control fields without persisting state."""

    if not isinstance(resume_payload, dict):
        raise ValueError("cross-agent resume payload must be an object")
    _reject_cross_agent_unsafe_metadata(resume_payload, label="cross-agent resume payload")
    checkpoint_ref = str(resume_payload.get("checkpoint_ref") or "").strip()
    if not checkpoint_ref:
        raise ValueError("checkpoint_ref is required for cross-agent resume")
    base_version = resume_payload.get("base_version")
    if type(base_version) is not int or base_version < 0:
        raise ValueError("base_version must be a non-negative integer for cross-agent resume")
    idempotency_key = str(resume_payload.get("idempotency_key") or "").strip()
    if not idempotency_key:
        raise ValueError("idempotency_key is required for cross-agent resume")
    owner_ref = str(resume_payload.get("owner_id") or resume_payload.get("owner_ref") or "").strip()
    if not owner_ref:
        raise ValueError("owner_id or owner_ref is required for cross-agent resume")
    if expected_owner_id and owner_ref != expected_owner_id:
        raise ValueError("owner scope does not match cross-agent resume payload")
    payload_interrupt_ref = str(resume_payload.get("interrupt_ref") or "").strip()
    if interrupt_ref and payload_interrupt_ref != interrupt_ref:
        raise ValueError("interrupt_ref does not match cross-agent resume payload")
    if not payload_interrupt_ref:
        raise ValueError("interrupt_ref is required for cross-agent interrupt resume")
    resume_action = str(resume_payload.get("allowed_action") or resume_payload.get("resume_action") or "").strip()
    if not resume_action:
        raise ValueError("allowed_action or resume_action is required for cross-agent resume")
    if resume_action not in allowed_actions:
        raise ValueError("unsupported cross-agent resume action")
    return {
        **resume_payload,
        "checkpoint_ref": checkpoint_ref,
        "base_version": base_version,
        "idempotency_key": idempotency_key,
        "owner_ref": owner_ref,
        "interrupt_ref": payload_interrupt_ref,
        "resume_action": resume_action,
    }


def validate_cross_agent_replay_metadata(metadata: dict[str, object]) -> dict[str, object]:
    """Validate that cross-agent replay remains read-only and formal-write-blocked."""

    if not isinstance(metadata, dict):
        raise ValueError("cross-agent replay metadata must be an object")
    _reject_cross_agent_unsafe_metadata(metadata, label="cross-agent replay metadata")
    if metadata.get("read_only") is not True:
        raise ValueError("cross-agent replay must be read_only")
    if metadata.get("formal_write_blocked") is not True:
        raise ValueError("cross-agent replay must be formal_write_blocked")
    for key in _CROSS_AGENT_REPLAY_COUNTER_KEYS:
        if not _metadata_counter_is_zero(metadata.get(key, 0)):
            raise ValueError("cross-agent replay cannot call providers, tools, repositories, DB, or formal writes")
    return dict(metadata)


def map_cross_agent_trace_timeline_refs(metadata: dict[str, object]) -> dict[str, object]:
    """Return refs-only cross-agent timeline buckets while keeping ref categories separate."""

    if not isinstance(metadata, dict):
        raise ValueError("cross-agent trace metadata must be an object")
    _reject_cross_agent_unsafe_metadata(metadata, label="cross-agent trace metadata")
    mapped: dict[str, object] = {
        key: _metadata_refs(metadata, key)
        for key in (*_CROSS_AGENT_REQUIRED_TIMELINE_REF_KEYS, *_CROSS_AGENT_OPTIONAL_TIMELINE_REF_KEYS)
    }
    missing = tuple(key for key in _CROSS_AGENT_REQUIRED_TIMELINE_REF_KEYS if not mapped[key])
    if missing:
        raise ValueError("cross-agent trace metadata is missing required refs")
    output_refs = _metadata_refs(metadata, "output_refs")
    collapsed_refs = set(output_refs) & (
        set(mapped["handoff_refs"]) | set(mapped["validation_refs"])
    )
    if collapsed_refs:
        raise ValueError("handoff refs and validation refs must not be collapsed into output_refs")
    failure_reason = str(metadata.get("failure_reason") or "").strip()
    status = str(metadata.get("status") or "").strip()
    if status:
        category = validate_agent_runtime_status(status, metadata)
        if category in {"blocked", "failed", "interrupted"} and not failure_reason and not mapped["interrupt_refs"]:
            raise ValueError("failure_reason or interrupt_refs are required for blocked cross-agent trace events")
    if failure_reason:
        mapped["failure_reason"] = failure_reason
    if output_refs:
        mapped["output_refs"] = output_refs
    return mapped


def validate_cross_agent_hitl_trigger(
    *,
    trigger_type: str,
    status: str,
    metadata: dict[str, object],
) -> dict[str, object]:
    """Validate refs-only cross-agent HITL control events and non-success semantics."""

    normalized_trigger = str(trigger_type).strip()
    if normalized_trigger not in CROSS_AGENT_HITL_TRIGGER_TYPES:
        raise ValueError("unsupported cross-agent HITL trigger")
    if not isinstance(metadata, dict):
        raise ValueError("cross-agent HITL metadata must be an object")
    _reject_cross_agent_unsafe_metadata(metadata, label="cross-agent HITL metadata")
    category = validate_agent_runtime_status(status, metadata)
    interrupt_refs = _metadata_refs(metadata, "interrupt_refs")
    low_confidence_flags = _metadata_refs(metadata, "low_confidence_flags")
    if normalized_trigger in {"formal_write_requested", "asset_conflict"}:
        if category not in {"blocked", "interrupted", "cancelled"}:
            raise ValueError("cross-agent HITL trigger must interrupt or block")
        if not interrupt_refs and category != "blocked":
            raise ValueError("cross-agent HITL trigger requires interrupt_refs when not blocked")
    if normalized_trigger == "low_confidence" and not low_confidence_flags:
        trace_refs = metadata.get("trace_refs")
        nested_flags = (
            _metadata_refs(trace_refs, "low_confidence_flags")
            if isinstance(trace_refs, dict)
            else ()
        )
        if not nested_flags:
            raise ValueError("low_confidence HITL trigger must be trace-visible")
    if normalized_trigger == "validation_failed_partial_result" and category == "succeeded":
        raise ValueError("validation_failed_partial_result must not be reported as success")
    return dict(metadata)


def _is_cross_agent_resume_payload(resume_payload: dict[str, object]) -> bool:
    return bool(resume_payload.get("cross_agent_resume") or resume_payload.get("cross_agent_handoff"))


def _metadata_refs(metadata: dict[str, object], key: str) -> tuple[str, ...]:
    value = metadata.get(key)
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item).strip())
    return ()


def _reject_cross_agent_unsafe_metadata(value: object, *, label: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _cross_agent_metadata_key_is_blocked(key):
                raise ValueError(f"{label} contains unsafe metadata")
            _reject_cross_agent_unsafe_metadata(item, label=label)
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            _reject_cross_agent_unsafe_metadata(item, label=label)


def _cross_agent_metadata_key_is_blocked(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in _FORMAL_METADATA_KEY_EXCEPTIONS:
        return False
    if normalized in {"formal_ref", "formal_refs", "formal_outputs", "formal_write_result"}:
        return True
    return any(part in normalized for part in _CROSS_AGENT_FORBIDDEN_METADATA_KEY_PARTS)


def _metadata_counter_is_zero(value: object) -> bool:
    if isinstance(value, bool):
        return value is False
    if isinstance(value, int):
        return value == 0
    if isinstance(value, float):
        return value == 0.0
    if isinstance(value, str):
        stripped = value.strip()
        return stripped == "" or stripped == "0"
    return value is None


@runtime_checkable
class AgentExecutor(Protocol):
    def start(self, plan: AgentExecutionPlan) -> AgentExecutionResult: ...

    def resume(self, run_id: str, resume_payload: dict[str, object]) -> AgentExecutionResult: ...

    def replay(self, run_id: str, trace_ref: str) -> AgentExecutionResult: ...

    def get_status(self, run_id: str) -> AgentExecutionStatus: ...

    def get_timeline(self, run_id: str, cursor: str | None = None, limit: int = 50) -> AgentExecutionTimeline: ...

    def cancel(self, run_id: str, reason: str, actor_id: str) -> AgentExecutionStatus: ...


class AgentGraphRunnerExecutorAdapter:
    """Adapter that exposes the active AgentGraphRunner through AgentExecutor."""

    def __init__(self, runner: AgentGraphRunner) -> None:
        self._runner = runner
        self._contexts: dict[str, AgentRunContext] = {}

    def start(self, plan: AgentExecutionPlan) -> AgentExecutionResult:
        context = self._context_from_plan(plan)
        result = self._runner.start(context, context.command)
        self._contexts[result.run_id] = context
        return self._result_from_run(context, result)

    def resume(self, run_id: str, resume_payload: dict[str, object]) -> AgentExecutionResult:
        context = self._context_for_run(run_id)
        interrupt_ref = str(resume_payload.get("interrupt_ref") or "").strip()
        if not interrupt_ref:
            raise ValueError("interrupt_ref is required to resume an agent run")
        if _is_cross_agent_resume_payload(resume_payload):
            resume_payload = validate_cross_agent_resume_payload(
                resume_payload,
                expected_owner_id=context.owner_id,
                interrupt_ref=interrupt_ref,
            )
        result = self._runner.resume(context, interrupt_ref=interrupt_ref, resume_payload=resume_payload)
        return self._result_from_run(context, result)

    def resume_from_context(
        self, context: AgentRunContext, *, interrupt_ref: str, resume_payload: dict[str, object]
    ) -> AgentExecutionResult:
        self._contexts[context.run_id] = context
        if _is_cross_agent_resume_payload(resume_payload):
            resume_payload = validate_cross_agent_resume_payload(
                resume_payload,
                expected_owner_id=context.owner_id,
                interrupt_ref=interrupt_ref,
            )
        result = self._runner.resume(context, interrupt_ref=interrupt_ref, resume_payload=resume_payload)
        return self._result_from_run(context, result)

    def replay(self, run_id: str, trace_ref: str) -> AgentExecutionResult:
        context = self._context_for_run(run_id)
        result = self._runner.replay(context, checkpoint_ref=trace_ref)
        return self._result_from_replay(context, result)

    def get_status(self, run_id: str) -> AgentExecutionStatus:
        context = self._context_for_run(run_id)
        status = self._runner.get_status(run_id, context.owner_id)
        return self._status_from_run(context, status)

    def get_timeline(self, run_id: str, cursor: str | None = None, limit: int = 50) -> AgentExecutionTimeline:
        context = self._context_for_run(run_id)
        page = self._runner.get_timeline(run_id, context.owner_id, cursor=cursor, limit=limit)
        return self._timeline_from_run(context, page)

    def cancel(self, run_id: str, reason: str, actor_id: str) -> AgentExecutionStatus:
        context = self._context_for_run(run_id)
        status = self._runner.cancel(run_id, context.owner_id, reason=reason, actor_id=actor_id)
        return self._status_from_run(context, status)

    def _context_from_plan(self, plan: AgentExecutionPlan) -> AgentRunContext:
        if plan.runtime_loop_policy is None:
            raise ValueError("runtime loop policy is required")
        graph_name = plan.graph_name or str(plan.metadata.get("graph_name") or plan.agent_id)
        graph_version = plan.graph_version or str(plan.metadata.get("graph_version") or "v0")
        run_id = plan.run_id or f"arun_{plan.plan_id}"
        ai_task_id = plan.ai_task_id or f"aitask_{plan.plan_id}"
        actor_id = plan.actor_id or str(plan.metadata.get("actor_id") or plan.owner_id)
        requested_outputs = plan.requested_outputs or plan.candidate_output_refs or ("candidate_refs",)
        command = AgentCommandEnvelope(
            entrypoint="start",
            input_refs=plan.input_refs,
            requested_outputs=requested_outputs,
            idempotency_key=plan.idempotency_key or plan.plan_id,
            metadata={
                "plan_id": plan.plan_id,
                "agent_id": plan.agent_id,
                "objective": plan.objective,
                "steps": plan.steps,
                "runtime_loop_policy": {
                    "max_steps": plan.runtime_loop_policy.max_steps,
                    "max_retries": plan.runtime_loop_policy.max_retries,
                    "timeout_seconds": plan.runtime_loop_policy.timeout_seconds,
                    "stop_conditions": plan.runtime_loop_policy.stop_conditions,
                    "allowed_tools": plan.runtime_loop_policy.allowed_tools,
                    "allowed_callers": plan.runtime_loop_policy.allowed_callers,
                    "side_effect_policy": plan.runtime_loop_policy.side_effect_policy,
                    "repair_strategy": plan.runtime_loop_policy.repair_strategy,
                    "fallback_semantics": plan.runtime_loop_policy.fallback_semantics,
                },
                **plan.metadata,
            },
        )
        return AgentRunContext(
            owner_id=plan.owner_id,
            actor_id=actor_id,
            run_id=run_id,
            ai_task_id=ai_task_id,
            graph_name=graph_name,
            graph_version=graph_version,
            command=command,
        )

    def _context_for_run(self, run_id: str) -> AgentRunContext:
        context = self._contexts.get(run_id)
        if context is None:
            raise ValueError(f"unknown agent run: {run_id}")
        return context

    def _result_from_run(self, context: AgentRunContext, result: AgentRunResult) -> AgentExecutionResult:
        if result.formal_refs:
            raise ValueError("runtime result cannot expose formal refs")
        self._reject_runtime_formal_write_metadata(result.metadata)
        self._validate_status_consistency(result.status, result.metadata)
        self._enforce_runtime_controls(
            context,
            status=result.status,
            metadata=result.metadata,
            interrupt_refs=result.interrupt_refs,
        )
        candidate_refs = self._candidate_refs(result)
        handoff_candidate_descriptors = self._handoff_candidate_descriptors(result.candidate_payloads)
        trace = self._trace_from_refs(
            context,
            trace_refs=result.trace_refs,
            candidate_refs=candidate_refs,
            output_refs=result.output_refs,
            metadata=result.metadata,
            status=result.status,
            candidate_payloads=result.candidate_payloads,
        )
        return AgentExecutionResult(
            run_id=result.run_id,
            status=result.status,
            candidate_refs=candidate_refs,
            trace=trace,
            output_refs=result.output_refs,
            interrupt_refs=result.interrupt_refs,
            candidate_payloads=result.candidate_payloads,
            handoff_refs=trace.handoff_refs,
            metadata={
                **result.metadata,
                **(
                    {"handoff_candidate_descriptors": handoff_candidate_descriptors}
                    if handoff_candidate_descriptors
                    else {}
                ),
                "formal_write_blocked": result.formal_refs == (),
                "source_boundary": "AgentGraphRunner",
            },
        )

    def _result_from_replay(self, context: AgentRunContext, result: AgentReplayResult) -> AgentExecutionResult:
        if not result.read_only or not result.formal_write_blocked:
            raise ValueError("replay must remain read-only and formal-write-blocked")
        replay_metadata = {
            **result.metadata,
            "read_only": result.read_only,
            "formal_write_blocked": result.formal_write_blocked,
        }
        if replay_metadata.get("cross_agent_replay") is True:
            validate_cross_agent_replay_metadata(replay_metadata)
        self._reject_runtime_formal_write_metadata(replay_metadata)
        self._validate_status_consistency(result.status, replay_metadata)
        trace = self._trace_from_refs(
            context,
            trace_refs=result.trace_refs or result.timeline_refs,
            candidate_refs=result.output_refs,
            output_refs=result.output_refs,
            metadata=replay_metadata,
            status=result.status,
        )
        return AgentExecutionResult(
            run_id=result.run_id,
            status=result.status,
            candidate_refs=result.output_refs,
            trace=trace,
            output_refs=result.output_refs,
            metadata={
                **replay_metadata,
                "source_boundary": "AgentGraphRunner",
            },
        )

    def _status_from_run(self, context: AgentRunContext, status: AgentRunStatus) -> AgentExecutionStatus:
        self._reject_runtime_formal_write_metadata(status.metadata)
        self._validate_status_consistency(status.status, status.metadata)
        self._enforce_runtime_controls(
            context,
            status=status.status,
            metadata=status.metadata,
            interrupt_refs=status.interrupt_refs,
        )
        return AgentExecutionStatus(
            run_id=status.run_id,
            agent_id=context.graph_name,
            status=status.status,
            candidate_refs=status.output_refs,
            trace_refs=status.trace_refs,
            handoff_refs=self._unique_refs(
                *self._handoff_refs_from_metadata_and_refs(status.metadata, status.trace_refs),
                *self._trace_metadata_refs(status.metadata, "handoff_refs"),
            ),
            metadata={
                **status.metadata,
                "formal_write_blocked": status.formal_write_blocked,
                "source_boundary": "AgentGraphRunner",
            },
        )

    def _timeline_from_run(self, context: AgentRunContext, page: AgentRunTimelinePage) -> AgentExecutionTimeline:
        for event in page.events:
            self._reject_runtime_formal_write_metadata(event.metadata)
        events = tuple(
            AgentExecutionTrace(
                trace_id=event.event_id,
                run_id=page.run_id,
                agent_id=context.graph_name,
                agent_version=context.graph_version,
                ai_task_id=context.ai_task_id,
                events=(event.event_type,),
                metadata={"summary": event.summary, **event.metadata},
                input_refs=context.command.input_refs,
                output_refs=self._timeline_output_refs(event.metadata, event.refs),
                candidate_refs=self._unique_refs(
                    *self._handoff_envelope_refs(context.command.metadata, "candidate_ref"),
                    *self._metadata_refs(event.metadata, "candidate_refs"),
                    *(ref for ref in event.refs if "candidate_ref" in str(ref)),
                ),
                plan_refs=self._unique_refs(
                    *self._metadata_refs(context.command.metadata, "plan_refs"),
                    *self._metadata_refs(event.metadata, "plan_refs"),
                ),
                skill_refs=self._unique_refs(
                    *self._metadata_refs(context.command.metadata, "skill_refs"),
                    *self._metadata_refs(event.metadata, "skill_refs"),
                ),
                tool_refs=self._unique_refs(
                    *self._tool_refs_from_metadata(context.command.metadata),
                    *self._tool_refs_from_metadata(event.metadata),
                    *self._trace_metadata_refs(event.metadata, "tool_refs"),
                ),
                policy_refs=self._unique_refs(
                    *self._metadata_refs(context.command.metadata, "policy_refs"),
                    *self._metadata_refs(event.metadata, "policy_refs"),
                    *self._trace_metadata_refs(event.metadata, "policy_refs"),
                ),
                provider_refs=self._unique_refs(
                    *self._metadata_refs(context.command.metadata, "provider_refs"),
                    *self._metadata_refs(event.metadata, "provider_refs"),
                    *self._trace_metadata_refs(event.metadata, "provider_refs"),
                ),
                validation_refs=self._unique_refs(
                    *self._metadata_refs(context.command.metadata, "validation_refs"),
                    *self._handoff_envelope_refs(context.command.metadata, "validation_refs"),
                    *self._metadata_refs(event.metadata, "validation_refs"),
                    *self._trace_metadata_refs(event.metadata, "validation_refs"),
                    *(ref for ref in event.refs if str(ref).startswith("validation_ref_")),
                ),
                handoff_refs=self._unique_refs(
                    *self._metadata_refs(context.command.metadata, "handoff_refs"),
                    *self._handoff_envelope_refs(context.command.metadata, "handoff_ref"),
                    *self._handoff_refs_from_metadata_and_refs(event.metadata, event.refs),
                    *self._trace_metadata_refs(event.metadata, "handoff_refs"),
                ),
                low_confidence_flags=self._unique_refs(
                    *self._metadata_refs(context.command.metadata, "low_confidence_flags"),
                    *self._metadata_refs(event.metadata, "low_confidence_flags"),
                    *self._trace_metadata_refs(event.metadata, "low_confidence_flags"),
                    *self._trace_metadata_refs(event.metadata, "low_confidence_refs"),
                ),
                failure_reason=str(event.metadata.get("failure_reason") or ""),
                fallback_reason=str(event.metadata.get("fallback_reason") or ""),
            )
            for event in page.events
        )
        return AgentExecutionTimeline(
            run_id=page.run_id,
            events=events,
            cursor=page.next_cursor,
            has_more=page.next_cursor is not None,
        )

    def _validate_status_consistency(self, status: str, metadata: dict[str, Any]) -> None:
        validate_agent_runtime_status(status, metadata)

    def _enforce_runtime_controls(
        self,
        context: AgentRunContext,
        *,
        status: str,
        metadata: dict[str, Any],
        interrupt_refs: tuple[str, ...],
    ) -> None:
        policy = self._runtime_loop_policy_from_context(context)
        if not policy:
            return
        category = validate_agent_runtime_status(status, metadata)
        self._reject_disallowed_runtime_tool_calls(policy, metadata)
        self._reject_unbounded_success(policy, category=category, metadata=metadata)
        self._validate_runtime_stop_conditions(policy, category=category, metadata=metadata, interrupt_refs=interrupt_refs)
        self._validate_runtime_hitl_triggers(status=status, metadata=metadata, interrupt_refs=interrupt_refs)

    @staticmethod
    def _runtime_loop_policy_from_context(context: AgentRunContext) -> dict[str, Any]:
        policy = context.command.metadata.get("runtime_loop_policy")
        return dict(policy) if isinstance(policy, dict) else {}

    @classmethod
    def _reject_unbounded_success(
        cls,
        policy: dict[str, Any],
        *,
        category: str,
        metadata: dict[str, Any],
    ) -> None:
        cls._reject_bound_success(
            metadata,
            limit=policy.get("max_steps"),
            value_keys=("runtime_step_count", "step_count", "steps_executed"),
            stop_condition="max_steps_exceeded",
            category=category,
        )
        cls._reject_bound_success(
            metadata,
            limit=policy.get("max_retries"),
            value_keys=("runtime_retry_count", "retry_count", "retries_attempted"),
            stop_condition="max_retries_exceeded",
            category=category,
            accepted_stop_conditions=("max_retries_exceeded", "provider_failed", "validation_failed"),
        )
        cls._reject_bound_success(
            metadata,
            limit=policy.get("timeout_seconds"),
            value_keys=("runtime_elapsed_seconds", "elapsed_seconds", "duration_seconds"),
            stop_condition="timeout",
            category=category,
        )

    @classmethod
    def _reject_bound_success(
        cls,
        metadata: dict[str, Any],
        *,
        limit: object,
        value_keys: tuple[str, ...],
        stop_condition: str,
        category: str,
        accepted_stop_conditions: tuple[str, ...] | None = None,
    ) -> None:
        numeric_limit = cls._metadata_number(limit)
        if numeric_limit is None:
            return
        value = cls._first_metadata_number(metadata, value_keys)
        if value is None or value <= numeric_limit:
            return
        accepted = accepted_stop_conditions or (stop_condition,)
        if category != "succeeded" and any(cls._runtime_stop_condition_present(metadata, item) for item in accepted):
            return
        raise RuntimeValidationError(f"{stop_condition}: runtime loop bound exceeded")

    @classmethod
    def _validate_runtime_stop_conditions(
        cls,
        policy: dict[str, Any],
        *,
        category: str,
        metadata: dict[str, Any],
        interrupt_refs: tuple[str, ...],
    ) -> None:
        allowed = set(cls._metadata_refs(policy, "stop_conditions"))
        triggered = cls._runtime_stop_conditions_from_metadata(metadata)
        unknown = tuple(condition for condition in triggered if condition not in allowed and condition != "max_retries_exceeded")
        if unknown:
            raise RuntimeValidationError("runtime stop condition is not allowed: " + ", ".join(unknown))
        if triggered and category == "succeeded":
            raise RuntimeValidationError("runtime stop condition cannot be reported as success")
        if (
            {"formal_write_requested", "interrupt_required"} & set(triggered)
            and category != "blocked"
            and not cls._metadata_refs(metadata, "interrupt_refs")
            and not interrupt_refs
        ):
            raise RuntimeValidationError("runtime stop condition requires interrupt refs")

    @classmethod
    def _validate_runtime_hitl_triggers(
        cls,
        *,
        status: str,
        metadata: dict[str, Any],
        interrupt_refs: tuple[str, ...],
    ) -> None:
        triggers = [*cls._metadata_refs(metadata, "hitl_triggers")]
        trigger = str(metadata.get("hitl_trigger") or "").strip()
        if trigger:
            triggers.append(trigger)
        if metadata.get("hitl_required") is True and validate_agent_runtime_status(status, metadata) == "succeeded":
            raise RuntimeValidationError("HITL-required runtime result cannot be reported as success")
        if not triggers:
            return
        hitl_metadata = dict(metadata)
        if interrupt_refs and not cls._metadata_refs(hitl_metadata, "interrupt_refs"):
            hitl_metadata["interrupt_refs"] = interrupt_refs
        for trigger_type in tuple(dict.fromkeys(triggers)):
            validate_cross_agent_hitl_trigger(
                trigger_type=trigger_type,
                status=status,
                metadata=hitl_metadata,
            )

    @classmethod
    def _reject_disallowed_runtime_tool_calls(cls, policy: dict[str, Any], metadata: dict[str, Any]) -> None:
        allowed_tools = set(cls._metadata_refs(policy, "allowed_tools"))
        allowed_callers = set(cls._metadata_refs(policy, "allowed_callers"))
        for tool_call in cls._runtime_tool_call_entries(metadata):
            tool_refs = cls._tool_call_refs(tool_call)
            if not tool_refs:
                raise RuntimeValidationError("runtime tool call is missing permission scope")
            if any(cls._tool_ref_exposes_repository(ref) for ref in tool_refs):
                raise RuntimeValidationError("runtime tool call exposes repository or database internals")
            if allowed_tools and not any(ref in allowed_tools for ref in tool_refs):
                raise RuntimeValidationError("tool_not_allowed: " + sorted(tool_refs)[0])
            caller_id = str(tool_call.get("caller_id") or tool_call.get("agent_id") or "").strip()
            if caller_id and allowed_callers and caller_id not in allowed_callers:
                raise RuntimeValidationError("caller not allowed for tool")

    @classmethod
    def _runtime_tool_call_entries(cls, metadata: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        entries: list[dict[str, Any]] = []
        for key in ("tool_calls", "tool_results", "runtime_tool_calls"):
            value = metadata.get(key)
            values = value if isinstance(value, (list, tuple)) else (value,)
            for item in values:
                if isinstance(item, dict):
                    entries.append(item)
        trace_refs = metadata.get("trace_refs")
        if isinstance(trace_refs, dict):
            entries.extend(cls._runtime_tool_call_entries(trace_refs))
        return tuple(entries)

    @staticmethod
    def _tool_call_refs(tool_call: dict[str, Any]) -> set[str]:
        refs: set[str] = set()
        for key in ("tool_id", "tool_name", "permission_scope", "owner_scope"):
            value = str(tool_call.get(key) or "").strip()
            if value:
                refs.add(value)
        return refs

    @staticmethod
    def _tool_ref_exposes_repository(value: str) -> bool:
        normalized = value.lower().replace("-", "_").replace(" ", "_")
        return any(
            token in normalized
            for token in (
                "repository",
                "database",
                "sqlalchemy",
                "unit_of_work",
                "formal_writer",
                "formal_write_tool",
            )
        )

    @classmethod
    def _runtime_stop_conditions_from_metadata(cls, metadata: dict[str, Any]) -> tuple[str, ...]:
        values = [
            *cls._metadata_refs(metadata, "stop_conditions_triggered"),
            *cls._metadata_refs(metadata, "stop_conditions"),
        ]
        stop_condition = str(metadata.get("stop_condition") or "").strip()
        if stop_condition:
            values.append(stop_condition)
        return tuple(dict.fromkeys(values))

    @classmethod
    def _runtime_stop_condition_present(cls, metadata: dict[str, Any], stop_condition: str) -> bool:
        failure_reason = str(metadata.get("failure_reason") or "").strip()
        return stop_condition in cls._runtime_stop_conditions_from_metadata(metadata) or failure_reason == stop_condition

    @classmethod
    def _first_metadata_number(cls, metadata: dict[str, Any], keys: tuple[str, ...]) -> float | None:
        for key in keys:
            number = cls._metadata_number(metadata.get(key))
            if number is not None:
                return number
        return None

    @staticmethod
    def _metadata_number(value: object) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.strip())
            except ValueError:
                return None
        return None

    def _trace_from_refs(
        self,
        context: AgentRunContext,
        *,
        trace_refs: tuple[str, ...],
        candidate_refs: tuple[str, ...],
        output_refs: tuple[str, ...],
        metadata: dict[str, Any],
        status: str,
        candidate_payloads: tuple[AgentCandidatePayload, ...] = (),
    ) -> AgentExecutionTrace:
        trace_id = trace_refs[0] if trace_refs else f"trace_{context.run_id}"
        validation_refs = self._unique_refs(
            *self._metadata_refs(context.command.metadata, "validation_refs"),
            *self._metadata_refs(metadata, "validation_refs"),
            *self._trace_metadata_refs(metadata, "validation_refs"),
            *(ref for ref in trace_refs if str(ref).startswith("validation_ref_")),
            *(ref for payload in candidate_payloads for ref in payload.validation_refs),
        )
        handoff_refs = self._unique_refs(
            *self._metadata_refs(context.command.metadata, "handoff_refs"),
            *self._handoff_envelope_refs(context.command.metadata, "handoff_ref"),
            *self._metadata_refs(metadata, "handoff_refs"),
            *self._trace_metadata_refs(metadata, "handoff_refs"),
            *(ref for ref in trace_refs if str(ref).startswith("handoff_")),
        )
        low_confidence_flags = self._unique_refs(
            *self._metadata_refs(context.command.metadata, "low_confidence_flags"),
            *self._metadata_refs(metadata, "low_confidence_flags"),
            *self._trace_metadata_refs(metadata, "low_confidence_flags"),
            *self._trace_metadata_refs(metadata, "low_confidence_refs"),
            *(flag for payload in candidate_payloads for flag in payload.low_confidence_flags),
        )
        return AgentExecutionTrace(
            trace_id=trace_id,
            run_id=context.run_id,
            agent_id=context.graph_name,
            agent_version=context.graph_version,
            ai_task_id=context.ai_task_id,
            candidate_refs=candidate_refs,
            metadata=metadata,
            input_refs=context.command.input_refs,
            plan_refs=self._unique_refs(
                *self._metadata_refs(context.command.metadata, "plan_refs"),
                *self._metadata_refs(metadata, "plan_refs"),
            ),
            skill_refs=self._unique_refs(
                *self._metadata_refs(context.command.metadata, "skill_refs"),
                *self._metadata_refs(metadata, "skill_refs"),
            ),
            tool_refs=self._unique_refs(
                *self._tool_refs_from_metadata(context.command.metadata),
                *self._tool_refs_from_metadata(metadata),
                *self._trace_metadata_refs(metadata, "tool_refs"),
            ),
            policy_refs=self._unique_refs(
                *self._metadata_refs(context.command.metadata, "policy_refs"),
                *self._metadata_refs(metadata, "policy_refs"),
                *self._trace_metadata_refs(metadata, "policy_refs"),
            ),
            provider_refs=self._unique_refs(
                *self._metadata_refs(context.command.metadata, "provider_refs"),
                *self._metadata_refs(metadata, "provider_refs"),
                *self._trace_metadata_refs(metadata, "provider_refs"),
            ),
            validation_refs=validation_refs,
            handoff_refs=handoff_refs,
            output_refs=output_refs,
            low_confidence_flags=low_confidence_flags,
            failure_reason=str(metadata.get("failure_reason") or self._failure_reason_from_status(status)),
            fallback_reason=str(metadata.get("fallback_reason") or ""),
            events=self._events_from_metadata(status=status, metadata=metadata),
        )

    @staticmethod
    def _candidate_refs(result: AgentRunResult) -> tuple[str, ...]:
        refs = [*result.output_refs, *(payload.candidate_ref for payload in result.candidate_payloads)]
        return tuple(dict.fromkeys(refs))

    @staticmethod
    def _handoff_candidate_descriptors(candidate_payloads: tuple[AgentCandidatePayload, ...]) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "candidate_ref": payload.candidate_ref,
                "candidate_type": payload.candidate_type,
                "payload_schema_id": payload.payload_schema_id,
                "trace_refs": payload.trace_refs,
                "validation_refs": payload.validation_refs,
                "low_confidence_flags": payload.low_confidence_flags,
                **AgentGraphRunnerExecutorAdapter._asset_handoff_descriptor_fields(payload),
            }
            for payload in candidate_payloads
        )

    @staticmethod
    def _asset_handoff_descriptor_fields(payload: AgentCandidatePayload) -> dict[str, object]:
        if payload.candidate_type != "asset_update_candidate":
            return {}
        descriptor: dict[str, object] = {
            "asset_update_candidate_ref": payload.candidate_ref,
        }
        safe_string_fields = ("asset_body_ref", "asset_schema_id", "formal_write_blocked_until")
        for field_name in safe_string_fields:
            value = payload.payload.get(field_name)
            if isinstance(value, str) and value.strip():
                descriptor[field_name] = value.strip()
        user_confirmation_required = payload.payload.get("user_confirmation_required")
        if isinstance(user_confirmation_required, bool):
            descriptor["user_confirmation_required"] = user_confirmation_required
        return descriptor

    @staticmethod
    def _metadata_refs(metadata: dict[str, Any], key: str) -> tuple[str, ...]:
        value = metadata.get(key)
        if value is None:
            return ()
        if isinstance(value, str):
            return (value,) if value.strip() else ()
        if isinstance(value, (list, tuple, set)):
            return tuple(str(item) for item in value if str(item).strip())
        return ()

    @classmethod
    def _trace_metadata_refs(cls, metadata: dict[str, Any], key: str) -> tuple[str, ...]:
        trace_refs = metadata.get("trace_refs")
        if not isinstance(trace_refs, dict):
            return ()
        return cls._metadata_refs(trace_refs, key)

    @classmethod
    def _reject_runtime_formal_write_metadata(cls, metadata: dict[str, Any]) -> None:
        if cls._contains_runtime_formal_write_metadata(metadata):
            raise ValueError("runtime metadata cannot expose formal refs or business writes")
        if cls._contains_runtime_fake_provider_metadata(metadata):
            raise ValueError("runtime metadata cannot expose fake provider")
        if cls._contains_runtime_fail_open_fallback_metadata(metadata):
            raise ValueError("runtime metadata cannot report fail-open fallback success")

    @classmethod
    def _contains_runtime_formal_write_metadata(cls, value: object) -> bool:
        if isinstance(value, dict):
            for key, item in value.items():
                normalized_key = str(key).strip().lower().replace("-", "_").replace(" ", "_")
                if normalized_key in {"formal_ref", "formal_refs"} and cls._metadata_value_present(item):
                    return True
                if normalized_key in {
                    "business_writes",
                    "database_business_writes",
                    "database_write_count",
                    "database_writes",
                    "db_business_writes",
                    "db_write_count",
                    "db_writes",
                    "formal_business_writes",
                    "formal_fact_writes",
                    "formal_write_count",
                    "formal_writes",
                    "repository_write_count",
                    "repository_writes",
                } and not cls._metadata_counter_is_zero(item):
                    return True
                if cls._contains_runtime_formal_write_metadata(item):
                    return True
            return False
        if isinstance(value, (list, tuple, set)):
            return any(cls._contains_runtime_formal_write_metadata(item) for item in value)
        return False

    @classmethod
    def _contains_runtime_fake_provider_metadata(cls, value: object) -> bool:
        if isinstance(value, dict):
            for key, item in value.items():
                normalized_key = str(key).strip().lower().replace("-", "_").replace(" ", "_")
                if normalized_key in {
                    "fake_provider",
                    "fake_provider_used",
                    "fake_transport_configured",
                    "llm_fake_provider",
                    "provider_fake",
                    "production_fake_provider",
                    "runtime_fake_provider",
                } and cls._metadata_flag_is_true(item):
                    return True
                if normalized_key in {"llm_provider", "provider_mode", "provider_name", "provider_type", "runtime_provider"}:
                    normalized_value = str(item).strip().lower().replace("-", "_").replace(" ", "_")
                    if normalized_value in {"fake", "fake_provider", "fake_transport", "test_fake"}:
                        return True
                if cls._contains_runtime_fake_provider_metadata(item):
                    return True
            return False
        if isinstance(value, (list, tuple, set)):
            return any(cls._contains_runtime_fake_provider_metadata(item) for item in value)
        return False

    @classmethod
    def _contains_runtime_fail_open_fallback_metadata(cls, value: object) -> bool:
        if isinstance(value, dict):
            for key, item in value.items():
                normalized_key = str(key).strip().lower().replace("-", "_").replace(" ", "_")
                if normalized_key in {
                    "fail_open",
                    "fail_open_fallback",
                    "fallback_reported_as_generated_success",
                    "provider_fail_open",
                    "provider_fail_open_fallback",
                } and cls._metadata_flag_is_true(item):
                    return True
                if cls._contains_runtime_fail_open_fallback_metadata(item):
                    return True
            return False
        if isinstance(value, (list, tuple, set)):
            return any(cls._contains_runtime_fail_open_fallback_metadata(item) for item in value)
        return False

    @classmethod
    def _metadata_value_present(cls, value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, dict):
            return any(cls._metadata_value_present(item) for item in value.values())
        if isinstance(value, (list, tuple, set)):
            return any(cls._metadata_value_present(item) for item in value)
        return True

    @staticmethod
    def _metadata_counter_is_zero(value: object) -> bool:
        if isinstance(value, bool):
            return value is False
        if isinstance(value, int):
            return value == 0
        if isinstance(value, float):
            return value == 0.0
        if isinstance(value, str):
            stripped = value.strip()
            return stripped == "" or stripped == "0"
        return False

    @staticmethod
    def _metadata_flag_is_true(value: object) -> bool:
        if isinstance(value, bool):
            return value is True
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "on"}
        return False

    @staticmethod
    def _handoff_envelope_refs(metadata: dict[str, Any], key: str) -> tuple[str, ...]:
        envelope = metadata.get("handoff_envelope")
        if not isinstance(envelope, dict):
            return ()
        value = envelope.get(key)
        if value is None:
            return ()
        if isinstance(value, str):
            return (value,) if value.strip() else ()
        if isinstance(value, (list, tuple, set)):
            return tuple(str(item) for item in value if str(item).strip())
        return ()

    @classmethod
    def _tool_refs_from_metadata(cls, metadata: dict[str, Any]) -> tuple[str, ...]:
        refs = [*cls._metadata_refs(metadata, "tool_refs")]
        tool_results = metadata.get("tool_results")
        if isinstance(tool_results, (list, tuple)):
            for item in tool_results:
                if isinstance(item, dict):
                    ref = str(item.get("tool_id") or item.get("tool_name") or "").strip()
                    if ref:
                        refs.append(ref)
        return cls._unique_refs(*refs)

    @classmethod
    def _handoff_refs_from_metadata_and_refs(cls, metadata: dict[str, Any], refs: tuple[str, ...]) -> tuple[str, ...]:
        return cls._unique_refs(
            *cls._metadata_refs(metadata, "handoff_refs"),
            *(ref for ref in refs if str(ref).startswith("handoff_")),
        )

    @classmethod
    def _timeline_output_refs(cls, metadata: dict[str, Any], refs: tuple[str, ...]) -> tuple[str, ...]:
        return cls._unique_refs(
            *(ref for ref in refs if not str(ref).startswith(("validation_ref_", "handoff_"))),
            *cls._metadata_refs(metadata, "output_refs"),
        )

    @classmethod
    def _events_from_metadata(cls, *, status: str, metadata: dict[str, Any]) -> tuple[str, ...]:
        events = [status]
        events.extend(cls._metadata_refs(metadata, "events"))
        for key, name_key in (("phase_results", "phase"), ("tool_results", "tool_name")):
            values = metadata.get(key)
            if not isinstance(values, (list, tuple)):
                continue
            for item in values:
                if not isinstance(item, dict):
                    continue
                name = str(item.get(name_key) or "").strip()
                item_status = str(item.get("status") or "").strip()
                if name and item_status:
                    validate_agent_runtime_status(item_status)
                    events.append(f"{name}:{item_status}")
        return cls._unique_refs(*events)

    @staticmethod
    def _failure_reason_from_status(status: str) -> str:
        normalized = status.lower()
        if "failed" in normalized or "blocked" in normalized or "validation" in normalized:
            return normalized
        return ""

    @staticmethod
    def _unique_refs(*refs: str) -> tuple[str, ...]:
        return tuple(dict.fromkeys(str(ref) for ref in refs if str(ref).strip()))


__all__ = [
    "AgentExecutor",
    "AgentGraphRunnerExecutorAdapter",
    "map_cross_agent_trace_timeline_refs",
    "validate_cross_agent_hitl_trigger",
    "validate_cross_agent_replay_metadata",
    "validate_cross_agent_resume_payload",
]
