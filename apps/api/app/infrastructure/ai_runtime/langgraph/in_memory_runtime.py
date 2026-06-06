"""In-memory LangGraph runtime shell with deterministic fallback paths."""

from __future__ import annotations

import hashlib
import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.application.agents.contracts import AgentRuntimeLoopPolicy
from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentCommandEnvelope,
    AgentReplayResult,
    AgentRunContext,
    AgentRunResult,
    AgentRunStatus,
    AgentRunTimelinePage,
    AgentTimelineEvent,
    GraphDisabledError,
    OwnerScopeError,
    RuntimePolicyError,
    RuntimeValidationError,
    classify_agent_runtime_status,
    sanitize_payload,
)
from app.application.ai_runtime.interrupts import AgentInterruptService
from app.application.ai_runtime.business_graphs.polish_feedback_graph import (
    POLISH_FEEDBACK_GRAPH_NAME,
    build_polish_feedback_fake_runtime_payload,
    build_polish_feedback_graph_descriptor,
)
from app.application.ai_runtime.business_graphs.polish_question_graph import (
    POLISH_QUESTION_GRAPH_NAME,
)
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.application.llm.ports import LlmTransport
from app.infrastructure.ai_runtime.langgraph.checkpointer import RefsOnlyLangGraphCheckpointer
from app.infrastructure.ai_runtime.langgraph.polish_question_runtime import PolishQuestionGraphRuntime
from app.infrastructure.ai_runtime.langgraph.serializer import (
    LangGraphRuntimeSerializer,
)


class _InMemoryGraphState(TypedDict):
    owner_id: str
    run_id: str
    entrypoint: str
    steps: list[str]
    provider_calls: int
    db_business_writes: int
    formal_business_writes: int


