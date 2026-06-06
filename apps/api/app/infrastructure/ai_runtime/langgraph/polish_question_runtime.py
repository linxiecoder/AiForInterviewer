"""Polish question graph runtime with provider-ready drafting path."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.application.ai_runtime.business_graphs.polish_question_graph import (
    POLISH_QUESTION_GRAPH_NAME,
    build_polish_question_candidate_from_draft,
    build_polish_question_graph_descriptor,
    run_polish_question_agent,
)
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
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.application.llm.ports import LlmTransport
from app.application.polish.question_generation_service import QuestionGenerationService
from app.infrastructure.ai_runtime.langgraph.checkpointer import RefsOnlyLangGraphCheckpointer
from app.infrastructure.ai_runtime.langgraph.serializer import (
    LangGraphRuntimeSerializer,
    build_agent_candidate_payload_from_runtime_output,
)


class _PolishQuestionGraphState(TypedDict):
    owner_id: str
    run_id: str
    entrypoint: str
    steps: list[str]
    provider_calls: int
    db_business_writes: int
    formal_business_writes: int


class _PolishQuestionGraphTransport:
    def __init__(self, transport: LlmTransport, *, source_context: dict[str, Any]) -> None:
        self._transport = transport
        self._source_context = source_context

    def generate(self, request):
        evidence_bundle = request.evidence_bundle
        if isinstance(evidence_bundle, dict):
            input_data = evidence_bundle.get("input_data")
            if isinstance(input_data, dict):
                evidence_bundle = {
                    **evidence_bundle,
                    "input_data": {**input_data, "source_context": self._source_context},
                }
        return self._transport.generate(
            replace(
                request,
                evidence_bundle=evidence_bundle,
                graph_name=POLISH_QUESTION_GRAPH_NAME,
                node_name="question_drafting",
            )
        )


class PolishQuestionGraphRuntime:
    """Dedicated runtime for the Polish question graph start path."""

    _checkpoint_namespace = "pr5_polish_question_fake_runtime"

    def __init__(
        self,
        *,
        flag_resolver: RuntimeFlagResolver | None = None,
        checkpointer: RefsOnlyLangGraphCheckpointer | None = None,
        serializer: LangGraphRuntimeSerializer | None = None,
        polish_question_llm_transport: LlmTransport | None = None,
        status_store: dict[tuple[str, str], AgentRunStatus] | None = None,
        timeline_store: dict[tuple[str, str], list[AgentTimelineEvent]] | None = None,
        interrupt_service: AgentInterruptService | None = None,
    ) -> None:
        self._flag_resolver = flag_resolver or RuntimeFlagResolver()
        self._checkpointer = checkpointer or RefsOnlyLangGraphCheckpointer()
        self._serializer = serializer or LangGraphRuntimeSerializer()
        self._polish_question_llm_transport = polish_question_llm_transport
        self._interrupt_service = interrupt_service or AgentInterruptService()
        self._compiled_graph = self._compile_graph()
        self._statuses = status_store if status_store is not None else {}
        self._timelines = timeline_store if timeline_store is not None else {}
        self._candidate_payloads: dict[tuple[str, str], tuple[AgentCandidatePayload, ...]] = {}

    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        if command != context.command:
            raise RuntimePolicyError("command must match context command")
        runtime_gate = self._require_runtime_enabled(context)
        descriptor = build_polish_question_graph_descriptor()
        graph_decision = self._flag_resolver.resolve_graph_flag(
            descriptor, actor_id=context.actor_id, caller="runner_entry"
        )
        if not graph_decision.enabled:
            raise GraphDisabledError(f"graph disabled: {descriptor.graph_name}")
        if context.graph_version != descriptor.graph_version:
            raise RuntimePolicyError(
                "context graph version does not match polish question in-memory runtime"
            )

        state = self._invoke_graph(context=context, entrypoint="polish_question_fake_start")
        checkpoint = self._record_checkpoint(context=context, state=state)
        agent_result = run_polish_question_agent(
            context,
            command,
            flag_resolver=self._flag_resolver,
            provider_draft_operation=(
                self._polish_question_provider_draft if runtime_gate["provider_gate_enabled"] else None
            ),
        )
        agent_payload = agent_result.candidate_payloads[0]
        candidate = agent_payload.payload
        candidate_ref = agent_payload.candidate_ref
        candidate_trace_refs = tuple(str(ref) for ref in agent_result.trace_refs if str(ref).strip())
        validation_refs = tuple(ref for ref in candidate_trace_refs if ref.startswith("validation_ref_"))
        result_ref = next(
            (ref for ref in agent_result.output_refs if ref != candidate_ref),
            agent_result.output_refs[0],
        )
        trace_refs = (checkpoint.checkpoint_ref, *candidate_trace_refs)
        payload = build_agent_candidate_payload_from_runtime_output(
            {
                "candidate_ref": candidate_ref,
                "candidate_type": agent_payload.candidate_type,
                "payload_schema_id": agent_payload.payload_schema_id,
                "payload": candidate,
                "status": agent_payload.status,
                "trace_refs": (checkpoint.checkpoint_ref, *candidate_trace_refs),
                "validation_refs": validation_refs,
                "low_confidence_flags": (),
            }
        )
        metadata = sanitize_payload(
            {
                **agent_result.metadata,
                "descriptor_graph_version": descriptor.graph_version,
                "trace_refs": {
                    "checkpoint_refs": [checkpoint.checkpoint_ref],
                    "validation_refs": list(validation_refs),
                },
            }
        )
        command_trace_metadata = _command_trace_event_metadata(command)
        events = self._timeline_for(context)
        events.extend(
            (
                _event(
                    "run_started",
                    "polish question agent runtime started",
                    refs=(context.ai_task_id,),
                    metadata=_with_command_trace_event_metadata(None, command_trace_metadata),
                ),
                _event(
                    "checkpoint_recorded",
                    "checkpoint ref recorded",
                    refs=(checkpoint.checkpoint_ref,),
                    metadata={"checkpoint_refs": (checkpoint.checkpoint_ref,)},
                ),
                _event(
                    "validation_recorded",
                    "validation ref recorded",
                    refs=validation_refs,
                    metadata={"validation_refs": validation_refs},
                ),
                _event(
                    "candidate_payload_emitted",
                    "polish question candidate payload emitted",
                    refs=(candidate_ref,),
                    metadata={
                        "candidate_type": payload.candidate_type,
                        "candidate_refs": (candidate_ref,),
                        "output_refs": (candidate_ref,),
                        "payload_schema_id": payload.payload_schema_id,
                        "status": payload.status,
                        "validation_refs": validation_refs,
                    },
                ),
            )
        )
        hitl_triggers = _hitl_triggers_from_metadata(command.metadata)
        checkpoint_base_version = len(self._checkpointer.list_refs(context.owner_id, context.run_id))
        hitl_interrupts = tuple(
            self._interrupt_service.create_hitl_interrupt(
                owner_id=context.owner_id,
                actor_id=context.actor_id,
                run_id=context.run_id,
                node_name="polish_question_fake_start",
                interrupt_type=trigger["interrupt_type"],
                checkpoint_ref=checkpoint.checkpoint_ref,
                base_version=checkpoint_base_version,
                candidate_refs=(candidate_ref,),
                validation_refs=validation_refs,
                low_confidence_flags=payload.low_confidence_flags,
                drawer_payload={
                    "trigger_ref": trigger["trigger_ref"],
                    "decision_point": "polish_question_fake_start",
                },
            )
            for trigger in hitl_triggers
        )
        hitl_interrupt_refs = tuple(interrupt.interrupt_id for interrupt in hitl_interrupts)
        if hitl_interrupt_refs:
            events.append(
                _event(
                    "interrupt_opened",
                    "polish question runtime HITL interrupt opened",
                    refs=hitl_interrupt_refs,
                    metadata=_with_command_trace_event_metadata(
                        {
                            "interrupt_refs": hitl_interrupt_refs,
                            "checkpoint_refs": (checkpoint.checkpoint_ref,),
                            "candidate_refs": (candidate_ref,),
                            "validation_refs": validation_refs,
                        },
                        command_trace_metadata,
                    ),
                )
            )
        else:
            events.append(
                _event(
                    "run_succeeded",
                    "polish question agent runtime succeeded",
                    refs=(result_ref, candidate_ref),
                    metadata=_with_command_trace_event_metadata(
                        {
                            "output_refs": (result_ref, candidate_ref),
                            "candidate_refs": (candidate_ref,),
                            "validation_refs": validation_refs,
                        },
                        command_trace_metadata,
                    ),
                )
            )
        result = AgentRunResult(
            run_id=context.run_id,
            status="interrupted" if hitl_interrupt_refs else agent_result.status,
            output_refs=(result_ref, candidate_ref),
            trace_refs=trace_refs,
            interrupt_refs=hitl_interrupt_refs,
            formal_refs=(),
            candidate_payloads=(payload,),
            metadata={**metadata, "hitl_interrupt_refs": list(hitl_interrupt_refs)},
        )
        self._statuses[(context.owner_id, context.run_id)] = AgentRunStatus(
            run_id=context.run_id,
            status=result.status,
            owner_id=context.owner_id,
            output_refs=result.output_refs,
            trace_refs=result.trace_refs,
            interrupt_refs=result.interrupt_refs,
            formal_write_blocked=True,
            metadata=result.metadata,
        )
        self._candidate_payloads[(context.owner_id, context.run_id)] = result.candidate_payloads
        self._serializer.serialize_run_result(result)
        return result

    def resume(
        self, context: AgentRunContext, interrupt_ref: str, resume_payload: dict[str, object]
    ) -> AgentRunResult:
        self._require_runtime_enabled(context)
        status = self._require_status(context.owner_id, context.run_id)
        if interrupt_ref not in status.interrupt_refs:
            raise RuntimePolicyError("unknown interrupt ref for run")
        sanitized_resume = sanitize_payload(resume_payload)
        if not isinstance(sanitized_resume, dict):
            raise RuntimeValidationError("resume payload must be an object")
        checkpoint_ref = sanitized_resume.get("checkpoint_ref")
        base_version = sanitized_resume.get("base_version")
        idempotency_key = sanitized_resume.get("idempotency_key")
        if not isinstance(checkpoint_ref, str) or not checkpoint_ref.strip():
            raise RuntimeValidationError("checkpoint_ref is required for interrupt resume")
        if type(base_version) is not int:
            raise RuntimeValidationError("base_version is required for interrupt resume")
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise RuntimeValidationError("idempotency_key is required for interrupt resume")
        resume_body = {
            key: value
            for key, value in sanitized_resume.items()
            if key not in {"checkpoint_ref", "base_version", "idempotency_key"}
        }
        resume_status = self._interrupt_service.resume_interrupt(
            run_id=context.run_id,
            interrupt_id=interrupt_ref,
            owner_id=context.owner_id,
            actor_id=context.actor_id,
            resume_payload=resume_body,
            base_version=base_version,
            idempotency_key=idempotency_key.strip(),
            checkpoint_ref=checkpoint_ref.strip(),
        )
        candidate_payloads = self._candidate_payloads.get((context.owner_id, context.run_id), ())
        command_trace_metadata = _command_trace_event_metadata(context.command)
        events = self._timeline_for(context)
        events.extend(
            (
                _event(
                    "run_resumed",
                    "polish question runtime resumed from HITL interrupt",
                    refs=(interrupt_ref,),
                    metadata=_with_command_trace_event_metadata(
                        {
                            "resume": resume_body,
                            "interrupt_refs": (interrupt_ref,),
                            "checkpoint_refs": status.trace_refs,
                        },
                        command_trace_metadata,
                    ),
                ),
                _event(
                    "run_succeeded",
                    "polish question runtime resumed as candidate-only result",
                    refs=status.output_refs,
                    metadata=_with_command_trace_event_metadata(
                        {
                            "output_refs": status.output_refs,
                            "candidate_refs": tuple(payload.candidate_ref for payload in candidate_payloads),
                            "validation_refs": tuple(
                                ref for ref in status.trace_refs if ref.startswith("validation_ref_")
                            ),
                            "resume_trace_refs": resume_status.trace_refs,
                        },
                        command_trace_metadata,
                    ),
                ),
            )
        )
        result = AgentRunResult(
            run_id=context.run_id,
            status="succeeded",
            output_refs=status.output_refs,
            trace_refs=status.trace_refs,
            formal_refs=(),
            candidate_payloads=candidate_payloads,
            metadata={**status.metadata, "resume_action": str(resume_body.get("action") or "").strip()},
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
        return self._require_status(owner_id, run_id)

    def get_timeline(
        self, run_id: str, owner_id: str, cursor: str | None = None, limit: int = 50
    ) -> AgentRunTimelinePage:
        events = tuple(self._timelines.get((owner_id, run_id), []))
        if cursor:
            events = tuple(event for event in events if event.event_id > cursor)
        page = AgentRunTimelinePage(run_id=run_id, events=events[:limit], next_cursor=None)
        self._serializer.serialize_timeline_page(page)
        return page

    def cancel(self, run_id: str, owner_id: str, reason: str, actor_id: str) -> AgentRunStatus:
        existing = self._require_status(owner_id, run_id)
        metadata_trace_refs = (
            existing.metadata.get("trace_refs") if isinstance(existing.metadata, dict) else None
        )
        checkpoint_refs = (
            tuple(str(ref) for ref in metadata_trace_refs.get("checkpoint_refs", ()) if ref)
            if isinstance(metadata_trace_refs, dict)
            else ()
        ) or tuple(ref for ref in existing.trace_refs if str(ref).startswith("ackpt_")) or existing.trace_refs
        validation_refs = (
            tuple(str(ref) for ref in metadata_trace_refs.get("validation_refs", ()) if ref)
            if isinstance(metadata_trace_refs, dict)
            else ()
        ) or tuple(ref for ref in existing.trace_refs if str(ref).startswith("validation_ref_"))
        cancel_metadata = {
            "reason": sanitize_payload(reason),
            "actor_id": sanitize_payload(actor_id),
            "output_refs": existing.output_refs,
            "candidate_refs": existing.output_refs,
            "checkpoint_refs": checkpoint_refs,
            "provider_calls": 0,
            "formal_business_writes": 0,
        }
        if validation_refs:
            cancel_metadata["validation_refs"] = validation_refs
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
                refs=(*existing.output_refs, *checkpoint_refs, *validation_refs),
                metadata=cancel_metadata,
            )
        )
        return status

    def _compile_graph(self):
        graph = StateGraph(_PolishQuestionGraphState)
        graph.add_node("polish_question_runtime_node", _polish_question_runtime_node)
        graph.add_edge(START, "polish_question_runtime_node")
        graph.add_edge("polish_question_runtime_node", END)
        return graph.compile()

    def _invoke_graph(
        self, *, context: AgentRunContext, entrypoint: str
    ) -> _PolishQuestionGraphState:
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
        self, *, context: AgentRunContext, state: _PolishQuestionGraphState
    ):
        state_hash = _hash_payload(state)
        return self._checkpointer.record_ref(
            owner_id=context.owner_id,
            actor_id=context.actor_id,
            agent_run_id=context.run_id,
            agent_node_run_id=None,
            graph_name=context.graph_name,
            graph_version=context.graph_version,
            node_name="polish_question_fake_start",
            checkpoint_namespace=self._checkpoint_namespace,
            thread_id=context.run_id,
            checkpoint_id="ckpt_"
            + _stable_id(context.owner_id, context.run_id, "polish_question_fake_start", state_hash),
            state_hash=state_hash,
            metadata={"retention_ref": "retention_pr5_polish_question_fake"},
        )

    def _polish_question_provider_draft(
        self,
        *,
        context: AgentRunContext,
        command: AgentCommandEnvelope,
        retrieved_context: dict[str, Any],
        scenario: dict[str, Any],
    ) -> dict[str, Any]:
        if self._polish_question_llm_transport is None:
            raise RuntimePolicyError("polish question provider path requires an LLM transport")
        snapshot = command.metadata.get("polish_question_context_snapshot")
        if not isinstance(snapshot, dict):
            raise RuntimePolicyError("polish question provider path requires a context snapshot")
        progress_context = snapshot.get("progress_context")
        progress_tree_plan = snapshot.get("progress_tree_plan")
        progress_tree_state = snapshot.get("progress_tree_state")
        if (
            not isinstance(progress_context, dict)
            or not isinstance(progress_tree_plan, dict)
            or not isinstance(progress_tree_state, dict)
        ):
            raise RuntimePolicyError("polish question provider context snapshot is incomplete")
        service = QuestionGenerationService(
            llm_transport=_PolishQuestionGraphTransport(
                self._polish_question_llm_transport,
                source_context={
                    "context_source": retrieved_context.get("context_source"),
                    "context_source_version": retrieved_context.get("context_source_version"),
                    **(
                        retrieved_context.get("source_refs")
                        if isinstance(retrieved_context.get("source_refs"), dict)
                        else {}
                    ),
                },
            )
        )
        result = service.generate(
            session=None,
            context=progress_context,
            plan=progress_tree_plan,
            state=progress_tree_state,
            requested_ref=str(
                snapshot.get("requested_progress_node_ref")
                or retrieved_context.get("progress_node_ref")
                or ""
            ),
            follow_up_context=(
                snapshot.get("follow_up_context")
                if isinstance(snapshot.get("follow_up_context"), dict)
                and snapshot.get("follow_up_context")
                else None
            ),
        )
        if not result.succeeded or result.draft is None:
            raise RuntimePolicyError(
                "polish question provider generation failed: "
                + ",".join(result.validation_errors or ("unknown",))
            )
        draft_metadata = result.draft.question_metadata
        if (
            draft_metadata.get("provider_status") == "fake_transport"
            or str(draft_metadata.get("llm_generation_mode") or "").startswith("deterministic")
        ):
            raise RuntimePolicyError("polish question provider path requires a non-fake provider transport")
        trace_refs = tuple(
            str(ref)
            for ref in draft_metadata.get("llm_trace_refs", ())
            if str(ref).strip()
        )
        return {
            "candidate": build_polish_question_candidate_from_draft(
                owner_id=context.owner_id,
                run_id=context.run_id,
                ai_task_id=context.ai_task_id,
                session_ref=str(retrieved_context.get("session_ref") or ""),
                draft=result.draft,
                scenario=scenario,
                provider_trace_refs=trace_refs,
            )
        }

    def _require_runtime_enabled(self, context: AgentRunContext) -> dict[str, Any]:
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


def _polish_question_runtime_node(
    state: _PolishQuestionGraphState,
) -> _PolishQuestionGraphState:
    return {
        "owner_id": state["owner_id"],
        "run_id": state["run_id"],
        "entrypoint": state["entrypoint"],
        "steps": [*state["steps"], "langgraph_invoked"],
        "provider_calls": 0,
        "db_business_writes": 0,
        "formal_business_writes": 0,
    }


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


def _with_command_trace_event_metadata(
    metadata: dict[str, Any] | None, command_metadata: dict[str, Any]
) -> dict[str, Any]:
    merged = dict(metadata or {})
    _merge_command_trace_event_metadata(merged, command_metadata)
    return merged


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


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(sanitize_payload(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:16]


def _hitl_triggers_from_metadata(metadata: dict[str, Any]) -> tuple[dict[str, str], ...]:
    trigger_keys = (
        ("formal_write_attempt_ref", "formal_write_attempt"),
        ("asset_conflict_ref", "asset_conflict"),
        ("low_confidence_formal_update_ref", "low_confidence_formal_update"),
        ("ambiguous_ownership_ref", "ambiguous_ownership"),
        ("validation_failed_partial_result_ref", "validation_failed_partial_result"),
    )
    triggers: list[dict[str, str]] = []
    for metadata_key, interrupt_type in trigger_keys:
        trigger_ref = metadata.get(metadata_key)
        if isinstance(trigger_ref, str) and trigger_ref.strip():
            triggers.append({"interrupt_type": interrupt_type, "trigger_ref": trigger_ref.strip()})
    return tuple(triggers)
