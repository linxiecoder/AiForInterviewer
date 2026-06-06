"""AI Runtime orchestration facade contract."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.application.agents.contracts import (
    AgentExecutionPlan,
    AgentExecutionResult,
    AgentExecutionStatus,
    AgentExecutionTimeline,
    AgentExecutionTrace,
    AgentRuntimeLoopPolicy,
)
from app.application.agents.runtime import AgentGraphRunnerExecutorAdapter
from app.application.ai_runtime.contracts import (
    AgentCommandEnvelope,
    AgentGraphRunner,
    AgentReplayResult,
    AgentRunContext,
    AgentRunResult,
    AgentRunStatus,
    AgentTimelineEvent,
    AgentRunTimelinePage,
    AgentTaskStatusRef,
    GraphDisabledError,
    OwnerScopeError,
    RuntimeConflictError,
    RuntimeValidationError,
    sanitize_payload,
)
from app.application.ai_runtime.registry import GraphDescriptor
from app.application.ai_runtime.registry import AgentGraphRegistry
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver


_ALLOWED_RESUME_ACTIONS = frozenset({"approve", "reject", "edit", "defer_to_handoff"})


class AiOrchestrationFacade:
    def __init__(
        self,
        *,
        runner: AgentGraphRunner,
        registry: AgentGraphRegistry | None = None,
        flag_resolver: RuntimeFlagResolver | None = None,
    ) -> None:
        self._runner = runner
        self._executor = AgentGraphRunnerExecutorAdapter(runner)
        self._registry = registry or AgentGraphRegistry.default()
        self._flag_resolver = flag_resolver or RuntimeFlagResolver()
        self._idempotency_cache: dict[tuple[str, str, str], tuple[str, AgentTaskStatusRef]] = {}
        self._run_owner_ids: dict[str, str] = {}
        self._run_graph_names: dict[str, str] = {}

    def start_job_match_analysis(
        self,
        *,
        owner_id: str,
        actor_id: str,
        binding_ref: str,
        resume_ref: str,
        job_ref: str,
        score_rule_ref: str,
        idempotency_key: str,
    ) -> AgentTaskStatusRef:
        return self._start_run(
            task_type="job_match_analysis",
            owner_id=owner_id,
            actor_id=actor_id,
            input_refs=(binding_ref, resume_ref, job_ref, score_rule_ref),
            requested_outputs=("result_refs", "candidate_refs", "suggestion_refs"),
            idempotency_key=idempotency_key,
        )

    def start_polish_question_generation(
        self,
        *,
        owner_id: str,
        actor_id: str,
        session_ref: str,
        progress_node_refs: tuple[str, ...],
        completed_focus_refs: tuple[str, ...],
        idempotency_key: str,
        context_snapshot: dict[str, object] | None = None,
    ) -> AgentTaskStatusRef:
        return self._start_run(
            task_type="polish_question_generation",
            owner_id=owner_id,
            actor_id=actor_id,
            input_refs=(session_ref, *progress_node_refs, *completed_focus_refs),
            requested_outputs=("candidate_refs",),
            idempotency_key=idempotency_key,
            command_metadata={
                "polish_question_context_snapshot": context_snapshot,
                "context_source": (context_snapshot or {}).get("context_source")
                if isinstance(context_snapshot, dict)
                else None,
            }
            if context_snapshot is not None
            else None,
        )

    def start_polish_feedback_generation(
        self,
        *,
        owner_id: str,
        actor_id: str,
        session_ref: str,
        question_ref: str,
        answer_ref: str,
        requested_outputs: tuple[str, ...],
        idempotency_key: str,
    ) -> AgentTaskStatusRef:
        return self._start_run(
            task_type="polish_feedback_generation",
            owner_id=owner_id,
            actor_id=actor_id,
            input_refs=(session_ref, question_ref, answer_ref),
            requested_outputs=requested_outputs,
            idempotency_key=idempotency_key,
        )

    def start_report_generation(
        self,
        *,
        owner_id: str,
        actor_id: str,
        session_ref: str,
        report_type_ref: str,
        score_refs: tuple[str, ...],
        idempotency_key: str,
    ) -> AgentTaskStatusRef:
        return self._start_run(
            task_type="report_generation",
            owner_id=owner_id,
            actor_id=actor_id,
            input_refs=(session_ref, report_type_ref, *score_refs),
            requested_outputs=("result_refs", "candidate_refs"),
            idempotency_key=idempotency_key,
        )

    def start_review_generation(
        self,
        *,
        owner_id: str,
        actor_id: str,
        source_refs: tuple[str, ...],
        review_scope: str,
        privacy_flags: tuple[str, ...],
        idempotency_key: str,
    ) -> AgentTaskStatusRef:
        return self._start_run(
            task_type="review_generation",
            owner_id=owner_id,
            actor_id=actor_id,
            input_refs=(*source_refs, review_scope, *privacy_flags),
            requested_outputs=("candidate_refs", "suggestion_refs"),
            idempotency_key=idempotency_key,
        )

    def resume_interrupted_run(
        self,
        *,
        owner_id: str,
        actor_id: str,
        run_id: str,
        ai_task_id: str,
        graph_name: str,
        graph_version: str,
        interrupt_ref: str,
        checkpoint_ref: str,
        resume_payload: dict[str, Any],
        base_version: int,
        idempotency_key: str,
    ) -> AgentTaskStatusRef:
        if not owner_id or not interrupt_ref or not checkpoint_ref or not idempotency_key:
            raise RuntimeValidationError("owner, interrupt ref, checkpoint ref, and idempotency key are required")
        if type(base_version) is not int or base_version < 0:
            raise RuntimeValidationError("base version must be a non-negative integer")
        sanitized_resume_payload = _sanitize_resume_payload(resume_payload)
        descriptor = self._registry.get_graph_descriptor(graph_name)
        _require_supported_entrypoint(descriptor, "resume")
        runtime_decision = self._flag_resolver.resolve_runtime_flag("AIFI_AI_RUNTIME_ENABLED", actor_id=actor_id)
        graph_decision = self._flag_resolver.resolve_graph_flag(descriptor, actor_id=actor_id, caller="facade")
        if not runtime_decision.enabled or not graph_decision.enabled:
            raise GraphDisabledError(f"graph disabled: {descriptor.graph_name}")
        command = AgentCommandEnvelope(
            entrypoint="resume",
            input_refs=(interrupt_ref, checkpoint_ref),
            requested_outputs=("candidate_refs", "suggestion_refs", "interrupt_refs"),
            idempotency_key=idempotency_key,
            metadata={
                "base_version": base_version,
                "checkpoint_ref": checkpoint_ref,
                "runtime_loop_policy": _runtime_loop_policy_metadata(descriptor),
            },
        )
        context = AgentRunContext(
            owner_id=owner_id,
            actor_id=actor_id,
            run_id=run_id,
            ai_task_id=ai_task_id,
            graph_name=graph_name,
            graph_version=graph_version,
            command=command,
        )
        result = self._executor.resume_from_context(
            context,
            interrupt_ref=interrupt_ref,
            resume_payload={
                **sanitized_resume_payload,
                "checkpoint_ref": checkpoint_ref,
                "base_version": base_version,
                "idempotency_key": idempotency_key,
            },
        )
        self._run_owner_ids[run_id] = owner_id
        self._run_owner_ids[result.run_id] = owner_id
        self._run_graph_names[run_id] = descriptor.graph_name
        self._run_graph_names[result.run_id] = descriptor.graph_name
        return self._status_ref_from_execution(ai_task_id=ai_task_id, result=result)

    def replay_agent_run(
        self,
        *,
        owner_id: str,
        actor_id: str,
        run_id: str,
        ai_task_id: str,
        graph_name: str,
        graph_version: str,
        checkpoint_ref: str,
    ) -> AgentReplayResult:
        if not owner_id or not run_id or not checkpoint_ref:
            raise RuntimeValidationError("owner, run id, and checkpoint ref are required")
        descriptor = self._registry.get_graph_descriptor(graph_name)
        _require_supported_entrypoint(descriptor, "replay")
        runtime_decision = self._flag_resolver.resolve_runtime_flag("AIFI_AI_RUNTIME_ENABLED", actor_id=actor_id)
        graph_decision = self._flag_resolver.resolve_graph_flag(descriptor, actor_id=actor_id, caller="facade")
        if not runtime_decision.enabled or not graph_decision.enabled:
            raise GraphDisabledError(f"graph disabled: {descriptor.graph_name}")
        command = AgentCommandEnvelope(
            entrypoint="replay",
            input_refs=(checkpoint_ref,),
            requested_outputs=("candidate_refs", "trace_refs", "timeline_refs"),
            replay_mode="read_only",
            metadata={
                "checkpoint_ref": checkpoint_ref,
                "runtime_loop_policy": _runtime_loop_policy_metadata(descriptor),
            },
        )
        context = AgentRunContext(
            owner_id=owner_id,
            actor_id=actor_id,
            run_id=run_id,
            ai_task_id=ai_task_id,
            graph_name=descriptor.graph_name,
            graph_version=graph_version or descriptor.graph_version,
            command=command,
        )
        replay = self._runner.replay(context, checkpoint_ref=checkpoint_ref)
        if not replay.read_only or not replay.formal_write_blocked:
            raise RuntimeValidationError("replay must be read-only and formal-write-blocked")
        return AgentReplayResult(
            run_id=replay.run_id,
            status=replay.status,
            read_only=True,
            formal_write_blocked=True,
            output_refs=replay.output_refs,
            trace_refs=replay.trace_refs,
            timeline_refs=replay.timeline_refs,
            metadata={
                **replay.metadata,
                "read_only": True,
                "formal_write_blocked": True,
            },
        )

    def get_agent_run_status(self, *, run_id: str, owner_id: str) -> AgentRunStatus:
        if self._should_route_through_executor(run_id=run_id, owner_id=owner_id):
            return self._status_from_execution_status(self._executor.get_status(run_id), owner_id=owner_id)
        status = self._runner.get_status(run_id, owner_id)
        return AgentRunStatus(
            run_id=status.run_id,
            status=status.status,
            owner_id=status.owner_id,
            output_refs=status.output_refs,
            trace_refs=status.trace_refs,
            interrupt_refs=status.interrupt_refs,
            formal_write_blocked=True,
            metadata=sanitize_payload(status.metadata),
        )

    def get_agent_run_timeline(
        self, *, run_id: str, owner_id: str, cursor: str | None = None, limit: int = 50
    ) -> AgentRunTimelinePage:
        if self._should_route_through_executor(run_id=run_id, owner_id=owner_id):
            _require_supported_entrypoint(self._descriptor_for_run(run_id), "timeline")
            return self._timeline_from_execution_timeline(
                self._executor.get_timeline(run_id, cursor=cursor, limit=limit)
            )
        page = self._runner.get_timeline(run_id, owner_id, cursor=cursor, limit=limit)
        return AgentRunTimelinePage(run_id=page.run_id, events=page.events, next_cursor=page.next_cursor)

    def cancel_agent_run(self, *, run_id: str, owner_id: str, reason: str, actor_id: str) -> AgentRunStatus:
        if self._should_route_through_executor(run_id=run_id, owner_id=owner_id):
            _require_supported_entrypoint(self._descriptor_for_run(run_id), "cancel")
            return self._status_from_execution_status(
                self._executor.cancel(run_id, reason=reason, actor_id=actor_id),
                owner_id=owner_id,
            )
        status = self._runner.cancel(run_id, owner_id, reason=reason, actor_id=actor_id)
        return AgentRunStatus(
            run_id=status.run_id,
            status=status.status,
            owner_id=status.owner_id,
            output_refs=status.output_refs,
            trace_refs=status.trace_refs,
            interrupt_refs=status.interrupt_refs,
            formal_write_blocked=True,
            metadata=sanitize_payload(status.metadata),
        )

    def _start_run(
        self,
        *,
        task_type: str,
        owner_id: str,
        actor_id: str,
        input_refs: tuple[str, ...],
        requested_outputs: tuple[str, ...],
        idempotency_key: str,
        command_metadata: dict[str, object] | None = None,
    ) -> AgentTaskStatusRef:
        descriptor = self._registry.get_graph_descriptor(task_type)
        self._registry.validate_requested_outputs(task_type, requested_outputs)
        runtime_decision = self._flag_resolver.resolve_runtime_flag("AIFI_AI_RUNTIME_ENABLED", actor_id=actor_id)
        graph_decision = self._flag_resolver.resolve_graph_flag(descriptor, actor_id=actor_id, caller="facade")
        if not runtime_decision.enabled or not graph_decision.enabled:
            raise GraphDisabledError(f"graph disabled: {descriptor.graph_name}")

        idempotency_key_hash = _hash_text(idempotency_key)
        request_digest = _request_digest(
            owner_id=owner_id,
            actor_id=actor_id,
            task_type=task_type,
            descriptor=descriptor,
            entrypoint="start",
            input_refs=input_refs,
            requested_outputs=requested_outputs,
            idempotency_key_hash=idempotency_key_hash,
        )
        cache_key = (owner_id, task_type, idempotency_key)
        cached = self._idempotency_cache.get(cache_key)
        if cached:
            cached_digest, cached_status = cached
            if cached_digest != request_digest:
                raise RuntimeConflictError("idempotency key reused with different request")
            self._run_owner_ids[cached_status.agent_run_id] = owner_id
            return cached_status

        ai_task_id = "aitask_" + _stable_id(owner_id, task_type, idempotency_key)
        run_id = "arun_" + _stable_id(owner_id, descriptor.graph_name, idempotency_key)
        plan = AgentExecutionPlan(
            plan_id="plan_" + _stable_id(owner_id, task_type, idempotency_key),
            run_id=run_id,
            ai_task_id=ai_task_id,
            agent_id=descriptor.graph_name,
            owner_id=owner_id,
            actor_id=actor_id,
            graph_name=descriptor.graph_name,
            graph_version=descriptor.graph_version,
            objective=f"start {task_type}",
            steps=("start",),
            input_refs=input_refs,
            requested_outputs=requested_outputs,
            idempotency_key=idempotency_key,
            runtime_loop_policy=_runtime_loop_policy(descriptor),
            metadata={
                "task_type": task_type,
                "graph_name": descriptor.graph_name,
                "graph_version": descriptor.graph_version,
                "request_digest": request_digest,
                "idempotency_key_hash": idempotency_key_hash,
                **(command_metadata or {}),
            },
        )
        result = self._executor.start(plan)
        status_ref = self._status_ref_from_execution(ai_task_id=ai_task_id, result=result)
        self._idempotency_cache[cache_key] = (request_digest, status_ref)
        self._run_owner_ids[status_ref.agent_run_id] = owner_id
        self._run_graph_names[status_ref.agent_run_id] = descriptor.graph_name
        return status_ref

    def _should_route_through_executor(self, *, run_id: str, owner_id: str) -> bool:
        known_owner_id = self._run_owner_ids.get(run_id)
        if known_owner_id is None:
            return False
        if known_owner_id != owner_id:
            raise OwnerScopeError("agent run not found for owner")
        return True

    def _descriptor_for_run(self, run_id: str) -> GraphDescriptor:
        graph_name = self._run_graph_names.get(run_id)
        if graph_name is None:
            raise RuntimeValidationError("agent run graph descriptor is required")
        return self._registry.get_graph_descriptor(graph_name)

    def _status_from_execution_status(
        self,
        status: AgentExecutionStatus,
        *,
        owner_id: str,
    ) -> AgentRunStatus:
        metadata = sanitize_payload({**status.metadata, "handoff_refs": status.handoff_refs})
        return AgentRunStatus(
            run_id=status.run_id,
            status=status.status,
            owner_id=owner_id,
            output_refs=status.candidate_refs,
            trace_refs=status.trace_refs,
            interrupt_refs=_metadata_refs(metadata, "interrupt_refs") if isinstance(metadata, dict) else (),
            formal_write_blocked=bool(metadata.get("formal_write_blocked", True)) if isinstance(metadata, dict) else True,
            metadata=metadata if isinstance(metadata, dict) else {},
        )

    def _timeline_from_execution_timeline(self, timeline: AgentExecutionTimeline) -> AgentRunTimelinePage:
        return AgentRunTimelinePage(
            run_id=timeline.run_id,
            events=tuple(_timeline_event_from_execution_trace(trace) for trace in timeline.events),
            next_cursor=timeline.cursor,
        )

    def _status_ref(self, *, ai_task_id: str, result: AgentRunResult) -> AgentTaskStatusRef:
        return AgentTaskStatusRef(
            ai_task_id=ai_task_id,
            agent_run_id=result.run_id,
            status=result.status,
            trace_refs=result.trace_refs,
            candidate_refs=result.output_refs,
            interrupt_refs=result.interrupt_refs,
            formal_refs=(),
            candidate_payloads=result.candidate_payloads,
        )

    def _status_ref_from_execution(self, *, ai_task_id: str, result: AgentExecutionResult) -> AgentTaskStatusRef:
        return AgentTaskStatusRef(
            ai_task_id=ai_task_id,
            agent_run_id=result.run_id,
            status=result.status,
            trace_refs=(result.trace.trace_id, *result.trace.validation_refs, *result.trace.handoff_refs),
            candidate_refs=result.output_refs,
            interrupt_refs=result.interrupt_refs,
            formal_refs=(),
            candidate_payloads=result.candidate_payloads,
        )


def _timeline_event_from_execution_trace(trace: AgentExecutionTrace) -> AgentTimelineEvent:
    metadata = sanitize_payload(
        {
            **trace.metadata,
            "trace_id": trace.trace_id,
            "agent_id": trace.agent_id,
            "agent_version": trace.agent_version,
            "ai_task_id": trace.ai_task_id,
            "input_refs": trace.input_refs,
            "output_refs": trace.output_refs,
            "candidate_refs": trace.candidate_refs,
            "plan_refs": trace.plan_refs,
            "skill_refs": trace.skill_refs,
            "tool_refs": trace.tool_refs,
            "policy_refs": trace.policy_refs,
            "provider_refs": trace.provider_refs,
            "validation_refs": trace.validation_refs,
            "handoff_refs": trace.handoff_refs,
            "low_confidence_flags": trace.low_confidence_flags,
            "failure_reason": trace.failure_reason,
            "fallback_reason": trace.fallback_reason,
            "source_boundary": "AgentGraphRunner",
        }
    )
    summary = str(trace.metadata.get("summary") or "")
    return AgentTimelineEvent(
        event_id=trace.trace_id,
        event_type=trace.events[0] if trace.events else "trace_event",
        summary=summary,
        refs=_unique_refs(
            trace.trace_id,
            *trace.output_refs,
            *trace.candidate_refs,
            *trace.validation_refs,
            *trace.handoff_refs,
            *trace.plan_refs,
            *trace.skill_refs,
            *trace.tool_refs,
            *trace.policy_refs,
            *trace.provider_refs,
        ),
        metadata=metadata if isinstance(metadata, dict) else {},
    )


def _metadata_refs(metadata: dict[str, Any], key: str) -> tuple[str, ...]:
    return _unique_refs(*_coerce_refs(metadata.get(key)))


def _coerce_refs(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        stripped = value.strip()
        return (stripped,) if stripped else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    text = str(value).strip()
    return (text,) if text else ()


def _unique_refs(*refs: object) -> tuple[str, ...]:
    unique: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        for text in _coerce_refs(ref):
            if text not in seen:
                unique.append(text)
                seen.add(text)
    return tuple(unique)


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _runtime_loop_policy_metadata(descriptor: GraphDescriptor) -> dict[str, object]:
    policy = _runtime_loop_policy(descriptor)
    return {
        "max_steps": policy.max_steps,
        "max_retries": policy.max_retries,
        "timeout_seconds": policy.timeout_seconds,
        "stop_conditions": policy.stop_conditions,
        "allowed_tools": policy.allowed_tools,
        "allowed_callers": policy.allowed_callers,
        "side_effect_policy": policy.side_effect_policy,
    }


def _runtime_loop_policy(descriptor: GraphDescriptor) -> AgentRuntimeLoopPolicy:
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
        raise RuntimeValidationError(f"invalid runtime loop policy for {descriptor.graph_name}: {exc}") from exc


def _require_supported_entrypoint(descriptor: GraphDescriptor, entrypoint: str) -> None:
    if entrypoint not in descriptor.supported_entrypoints:
        raise RuntimeValidationError(f"unsupported graph entrypoint: {descriptor.graph_name}.{entrypoint}")


def _sanitize_resume_payload(resume_payload: dict[str, Any]) -> dict[str, object]:
    sanitized_payload = sanitize_payload(resume_payload)
    if not isinstance(sanitized_payload, dict):
        raise RuntimeValidationError("resume payload must be an object")
    action = sanitized_payload.get("action")
    if not isinstance(action, str) or action not in _ALLOWED_RESUME_ACTIONS:
        raise RuntimeValidationError("unsupported resume action")
    return sanitized_payload


def _request_digest(
    *,
    owner_id: str,
    actor_id: str,
    task_type: str,
    descriptor: GraphDescriptor,
    entrypoint: str,
    input_refs: tuple[str, ...],
    requested_outputs: tuple[str, ...],
    idempotency_key_hash: str,
) -> str:
    body = {
        "owner_id": owner_id,
        "actor_id": actor_id,
        "task_type": task_type,
        "graph_name": descriptor.graph_name,
        "graph_version": descriptor.graph_version,
        "entrypoint": entrypoint,
        "input_refs": input_refs,
        "requested_outputs": requested_outputs,
        "idempotency_key_hash": idempotency_key_hash,
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