class InMemoryLangGraphRuntime:
    """In-memory runtime shell with deterministic fallback paths."""

    _checkpoint_namespace = "pr4_fake_runtime"
    _polish_feedback_checkpoint_namespace = "pr6_polish_feedback_fake_runtime"

    def __init__(
        self,
        *,
        flag_resolver: RuntimeFlagResolver | None = None,
        checkpointer: RefsOnlyLangGraphCheckpointer | None = None,
        serializer: LangGraphRuntimeSerializer | None = None,
        interrupt_service: AgentInterruptService | None = None,
        polish_question_llm_transport: LlmTransport | None = None,
        polish_question_runtime: PolishQuestionGraphRuntime | None = None,
    ) -> None:
        self._flag_resolver = flag_resolver or RuntimeFlagResolver()
        self._checkpointer = checkpointer or RefsOnlyLangGraphCheckpointer()
        self._serializer = serializer or LangGraphRuntimeSerializer()
        self._interrupt_service = interrupt_service or AgentInterruptService()
        self._compiled_graph = self._compile_graph()
        self._statuses: dict[tuple[str, str], AgentRunStatus] = {}
        self._timelines: dict[tuple[str, str], list[AgentTimelineEvent]] = {}
        self._polish_question_runtime = polish_question_runtime or PolishQuestionGraphRuntime(
            flag_resolver=self._flag_resolver,
            checkpointer=self._checkpointer,
            serializer=self._serializer,
            polish_question_llm_transport=polish_question_llm_transport,
            status_store=self._statuses,
            timeline_store=self._timelines,
            interrupt_service=self._interrupt_service,
        )

    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        if command != context.command:
            raise RuntimePolicyError("command must match context command")
        if context.graph_name == POLISH_FEEDBACK_GRAPH_NAME:
            return self._start_polish_feedback_fake(context=context, command=command)
        if context.graph_name == POLISH_QUESTION_GRAPH_NAME:
            return self._polish_question_runtime.start(context, command)
        gate = self._require_runtime_enabled(context)
        _require_direct_runtime_loop_policy(command)
        state = self._invoke_graph(context=context, entrypoint="start")
        checkpoint = self._record_checkpoint(context=context, node_name="fake_start", state=state)
        checkpoint_base_version = len(self._checkpointer.list_refs(context.owner_id, context.run_id))
        interrupt = self._interrupt_service.create_interrupt(
            owner_id=context.owner_id,
            actor_id=context.actor_id,
            run_id=context.run_id,
            node_name="fake_start",
            interrupt_type="runtime_checkpoint_resume",
            resume_schema_id="agent.resume.user_confirmation.v1",
            checkpoint_ref=checkpoint.checkpoint_ref,
            base_version=checkpoint_base_version,
            drawer_payload={
                "checkpoint_ref": checkpoint.checkpoint_ref,
                "formal_write_blocked": True,
            },
        )
        interrupt_ref = interrupt.interrupt_id
        events = self._timeline_for(context)
        events.extend(
            (
                _event(
                    "run_started",
                    "in-memory runtime run started",
                    refs=(context.ai_task_id,),
                    metadata={
                        "ai_task_id": context.ai_task_id,
                        "input_refs": context.command.input_refs,
                        **_command_trace_event_metadata(context.command),
                    },
                ),
                _event(
                    "checkpoint_recorded",
                    "checkpoint ref recorded",
                    refs=(checkpoint.checkpoint_ref,),
                    metadata={"checkpoint_refs": (checkpoint.checkpoint_ref,)},
                ),
                _event(
                    "interrupt_opened",
                    "in-memory runtime interrupt opened",
                    refs=(interrupt_ref,),
                    metadata={
                        "interrupt_refs": (interrupt_ref,),
                        "checkpoint_refs": (checkpoint.checkpoint_ref,),
                    },
                ),
            )
        )
        result = AgentRunResult(
            run_id=context.run_id,
            status="interrupted",
            trace_refs=(checkpoint.checkpoint_ref,),
            interrupt_refs=(interrupt_ref,),
            formal_refs=(),
            metadata=_runtime_metadata(state, gate),
        )
        self._statuses[(context.owner_id, context.run_id)] = AgentRunStatus(
            run_id=context.run_id,
            status="interrupted",
            owner_id=context.owner_id,
            trace_refs=result.trace_refs,
            interrupt_refs=result.interrupt_refs,
            formal_write_blocked=True,
            metadata=result.metadata,
        )
        self._serializer.serialize_run_result(result)
        return result

    def resume(
        self, context: AgentRunContext, interrupt_ref: str, resume_payload: dict[str, object]
    ) -> AgentRunResult:
        if context.graph_name == POLISH_QUESTION_GRAPH_NAME:
            return self._polish_question_runtime.resume(context, interrupt_ref, resume_payload)
        gate = self._require_runtime_enabled(context)
        sanitized_resume = sanitize_payload(resume_payload)
        if not isinstance(sanitized_resume, dict):
            raise RuntimeValidationError("resume payload must be an object")
        status = self._require_status(context.owner_id, context.run_id)
        if interrupt_ref not in status.interrupt_refs:
            raise RuntimePolicyError("unknown interrupt ref for run")
        service_interrupt = self._interrupt_service.get_interrupt(interrupt_ref, owner_id=context.owner_id)
        if service_interrupt is not None:
            checkpoint_ref = sanitized_resume.get("checkpoint_ref")
            base_version = sanitized_resume.get("base_version")
            idempotency_key = sanitized_resume.get("idempotency_key")
            if not isinstance(checkpoint_ref, str) or not checkpoint_ref.strip():
                raise RuntimeValidationError("checkpoint_ref is required for interrupt resume")
            if type(base_version) is not int:
                raise RuntimeValidationError("base_version is required for interrupt resume")
            if not isinstance(idempotency_key, str) or not idempotency_key.strip():
                raise RuntimeValidationError("idempotency_key is required for interrupt resume")
            sanitized_resume = {
                key: value
                for key, value in sanitized_resume.items()
                if key not in {"checkpoint_ref", "base_version", "idempotency_key"}
            }
            self._interrupt_service.resume_interrupt(
                run_id=context.run_id,
                interrupt_id=interrupt_ref,
                owner_id=context.owner_id,
                actor_id=context.actor_id,
                resume_payload=sanitized_resume,
                base_version=base_version,
                idempotency_key=idempotency_key.strip(),
                checkpoint_ref=checkpoint_ref.strip(),
            )
        state = self._invoke_graph(context=context, entrypoint="resume")
        checkpoint = self._record_checkpoint(context=context, node_name="fake_resume", state=state)
        output_ref = "candidate_ref_" + _stable_id(context.owner_id, context.run_id, "resume")
        events = self._timeline_for(context)
        status_metadata = status.metadata if isinstance(status.metadata, dict) else {}
        output_refs_metadata = (
            status_metadata.get("output_refs") if isinstance(status_metadata.get("output_refs"), dict) else {}
        )
        trace_refs_metadata = (
            status_metadata.get("trace_refs") if isinstance(status_metadata.get("trace_refs"), dict) else {}
        )
        checkpoint_refs = tuple(
            str(ref).strip()
            for ref in trace_refs_metadata.get("checkpoint_refs", ())
            if str(ref).strip()
        ) or tuple(ref for ref in status.trace_refs if str(ref).startswith("ackpt_")) or status.trace_refs
        candidate_refs = tuple(
            str(ref).strip()
            for ref in output_refs_metadata.get("candidate_refs", ())
            if str(ref).strip()
        )
        validation_refs = tuple(
            str(ref).strip()
            for ref in trace_refs_metadata.get("validation_refs", ())
            if str(ref).strip()
        )
        command_trace_metadata = _command_trace_event_metadata(context.command)
        resume_event_metadata: dict[str, Any] = {
            "resume": sanitized_resume,
            "interrupt_refs": (interrupt_ref,),
            "checkpoint_refs": checkpoint_refs,
        }
        if candidate_refs:
            resume_event_metadata["candidate_refs"] = candidate_refs
        if validation_refs:
            resume_event_metadata["validation_refs"] = validation_refs
        _merge_command_trace_event_metadata(resume_event_metadata, command_trace_metadata)
        trace_refs = tuple(ref.checkpoint_ref for ref in self._checkpointer.list_refs(context.owner_id, context.run_id))
        succeeded_event_metadata: dict[str, Any] = {
            "output_refs": (output_ref,),
            "candidate_refs": (output_ref,),
            "checkpoint_refs": trace_refs,
        }
        _merge_command_trace_event_metadata(succeeded_event_metadata, command_trace_metadata)
        events.extend(
            (
                _event(
                    "run_resumed",
                    "in-memory runtime resumed from sanitized payload",
                    refs=(interrupt_ref,),
                    metadata=resume_event_metadata,
                ),
                _event(
                    "checkpoint_recorded",
                    "checkpoint ref recorded",
                    refs=(checkpoint.checkpoint_ref,),
                    metadata={"checkpoint_refs": (checkpoint.checkpoint_ref,)},
                ),
                _event(
                    "run_succeeded",
                    "in-memory runtime run succeeded",
                    refs=(output_ref,),
                    metadata=succeeded_event_metadata,
                ),
            )
        )
        result = AgentRunResult(
            run_id=context.run_id,
            status="succeeded",
            output_refs=(output_ref,),
            trace_refs=trace_refs,
            formal_refs=(),
            metadata=_runtime_metadata(state, gate),
        )
        self._statuses[(context.owner_id, context.run_id)] = AgentRunStatus(
            run_id=context.run_id,
            status="succeeded",
            owner_id=context.owner_id,
            output_refs=result.output_refs,
            trace_refs=result.trace_refs,
            interrupt_refs=(),
            formal_write_blocked=True,
            metadata=result.metadata,
        )
        self._serializer.serialize_run_result(result)
        return result

    def replay(self, context: AgentRunContext, checkpoint_ref: str) -> AgentReplayResult:
        if context.graph_name == POLISH_QUESTION_GRAPH_NAME:
            return self._polish_question_runtime.replay(context, checkpoint_ref)
        self._require_runtime_enabled(context)
        checkpoint = self._checkpointer.get_by_ref(context.owner_id, checkpoint_ref)
        if checkpoint is None:
            raise RuntimePolicyError("checkpoint ref not found for owner")
        timeline = self.get_timeline(context.run_id, context.owner_id)
        status = self._statuses.get((context.owner_id, context.run_id))
        timeline_refs = tuple(event.event_id for event in timeline.events)
        return AgentReplayResult(
            run_id=context.run_id,
            status=_replay_status_from_original(status.status if status is not None else ""),
            read_only=True,
            formal_write_blocked=True,
            trace_refs=(checkpoint.checkpoint_ref,),
            timeline_refs=timeline_refs,
            metadata=_replay_metadata_from_status(
                status=status,
                checkpoint_ref=checkpoint.checkpoint_ref,
                timeline_refs=timeline_refs,
            ),
        )

    def get_status(self, run_id: str, owner_id: str) -> AgentRunStatus:
        try:
            return self._require_status(owner_id, run_id)
        except OwnerScopeError:
            return self._polish_question_runtime.get_status(run_id, owner_id)

    def get_timeline(
        self, run_id: str, owner_id: str, cursor: str | None = None, limit: int = 50
    ) -> AgentRunTimelinePage:
        events = self._timelines.get((owner_id, run_id))
        if events is None:
            return self._polish_question_runtime.get_timeline(run_id, owner_id, cursor=cursor, limit=limit)
        resolved_events = tuple(events)
        if cursor:
            resolved_events = tuple(event for event in resolved_events if event.event_id > cursor)
        page = AgentRunTimelinePage(run_id=run_id, events=resolved_events[:limit], next_cursor=None)
        self._serializer.serialize_timeline_page(page)
        return page

    def cancel(self, run_id: str, owner_id: str, reason: str, actor_id: str) -> AgentRunStatus:
        try:
            existing = self._require_status(owner_id, run_id)
        except OwnerScopeError:
            return self._polish_question_runtime.cancel(run_id, owner_id, reason=reason, actor_id=actor_id)
        metadata_output_refs = existing.metadata.get("output_refs") if isinstance(existing.metadata, dict) else None
        metadata_trace_refs = existing.metadata.get("trace_refs") if isinstance(existing.metadata, dict) else None
        metadata_candidate_refs = (
            tuple(str(ref) for ref in metadata_output_refs.get("candidate_refs", ()) if ref)
            if isinstance(metadata_output_refs, dict)
            else ()
        )
        validation_refs = (
            tuple(str(ref) for ref in metadata_trace_refs.get("validation_refs", ()) if ref)
            if isinstance(metadata_trace_refs, dict)
            else ()
        )
        is_polish_feedback_status = (
            existing.metadata.get("graph_name") == POLISH_FEEDBACK_GRAPH_NAME
            if isinstance(existing.metadata, dict)
            else False
        )
        if is_polish_feedback_status:
            checkpoint_refs = (
                tuple(str(ref) for ref in metadata_trace_refs.get("checkpoint_refs", ()) if ref)
                if isinstance(metadata_trace_refs, dict)
                else ()
            ) or tuple(ref for ref in existing.trace_refs if str(ref).startswith("ackpt_")) or existing.trace_refs
            validation_refs_to_add = validation_refs
            candidate_refs = metadata_candidate_refs or existing.output_refs
            timeline_refs = tuple(dict.fromkeys((*existing.output_refs, *checkpoint_refs, *validation_refs_to_add)))
        else:
            checkpoint_refs = (
                tuple(str(ref) for ref in metadata_trace_refs.get("checkpoint_refs", ()) if ref)
                if isinstance(metadata_trace_refs, dict)
                else ()
            ) or tuple(ref for ref in existing.trace_refs if str(ref).startswith("ackpt_")) or existing.trace_refs
            validation_refs_to_add = validation_refs or tuple(
                ref for ref in existing.trace_refs if str(ref).startswith("validation_ref_")
            )
            candidate_refs = metadata_candidate_refs if validation_refs_to_add and metadata_candidate_refs else existing.output_refs
            timeline_refs = (*existing.output_refs, *checkpoint_refs, *validation_refs_to_add)
        cancel_metadata = {
            "reason": sanitize_payload(reason),
            "actor_id": sanitize_payload(actor_id),
            "output_refs": existing.output_refs,
            "candidate_refs": candidate_refs,
            "checkpoint_refs": checkpoint_refs,
            "provider_calls": 0,
            "formal_business_writes": 0,
        }
        if validation_refs_to_add:
            cancel_metadata["validation_refs"] = validation_refs_to_add
        status = AgentRunStatus(
            run_id=run_id,
            status="cancelled",
            owner_id=owner_id,
            output_refs=existing.output_refs,
            trace_refs=existing.trace_refs,
            interrupt_refs=(),
            formal_write_blocked=True,
            metadata={"reason": sanitize_payload(reason), "provider_calls": 0, "formal_business_writes": 0},
        )
        self._statuses[(owner_id, run_id)] = status
        self._timelines.setdefault((owner_id, run_id), []).append(
            _event(
                "run_cancelled",
                "Runtime run cancelled",
                refs=timeline_refs,
                metadata=cancel_metadata,
            )
        )
        return status

    def _compile_graph(self):
        graph = StateGraph(_InMemoryGraphState)
        graph.add_node("in_memory_runtime_node", _in_memory_runtime_node)
        graph.add_edge(START, "in_memory_runtime_node")
        graph.add_edge("in_memory_runtime_node", END)
        return graph.compile()

    def _invoke_graph(self, *, context: AgentRunContext, entrypoint: str) -> _InMemoryGraphState:
        return self._compiled_graph.invoke(
            {
                "owner_id": context.owner_id,
                "run_id": context.run_id,
                "entrypoint": entrypoint,
                "steps": [entrypoint],
                "provider_calls": 0,
                "db_business_writes": 0,
                "formal_business_writes": 0,
            }
        )

    def _record_checkpoint(
        self, *, context: AgentRunContext, node_name: str, state: _InMemoryGraphState
    ):
        state_hash = _hash_payload(state)
        return self._checkpointer.record_ref(
            owner_id=context.owner_id,
            actor_id=context.actor_id,
            agent_run_id=context.run_id,
            agent_node_run_id=None,
            graph_name=context.graph_name,
            graph_version=context.graph_version,
            node_name=node_name,
            checkpoint_namespace=self._checkpoint_namespace,
            thread_id=context.run_id,
            checkpoint_id="ckpt_" + _stable_id(context.owner_id, context.run_id, node_name, state_hash),
            state_hash=state_hash,
            metadata={"retention_ref": "retention_pr4_fake"},
        )

    def _start_polish_feedback_fake(
        self, *, context: AgentRunContext, command: AgentCommandEnvelope
    ) -> AgentRunResult:
        self._require_runtime_enabled(context)
        descriptor = build_polish_feedback_graph_descriptor()
        graph_decision = self._flag_resolver.resolve_graph_flag(
            descriptor, actor_id=context.actor_id, caller="runner_entry"
        )
        if not graph_decision.enabled:
            raise GraphDisabledError(f"graph disabled: {descriptor.graph_name}")
        _require_descriptor_runtime_loop_policy(command=command, descriptor=descriptor)

        state = self._invoke_graph(context=context, entrypoint="polish_feedback_fake_start")
        checkpoint = self._record_polish_feedback_checkpoint(context=context, state=state)
        command_trace_metadata = _command_trace_event_metadata(command)
        payload_command = _command_without_runtime_control_metadata(command)
        payload_context = _context_with_command(context, payload_command)
        payload = build_polish_feedback_fake_runtime_payload(
            context=payload_context,
            command=payload_command,
            checkpoint_refs=(checkpoint.checkpoint_ref,),
        )
        result_ref = tuple(payload["output_refs"]["result_refs"])
        candidate_ref = tuple(payload["output_refs"]["candidate_refs"])
        feedback_candidate_ref = candidate_ref[0]
        asset_update_candidate_refs = tuple(payload["output_refs"].get("asset_update_candidate_refs", ()))
        checkpoint_refs = tuple(payload["trace_refs"]["checkpoint_refs"])
        validation_refs = tuple(payload["trace_refs"]["validation_refs"])
        low_confidence_refs = tuple(payload["trace_refs"]["low_confidence_refs"])
        candidate_trace_refs = (*checkpoint_refs, *validation_refs)
        feedback_candidate_payload = AgentCandidatePayload(
            candidate_ref=feedback_candidate_ref,
            candidate_type="feedback_candidate",
            payload_schema_id="polish_feedback_candidate.v1",
            payload={
                "candidate_ref": feedback_candidate_ref,
                "result_ref": result_ref[0],
                "input_refs": payload["input_refs"],
                "asset_update_candidate_refs": list(asset_update_candidate_refs),
                "feedback_metadata": {
                    "graph_name": payload["graph_name"],
                    "graph_version": payload["graph_version"],
                    "handoff_contract": "handoff.polish_feedback_agent.v1",
                    "checkpoint_refs": list(checkpoint_refs),
                    "validation_refs": list(validation_refs),
                    "formal_write_blocked": True,
                    "asset_update_formal_write_performed": False,
                },
                "sanitized": True,
            },
            status="accepted",
            trace_refs=candidate_trace_refs,
            validation_refs=validation_refs,
        )
        asset_update_candidate_payloads = tuple(
            AgentCandidatePayload(
                candidate_ref=asset_candidate_ref,
                candidate_type="asset_update_candidate",
                payload_schema_id="polish_asset_update_candidate.v1",
                payload={
                    "candidate_ref": asset_candidate_ref,
                    "candidate_type": "project_asset_update_candidate",
                    "asset_body_ref": _asset_body_ref_from_candidate(asset_candidate_ref),
                    "asset_schema_id": "project_asset.update_candidate.v1",
                    "source_feedback_candidate_ref": feedback_candidate_ref,
                    "handoff_contract": "handoff.polish_feedback_agent.v1",
                    "formal_write_blocked_until": "user_confirmation",
                    "user_confirmation_required": True,
                    "validation_refs": list(validation_refs),
                    "trace_refs": list(candidate_trace_refs),
                    "formal_refs": [],
                    "sanitized": True,
                },
                status="requires_user_confirmation",
                trace_refs=candidate_trace_refs,
                validation_refs=validation_refs,
            )
            for asset_candidate_ref in asset_update_candidate_refs
        )
        checkpoint_base_version = len(self._checkpointer.list_refs(context.owner_id, context.run_id))
        hitl_interrupts = tuple(
            self._interrupt_service.create_hitl_interrupt(
                owner_id=context.owner_id,
                actor_id=context.actor_id,
                run_id=context.run_id,
                node_name="polish_feedback_fake_start",
                interrupt_type=str(trigger["interrupt_type"]),
                checkpoint_ref=checkpoint_refs[0],
                base_version=checkpoint_base_version,
                candidate_refs=candidate_ref,
                validation_refs=validation_refs,
                low_confidence_flags=(
                    low_confidence_refs
                    if trigger["interrupt_type"] == "low_confidence_formal_update"
                    else ()
                ),
                drawer_payload={
                    "trigger_ref": trigger["trigger_ref"],
                    "decision_point": "polish_feedback_fake_start",
                },
            )
            for trigger in payload.get("hitl_triggers", ())
        )
        hitl_interrupt_refs = tuple(interrupt.interrupt_id for interrupt in hitl_interrupts)
        result_status = "interrupted" if hitl_interrupt_refs else payload["status"]
        runtime_metadata = {
            **payload,
            "hitl_interrupt_refs": list(hitl_interrupt_refs),
        }
        events = self._timeline_for(context)
        run_started_metadata = {
            "ai_task_id": context.ai_task_id,
            "input_refs": context.command.input_refs,
        }
        _merge_command_trace_event_metadata(run_started_metadata, command_trace_metadata)
        events.extend(
            (
                _event(
                    "run_started",
                    "polish feedback in-memory runtime started",
                    refs=(context.ai_task_id,),
                    metadata=run_started_metadata,
                ),
                _event(
                    "checkpoint_recorded",
                    "checkpoint ref recorded",
                    refs=checkpoint_refs,
                    metadata={"checkpoint_refs": checkpoint_refs},
                ),
                _event(
                    "validation_recorded",
                    "validation ref recorded",
                    refs=validation_refs,
                    metadata={"validation_refs": validation_refs, "candidate_refs": candidate_ref},
                ),
            )
        )
        if hitl_interrupt_refs:
            interrupt_metadata = {
                "trigger_types": tuple(interrupt.interrupt_type for interrupt in hitl_interrupts),
                "interrupt_refs": hitl_interrupt_refs,
                "candidate_refs": candidate_ref,
                "validation_refs": validation_refs,
            }
            _merge_command_trace_event_metadata(interrupt_metadata, command_trace_metadata)
            events.append(
                _event(
                    "interrupt_opened",
                    "polish feedback HITL interrupt opened",
                    refs=hitl_interrupt_refs,
                    metadata=interrupt_metadata,
                )
            )
        else:
            run_succeeded_metadata = {
                "output_refs": (*result_ref, *candidate_ref),
                "candidate_refs": candidate_ref,
                "validation_refs": validation_refs,
            }
            _merge_command_trace_event_metadata(run_succeeded_metadata, command_trace_metadata)
            events.append(
                _event(
                    "run_succeeded",
                    "polish feedback in-memory runtime succeeded",
                    refs=(*result_ref, *candidate_ref),
                    metadata=run_succeeded_metadata,
                )
            )
        result = AgentRunResult(
            run_id=context.run_id,
            status=result_status,
            output_refs=(*result_ref, *candidate_ref),
            trace_refs=checkpoint_refs,
            interrupt_refs=hitl_interrupt_refs,
            formal_refs=(),
            candidate_payloads=(feedback_candidate_payload, *asset_update_candidate_payloads),
            metadata=runtime_metadata,
        )
        self._statuses[(context.owner_id, context.run_id)] = AgentRunStatus(
            run_id=context.run_id,
            status=result.status,
            owner_id=context.owner_id,
            output_refs=result.output_refs,
            trace_refs=candidate_trace_refs,
            interrupt_refs=hitl_interrupt_refs,
            formal_write_blocked=True,
            metadata=runtime_metadata,
        )
        self._serializer.serialize_run_result(result)
        return result

    def _record_polish_feedback_checkpoint(
        self, *, context: AgentRunContext, state: _InMemoryGraphState
    ):
        state_hash = _hash_payload(state)
        return self._checkpointer.record_ref(
            owner_id=context.owner_id,
            actor_id=context.actor_id,
            agent_run_id=context.run_id,
            agent_node_run_id=None,
            graph_name=context.graph_name,
            graph_version=context.graph_version,
            node_name="polish_feedback_fake_start",
            checkpoint_namespace=self._polish_feedback_checkpoint_namespace,
            thread_id=context.run_id,
            checkpoint_id="ckpt_"
            + _stable_id(context.owner_id, context.run_id, "polish_feedback_fake_start", state_hash),
            state_hash=state_hash,
            metadata={"retention_ref": "retention_pr6_polish_feedback_fake"},
        )

    def _require_runtime_enabled(self, context: AgentRunContext) -> dict[str, bool]:
        runtime_decision = self._flag_resolver.resolve_runtime_flag(
            "AIFI_AI_RUNTIME_ENABLED", actor_id=context.actor_id
        )
        langgraph_decision = self._flag_resolver.resolve_runtime_flag(
            "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED", actor_id=context.actor_id
        )
        if not runtime_decision.enabled or not langgraph_decision.enabled:
            raise GraphDisabledError("in-memory LangGraph runtime is disabled")
        provider_decision = self._flag_resolver.is_real_provider_enabled(actor_id=context.actor_id)
        return {
            "runtime_enabled": runtime_decision.enabled,
            "langgraph_enabled": langgraph_decision.enabled,
            "provider_gate_enabled": provider_decision.enabled,
            "provider_gate_source": provider_decision.source,
        }

    def _require_status(self, owner_id: str, run_id: str) -> AgentRunStatus:
        status = self._statuses.get((owner_id, run_id))
        if status is None:
            raise OwnerScopeError("agent run not found for owner")
        return status

    def _timeline_for(self, context: AgentRunContext) -> list[AgentTimelineEvent]:
        return self._timelines.setdefault((context.owner_id, context.run_id), [])


