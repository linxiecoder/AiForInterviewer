"""AI Runtime orchestration facade contract."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.application.ai_runtime.contracts import (
    AgentCommandEnvelope,
    AgentGraphRunner,
    AgentRunContext,
    AgentRunResult,
    AgentRunStatus,
    AgentRunTimelinePage,
    AgentTaskStatusRef,
    GraphDisabledError,
    RuntimeConflictError,
    RuntimeValidationError,
    sanitize_payload,
)
from app.application.ai_runtime.registry import GraphDescriptor
from app.application.ai_runtime.registry import AgentGraphRegistry
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver


class AiOrchestrationFacade:
    def __init__(
        self,
        *,
        runner: AgentGraphRunner,
        registry: AgentGraphRegistry | None = None,
        flag_resolver: RuntimeFlagResolver | None = None,
    ) -> None:
        self._runner = runner
        self._registry = registry or AgentGraphRegistry.default()
        self._flag_resolver = flag_resolver or RuntimeFlagResolver()
        self._idempotency_cache: dict[tuple[str, str, str], tuple[str, AgentTaskStatusRef]] = {}

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
    ) -> AgentTaskStatusRef:
        return self._start_run(
            task_type="polish_question_generation",
            owner_id=owner_id,
            actor_id=actor_id,
            input_refs=(session_ref, *progress_node_refs, *completed_focus_refs),
            requested_outputs=("candidate_refs",),
            idempotency_key=idempotency_key,
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
        resume_payload: dict[str, Any],
        base_version: int,
        idempotency_key: str,
    ) -> AgentTaskStatusRef:
        if not owner_id or not interrupt_ref or not idempotency_key:
            raise RuntimeValidationError("owner, interrupt ref, and idempotency key are required")
        if base_version < 0:
            raise RuntimeValidationError("base version must be non-negative")
        descriptor = self._registry.get_graph_descriptor(graph_name)
        runtime_decision = self._flag_resolver.resolve_runtime_flag("AIFI_AI_RUNTIME_ENABLED", actor_id=actor_id)
        graph_decision = self._flag_resolver.resolve_graph_flag(descriptor, actor_id=actor_id, caller="facade")
        if not runtime_decision.enabled or not graph_decision.enabled:
            raise GraphDisabledError(f"graph disabled: {descriptor.graph_name}")
        command = AgentCommandEnvelope(
            entrypoint="resume",
            input_refs=(interrupt_ref,),
            requested_outputs=("candidate_refs", "suggestion_refs", "interrupt_refs"),
            idempotency_key=idempotency_key,
            metadata={"base_version": base_version},
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
        result = self._runner.resume(context, interrupt_ref=interrupt_ref, resume_payload=sanitize_payload(resume_payload))
        return self._status_ref(ai_task_id=ai_task_id, result=result)

    def get_agent_run_status(self, *, run_id: str, owner_id: str) -> AgentRunStatus:
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
        page = self._runner.get_timeline(run_id, owner_id, cursor=cursor, limit=limit)
        return AgentRunTimelinePage(run_id=page.run_id, events=page.events, next_cursor=page.next_cursor)

    def cancel_agent_run(self, *, run_id: str, owner_id: str, reason: str, actor_id: str) -> AgentRunStatus:
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
            return cached_status

        ai_task_id = "aitask_" + _stable_id(owner_id, task_type, idempotency_key)
        run_id = "arun_" + _stable_id(owner_id, descriptor.graph_name, idempotency_key)
        command = AgentCommandEnvelope(
            entrypoint="start",
            input_refs=input_refs,
            requested_outputs=requested_outputs,
            idempotency_key=idempotency_key,
            metadata={
                "task_type": task_type,
                "graph_name": descriptor.graph_name,
                "graph_version": descriptor.graph_version,
                "request_digest": request_digest,
                "idempotency_key_hash": idempotency_key_hash,
            },
        )
        context = AgentRunContext(
            owner_id=owner_id,
            actor_id=actor_id,
            run_id=run_id,
            ai_task_id=ai_task_id,
            graph_name=descriptor.graph_name,
            graph_version=descriptor.graph_version,
            command=command,
        )
        result = self._runner.start(context, command)
        status_ref = self._status_ref(ai_task_id=ai_task_id, result=result)
        self._idempotency_cache[cache_key] = (request_digest, status_ref)
        return status_ref

    def _status_ref(self, *, ai_task_id: str, result: AgentRunResult) -> AgentTaskStatusRef:
        return AgentTaskStatusRef(
            ai_task_id=ai_task_id,
            agent_run_id=result.run_id,
            status=result.status,
            trace_refs=result.trace_refs,
            candidate_refs=result.output_refs,
            interrupt_refs=result.interrupt_refs,
            formal_refs=(),
        )


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