def _in_memory_runtime_node(state: _InMemoryGraphState) -> _InMemoryGraphState:
    return {
        "owner_id": state["owner_id"],
        "run_id": state["run_id"],
        "entrypoint": state["entrypoint"],
        "steps": [*state["steps"], "langgraph_invoked"],
        "provider_calls": 0,
        "db_business_writes": 0,
        "formal_business_writes": 0,
    }


def _runtime_metadata(state: _InMemoryGraphState, gate: dict[str, bool]) -> dict[str, Any]:
    return {
        "runtime_enabled": gate["runtime_enabled"],
        "langgraph_enabled": gate["langgraph_enabled"],
        "provider_gate_enabled": gate["provider_gate_enabled"],
        "provider_calls": state["provider_calls"],
        "db_business_writes": state["db_business_writes"],
        "formal_business_writes": state["formal_business_writes"],
        "steps": tuple(state["steps"]),
    }


def _command_trace_event_metadata(command: AgentCommandEnvelope) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for key in (
        "plan_refs",
        "skill_refs",
        "tool_refs",
        "policy_refs",
        "provider_refs",
        "validation_refs",
        "handoff_refs",
        "low_confidence_flags",
    ):
        refs = _metadata_refs(command.metadata, key)
        if refs:
            metadata[key] = refs

    for key in ("failure_reason", "fallback_reason"):
        value = sanitize_payload(command.metadata.get(key))
        if isinstance(value, str) and value.strip():
            metadata[key] = value.strip()
    return metadata


def _merge_command_trace_event_metadata(target: dict[str, Any], command_metadata: dict[str, Any]) -> None:
    for key, value in command_metadata.items():
        if key in {"failure_reason", "fallback_reason"}:
            target.setdefault(key, value)
            continue
        existing = target.get(key)
        if isinstance(existing, tuple) and isinstance(value, tuple):
            target[key] = tuple(dict.fromkeys((*existing, *value)))
            continue
        target.setdefault(key, value)


def _metadata_refs(metadata: dict[str, Any], key: str) -> tuple[str, ...]:
    value = metadata.get(key)
    if value is None:
        return ()
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _require_descriptor_runtime_loop_policy(*, command: AgentCommandEnvelope, descriptor: Any) -> None:
    policy = command.metadata.get("runtime_loop_policy")
    if not isinstance(policy, dict):
        raise RuntimeValidationError(f"runtime_loop_policy is required for {descriptor.graph_name}")
    expected = {
        "max_steps": descriptor.runtime_max_steps,
        "max_retries": descriptor.runtime_max_retries,
        "timeout_seconds": descriptor.runtime_timeout_seconds,
        "stop_conditions": descriptor.runtime_stop_conditions,
        "allowed_tools": descriptor.runtime_allowed_tools,
        "allowed_callers": descriptor.runtime_allowed_callers,
        "side_effect_policy": descriptor.runtime_side_effect_policy,
    }
    for key, expected_value in expected.items():
        if key not in policy:
            raise RuntimeValidationError(f"runtime_loop_policy.{key} is required for {descriptor.graph_name}")
        actual_value = policy[key]
        if key in {"stop_conditions", "allowed_tools", "allowed_callers"}:
            actual_value = _runtime_loop_policy_tuple_field(actual_value, field_name=key)
        elif key in {"max_steps", "max_retries", "timeout_seconds"} and isinstance(actual_value, bool):
            raise RuntimeValidationError(f"runtime_loop_policy.{key} mismatch for {descriptor.graph_name}")
        if actual_value != expected_value:
            raise RuntimeValidationError(f"runtime_loop_policy.{key} mismatch for {descriptor.graph_name}")


def _runtime_loop_policy_tuple_field(value: object, *, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise RuntimeValidationError(f"runtime_loop_policy.{field_name} must be a sequence")
    values = tuple(value)
    if any(not isinstance(item, str) or not item.strip() for item in values):
        raise RuntimeValidationError(f"runtime_loop_policy.{field_name} must contain strings")
    return values


def _require_direct_runtime_loop_policy(command: AgentCommandEnvelope) -> None:
    policy = command.metadata.get("runtime_loop_policy")
    if not isinstance(policy, dict):
        raise RuntimeValidationError("runtime_loop_policy is required for direct runtime start")
    try:
        AgentRuntimeLoopPolicy(
            max_steps=_runtime_loop_policy_int_field(policy.get("max_steps"), field_name="max_steps"),
            max_retries=_runtime_loop_policy_int_field(policy.get("max_retries"), field_name="max_retries"),
            timeout_seconds=_runtime_loop_policy_int_field(
                policy.get("timeout_seconds"),
                field_name="timeout_seconds",
            ),
            stop_conditions=_runtime_loop_policy_tuple_field(
                policy.get("stop_conditions"),
                field_name="stop_conditions",
            ),
            allowed_tools=_runtime_loop_policy_tuple_field(
                policy.get("allowed_tools"),
                field_name="allowed_tools",
            ),
            allowed_callers=_runtime_loop_policy_tuple_field(
                policy.get("allowed_callers"),
                field_name="allowed_callers",
            ),
            side_effect_policy=_runtime_loop_policy_string_field(
                policy.get("side_effect_policy"),
                field_name="side_effect_policy",
            ),
        )
    except ValueError as exc:
        raise RuntimeValidationError(f"runtime_loop_policy invalid: {exc}") from exc


def _runtime_loop_policy_int_field(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeValidationError(f"runtime_loop_policy.{field_name} must be an integer")
    return value


def _runtime_loop_policy_string_field(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeValidationError(f"runtime_loop_policy.{field_name} must be a non-empty string")
    return value


def _command_without_runtime_loop_policy(command: AgentCommandEnvelope) -> AgentCommandEnvelope:
    if "runtime_loop_policy" not in command.metadata:
        return command
    metadata = {key: value for key, value in command.metadata.items() if key != "runtime_loop_policy"}
    return AgentCommandEnvelope(
        entrypoint=command.entrypoint,
        input_refs=command.input_refs,
        requested_outputs=command.requested_outputs,
        idempotency_key=command.idempotency_key,
        replay_mode=command.replay_mode,
        metadata=metadata,
    )


def _command_without_runtime_control_metadata(command: AgentCommandEnvelope) -> AgentCommandEnvelope:
    control_keys = {
        "runtime_loop_policy",
        "plan_refs",
        "skill_refs",
        "tool_refs",
        "policy_refs",
        "provider_refs",
        "validation_refs",
        "handoff_refs",
        "low_confidence_flags",
        "failure_reason",
        "fallback_reason",
    }
    metadata = {key: value for key, value in command.metadata.items() if key not in control_keys}
    if metadata == command.metadata:
        return command
    return AgentCommandEnvelope(
        entrypoint=command.entrypoint,
        input_refs=command.input_refs,
        requested_outputs=command.requested_outputs,
        idempotency_key=command.idempotency_key,
        replay_mode=command.replay_mode,
        metadata=metadata,
    )


def _context_with_command(context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunContext:
    if command == context.command:
        return context
    return AgentRunContext(
        owner_id=context.owner_id,
        actor_id=context.actor_id,
        run_id=context.run_id,
        ai_task_id=context.ai_task_id,
        graph_name=context.graph_name,
        graph_version=context.graph_version,
        command=command,
    )


def _replay_status_from_original(original_status: str) -> str:
    if not str(original_status).strip():
        return "replayed"
    category = classify_agent_runtime_status(original_status)
    if category in {"failed", "blocked", "interrupted", "cancelled"}:
        return f"replayed_{category}"
    return "replayed"


def _replay_metadata_from_status(
    *,
    status: AgentRunStatus | None,
    checkpoint_ref: str,
    timeline_refs: tuple[str, ...],
) -> dict[str, object]:
    status_metadata = status.metadata if status is not None and isinstance(status.metadata, dict) else {}
    status_metadata_trace_refs = _trace_refs_metadata_from_status_metadata(status_metadata)
    original_status = status.status if status is not None else ""
    original_category = classify_agent_runtime_status(original_status) if original_status else ""
    status_trace_refs = status.trace_refs if status is not None else ()
    metadata: dict[str, object] = {
        "replay_mode": "read_only",
        "original_status": original_status,
        "original_status_category": original_category,
        "replay_trace_match": bool(status_trace_refs and checkpoint_ref in status_trace_refs),
        "replay_compared_trace_refs": tuple(dict.fromkeys((checkpoint_ref, *status_trace_refs))),
        "timeline_refs": timeline_refs,
        "provider_calls": 0,
        "tool_calls": 0,
        "repository_writes": 0,
        "formal_business_writes": 0,
    }
    if status_metadata_trace_refs:
        metadata["trace_refs"] = status_metadata_trace_refs
        _merge_trace_refs_metadata(metadata, status_metadata_trace_refs)
    for key in (
        "failure_reason",
        "fallback_reason",
        "validation_refs",
        "tool_refs",
        "handoff_refs",
        "policy_refs",
        "provider_refs",
        "low_confidence_flags",
    ):
        value = status_metadata.get(key)
        if value:
            metadata[key] = value
    if original_category in {"failed", "blocked"} and not metadata.get("failure_reason"):
        metadata["failure_reason"] = original_status
    return metadata


def _trace_refs_metadata_from_status_metadata(status_metadata: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    trace_refs = status_metadata.get("trace_refs")
    if not isinstance(trace_refs, dict):
        return {}
    result: dict[str, tuple[str, ...]] = {}
    for key in (
        "checkpoint_refs",
        "validation_refs",
        "handoff_refs",
        "tool_refs",
        "policy_refs",
        "provider_refs",
        "low_confidence_refs",
        "low_confidence_flags",
    ):
        if key in trace_refs:
            result[key] = _metadata_ref_values(trace_refs.get(key))
    return result


def _merge_trace_refs_metadata(metadata: dict[str, object], trace_refs: dict[str, tuple[str, ...]]) -> None:
    for nested_key, metadata_key in (
        ("validation_refs", "validation_refs"),
        ("handoff_refs", "handoff_refs"),
        ("tool_refs", "tool_refs"),
        ("policy_refs", "policy_refs"),
        ("provider_refs", "provider_refs"),
        ("low_confidence_refs", "low_confidence_flags"),
        ("low_confidence_flags", "low_confidence_flags"),
    ):
        if nested_key in trace_refs:
            refs = trace_refs.get(nested_key, ())
            metadata[metadata_key] = tuple(dict.fromkeys((*_metadata_ref_values(metadata.get(metadata_key)), *refs)))


def _metadata_ref_values(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _event(
    event_type: str,
    summary: str,
    *,
    refs: tuple[str, ...] = (),
    metadata: dict[str, Any] | None = None,
) -> AgentTimelineEvent:
    return AgentTimelineEvent(
        event_id="evt_" + _stable_id(event_type, summary, "::".join(refs), json.dumps(metadata or {}, sort_keys=True)),
        event_type=event_type,
        summary=summary,
        refs=refs,
        metadata=metadata or {},
    )


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(sanitize_payload(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _asset_body_ref_from_candidate(asset_candidate_ref: str) -> str:
    suffix = asset_candidate_ref.removeprefix("asset_update_candidate_ref_")
    return "asset_body_ref_" + suffix


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:16]
