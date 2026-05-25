"""Deterministic PR4 fake LangGraph runtime."""

from __future__ import annotations

import hashlib
import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

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
    contains_sensitive_payload,
    sanitize_payload,
)
from app.application.ai_runtime.business_graphs.polish_feedback_graph import (
    POLISH_FEEDBACK_GRAPH_NAME,
    build_polish_feedback_fake_runtime_payload,
    build_polish_feedback_graph_descriptor,
)
from app.application.ai_runtime.business_graphs.polish_question_graph import (
    POLISH_QUESTION_GRAPH_NAME,
    build_polish_question_candidate_readonly,
    build_polish_question_graph_descriptor,
    derive_question_scenario,
)
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.langgraph.checkpointer import RefsOnlyLangGraphCheckpointer
from app.infrastructure.ai_runtime.langgraph.serializer import LangGraphRuntimeSerializer


class _FakeGraphState(TypedDict):
    owner_id: str
    run_id: str
    entrypoint: str
    steps: list[str]
    provider_calls: int
    db_business_writes: int
    formal_business_writes: int


class FakeLangGraphRuntime:
    """A provider-free, deterministic runtime implementing the PR3 runner port."""

    _checkpoint_namespace = "pr4_fake_runtime"
    _polish_feedback_checkpoint_namespace = "pr6_polish_feedback_fake_runtime"
    _polish_question_checkpoint_namespace = "pr5_polish_question_fake_runtime"

    def __init__(
        self,
        *,
        flag_resolver: RuntimeFlagResolver | None = None,
        checkpointer: RefsOnlyLangGraphCheckpointer | None = None,
        serializer: LangGraphRuntimeSerializer | None = None,
    ) -> None:
        self._flag_resolver = flag_resolver or RuntimeFlagResolver()
        self._checkpointer = checkpointer or RefsOnlyLangGraphCheckpointer()
        self._serializer = serializer or LangGraphRuntimeSerializer()
        self._compiled_graph = self._compile_graph()
        self._statuses: dict[tuple[str, str], AgentRunStatus] = {}
        self._timelines: dict[tuple[str, str], list[AgentTimelineEvent]] = {}

    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult:
        if command != context.command:
            raise RuntimePolicyError("command must match context command")
        if context.graph_name == POLISH_FEEDBACK_GRAPH_NAME:
            return self._start_polish_feedback_fake(context=context, command=command)
        if context.graph_name == POLISH_QUESTION_GRAPH_NAME:
            return self._start_polish_question_fake(context=context, command=command)
        gate = self._require_runtime_enabled(context)
        state = self._invoke_graph(context=context, entrypoint="start")
        checkpoint = self._record_checkpoint(context=context, node_name="fake_start", state=state)
        interrupt_ref = "aint_" + _stable_id(context.owner_id, context.run_id, "interrupt")
        events = self._timeline_for(context)
        events.extend(
            (
                _event("run_started", "fake runtime run started", refs=(context.ai_task_id,)),
                _event("checkpoint_recorded", "checkpoint ref recorded", refs=(checkpoint.checkpoint_ref,)),
                _event("interrupt_opened", "fake runtime interrupt opened", refs=(interrupt_ref,)),
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
        gate = self._require_runtime_enabled(context)
        sanitized_resume = sanitize_payload(resume_payload)
        status = self._require_status(context.owner_id, context.run_id)
        if interrupt_ref not in status.interrupt_refs:
            raise RuntimePolicyError("unknown interrupt ref for run")
        state = self._invoke_graph(context=context, entrypoint="resume")
        checkpoint = self._record_checkpoint(context=context, node_name="fake_resume", state=state)
        output_ref = "candidate_ref_" + _stable_id(context.owner_id, context.run_id, "resume")
        events = self._timeline_for(context)
        events.extend(
            (
                _event("run_resumed", "fake runtime resumed from sanitized payload", refs=(interrupt_ref,), metadata={"resume": sanitized_resume}),
                _event("checkpoint_recorded", "checkpoint ref recorded", refs=(checkpoint.checkpoint_ref,)),
                _event("run_succeeded", "fake runtime run succeeded", refs=(output_ref,)),
            )
        )
        trace_refs = tuple(ref.checkpoint_ref for ref in self._checkpointer.list_refs(context.owner_id, context.run_id))
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
        self._require_runtime_enabled(context)
        checkpoint = self._checkpointer.get_by_ref(context.owner_id, checkpoint_ref)
        if checkpoint is None:
            raise RuntimePolicyError("checkpoint ref not found for owner")
        timeline = self.get_timeline(context.run_id, context.owner_id)
        return AgentReplayResult(
            run_id=context.run_id,
            status="replayed",
            read_only=True,
            formal_write_blocked=True,
            trace_refs=(checkpoint.checkpoint_ref,),
            timeline_refs=tuple(event.event_id for event in timeline.events),
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
        return status

    def _compile_graph(self):
        graph = StateGraph(_FakeGraphState)
        graph.add_node("fake_runtime_node", _fake_runtime_node)
        graph.add_edge(START, "fake_runtime_node")
        graph.add_edge("fake_runtime_node", END)
        return graph.compile()

    def _invoke_graph(self, *, context: AgentRunContext, entrypoint: str) -> _FakeGraphState:
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
        self, *, context: AgentRunContext, node_name: str, state: _FakeGraphState
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

        state = self._invoke_graph(context=context, entrypoint="polish_feedback_fake_start")
        checkpoint = self._record_polish_feedback_checkpoint(context=context, state=state)
        payload = build_polish_feedback_fake_runtime_payload(
            context=context,
            command=command,
            checkpoint_refs=(checkpoint.checkpoint_ref,),
        )
        result_ref = tuple(payload["output_refs"]["result_refs"])
        candidate_ref = tuple(payload["output_refs"]["candidate_refs"])
        checkpoint_refs = tuple(payload["trace_refs"]["checkpoint_refs"])
        validation_refs = tuple(payload["trace_refs"]["validation_refs"])
        events = self._timeline_for(context)
        events.extend(
            (
                _event("run_started", "polish feedback fake runtime started", refs=(context.ai_task_id,)),
                _event("checkpoint_recorded", "checkpoint ref recorded", refs=checkpoint_refs),
                _event("validation_recorded", "validation ref recorded", refs=validation_refs),
                _event("run_succeeded", "polish feedback fake runtime succeeded", refs=(*result_ref, *candidate_ref)),
            )
        )
        result = AgentRunResult(
            run_id=context.run_id,
            status=payload["status"],
            output_refs=(*result_ref, *candidate_ref),
            trace_refs=checkpoint_refs,
            interrupt_refs=(),
            formal_refs=(),
            metadata=payload,
        )
        self._statuses[(context.owner_id, context.run_id)] = AgentRunStatus(
            run_id=context.run_id,
            status=result.status,
            owner_id=context.owner_id,
            output_refs=result.output_refs,
            trace_refs=result.trace_refs,
            interrupt_refs=(),
            formal_write_blocked=True,
            metadata=payload,
        )
        self._serializer.serialize_run_result(result)
        return result

    def _start_polish_question_fake(
        self, *, context: AgentRunContext, command: AgentCommandEnvelope
    ) -> AgentRunResult:
        self._require_runtime_enabled(context)
        descriptor = build_polish_question_graph_descriptor()
        graph_decision = self._flag_resolver.resolve_graph_flag(
            descriptor, actor_id=context.actor_id, caller="runner_entry"
        )
        if not graph_decision.enabled:
            raise GraphDisabledError(f"graph disabled: {descriptor.graph_name}")
        if context.graph_version != descriptor.graph_version:
            raise RuntimePolicyError(
                "context graph version does not match polish question fake runtime"
            )

        state = self._invoke_graph(context=context, entrypoint="polish_question_fake_start")
        checkpoint = self._record_polish_question_checkpoint(context=context, state=state)
        session_ref = _question_session_ref(command)
        progress_node_ref = _question_progress_node_ref(command)
        completed_focus_refs = _question_completed_focus_refs(command)
        context_digest = str(
            command.metadata.get("context_digest")
            or command.metadata.get("request_digest")
            or ""
        )
        scenario_summary = _question_fake_scenario_summary(command, progress_node_ref=progress_node_ref)
        evidence_ref = progress_node_ref or "question_evidence_ref_" + _stable_id(session_ref, context.run_id)
        scenario = derive_question_scenario(
            session_ref=session_ref,
            selected_progress_node_summary=scenario_summary,
            selected_evidence_refs=(evidence_ref,),
            resume_evidence_summaries=(
                {
                    "ref": evidence_ref,
                    "summary": scenario_summary,
                    "source_type": "resume_project",
                },
            ),
            completed_focus_refs=completed_focus_refs,
        )
        candidate = build_polish_question_candidate_readonly(
            owner_id=context.owner_id,
            run_id=context.run_id,
            ai_task_id=context.ai_task_id,
            session_ref=session_ref,
            scenario=scenario,
            progress_node_ref=progress_node_ref,
            context_digest=context_digest,
        )
        quality_gate = dict(candidate["quality_gate"])
        quality_gate.setdefault(
            "status", "accepted" if quality_gate.get("passed") is True else "blocked"
        )
        candidate = sanitize_payload(
            {
                **candidate,
                "quality_gate": quality_gate,
                "question_metadata": {"llm_generation_mode": "graph_candidate_handoff"},
            }
        )
        candidate_ref = str(candidate["candidate_ref"])
        candidate_trace_refs = tuple(
            str(ref) for ref in candidate.get("trace_refs", ()) if str(ref).strip()
        )
        validation_refs = tuple(ref for ref in candidate_trace_refs if ref.startswith("validation_ref_"))
        result_ref = "question_result_ref_" + _stable_id(context.owner_id, context.run_id, candidate_ref)
        trace_refs = (checkpoint.checkpoint_ref, *validation_refs)
        payload = AgentCandidatePayload(
            candidate_ref=candidate_ref,
            candidate_type="polish_question_candidate",
            payload_schema_id="polish_question_candidate.v1",
            payload=candidate,
            status="accepted",
            trace_refs=(checkpoint.checkpoint_ref, *candidate_trace_refs),
            validation_refs=validation_refs,
            low_confidence_flags=(),
        )
        metadata = {
            "graph_name": POLISH_QUESTION_GRAPH_NAME,
            "graph_version": "pr5-c2-fake-runtime",
            "descriptor_graph_version": descriptor.graph_version,
            "status": "fake_runtime_succeeded",
            "runtime_flag_key": descriptor.runtime_flag_key,
            "runtime_flag_source": graph_decision.source,
            "input_refs": {
                "session_ref": session_ref,
                "progress_node_ref": progress_node_ref,
                "completed_focus_refs": list(completed_focus_refs),
            },
            "output_refs": {
                "result_refs": [result_ref],
                "candidate_refs": [candidate_ref],
                "formal_refs": [],
            },
            "trace_refs": {
                "checkpoint_refs": [checkpoint.checkpoint_ref],
                "validation_refs": list(validation_refs),
            },
            "provider_calls": 0,
            "db_business_writes": 0,
            "formal_business_writes": 0,
            "counters": {
                "provider_calls": 0,
                "db_business_writes": 0,
                "formal_business_writes": 0,
            },
            "checkpoint_refs_are_business_facts": False,
            "sanitized": True,
            "accepted_candidate_payload": True,
        }
        events = self._timeline_for(context)
        events.extend(
            (
                _event("run_started", "polish question fake runtime started", refs=(context.ai_task_id,)),
                _event("checkpoint_recorded", "checkpoint ref recorded", refs=(checkpoint.checkpoint_ref,)),
                _event("validation_recorded", "validation ref recorded", refs=validation_refs),
                _event(
                    "candidate_payload_emitted",
                    "polish question candidate payload emitted",
                    refs=(candidate_ref,),
                    metadata={
                        "candidate_type": payload.candidate_type,
                        "payload_schema_id": payload.payload_schema_id,
                        "status": payload.status,
                    },
                ),
                _event(
                    "run_succeeded",
                    "polish question fake runtime succeeded",
                    refs=(result_ref, candidate_ref),
                ),
            )
        )
        result = AgentRunResult(
            run_id=context.run_id,
            status="fake_runtime_succeeded",
            output_refs=(result_ref, candidate_ref),
            trace_refs=trace_refs,
            interrupt_refs=(),
            formal_refs=(),
            candidate_payloads=(payload,),
            metadata=metadata,
        )
        self._statuses[(context.owner_id, context.run_id)] = AgentRunStatus(
            run_id=context.run_id,
            status=result.status,
            owner_id=context.owner_id,
            output_refs=result.output_refs,
            trace_refs=result.trace_refs,
            interrupt_refs=(),
            formal_write_blocked=True,
            metadata=result.metadata,
        )
        self._serializer.serialize_run_result(result)
        return result

    def _record_polish_feedback_checkpoint(
        self, *, context: AgentRunContext, state: _FakeGraphState
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

    def _record_polish_question_checkpoint(
        self, *, context: AgentRunContext, state: _FakeGraphState
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
            checkpoint_namespace=self._polish_question_checkpoint_namespace,
            thread_id=context.run_id,
            checkpoint_id="ckpt_"
            + _stable_id(context.owner_id, context.run_id, "polish_question_fake_start", state_hash),
            state_hash=state_hash,
            metadata={"retention_ref": "retention_pr5_polish_question_fake"},
        )

    def _require_runtime_enabled(self, context: AgentRunContext) -> dict[str, bool]:
        runtime_decision = self._flag_resolver.resolve_runtime_flag(
            "AIFI_AI_RUNTIME_ENABLED", actor_id=context.actor_id
        )
        langgraph_decision = self._flag_resolver.resolve_runtime_flag(
            "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED", actor_id=context.actor_id
        )
        if not runtime_decision.enabled or not langgraph_decision.enabled:
            raise GraphDisabledError("PR4 fake runtime is disabled")
        provider_decision = self._flag_resolver.is_real_provider_enabled(actor_id=context.actor_id)
        return {
            "runtime_enabled": runtime_decision.enabled,
            "langgraph_enabled": langgraph_decision.enabled,
            "provider_gate_enabled": provider_decision.enabled,
        }

    def _require_status(self, owner_id: str, run_id: str) -> AgentRunStatus:
        status = self._statuses.get((owner_id, run_id))
        if status is None:
            raise OwnerScopeError("agent run not found for owner")
        return status

    def _timeline_for(self, context: AgentRunContext) -> list[AgentTimelineEvent]:
        return self._timelines.setdefault((context.owner_id, context.run_id), [])


def _question_session_ref(command: AgentCommandEnvelope) -> str:
    if not command.input_refs:
        raise RuntimePolicyError("polish question fake runtime requires a session ref")
    session_ref = str(command.input_refs[0]).strip()
    if not session_ref or any(char.isspace() for char in session_ref):
        raise RuntimePolicyError("polish question fake runtime accepts refs only")
    if contains_sensitive_payload((session_ref,)):
        raise RuntimePolicyError("polish question fake runtime rejects sensitive input refs")
    return session_ref


def _question_progress_node_ref(command: AgentCommandEnvelope) -> str | None:
    if len(command.input_refs) < 2:
        return None
    progress_node_ref = str(command.input_refs[1]).strip()
    if not progress_node_ref:
        return None
    if any(char.isspace() for char in progress_node_ref) or contains_sensitive_payload((progress_node_ref,)):
        raise RuntimePolicyError("polish question fake runtime accepts progress refs only")
    return progress_node_ref


def _question_completed_focus_refs(command: AgentCommandEnvelope) -> tuple[str, ...]:
    refs = tuple(str(ref).strip() for ref in command.input_refs[2:] if str(ref).strip())
    if any(any(char.isspace() for char in ref) for ref in refs) or contains_sensitive_payload(refs):
        raise RuntimePolicyError("polish question fake runtime accepts focus refs only")
    return refs


def _question_fake_scenario_summary(
    command: AgentCommandEnvelope, *, progress_node_ref: str | None
) -> str:
    summary = str(command.metadata.get("selected_progress_node_summary") or "").strip()
    if summary and not contains_sensitive_payload(summary):
        return summary
    if progress_node_ref:
        return "候选人项目表达场景"
    return "证据不足的打磨题场景"


def _fake_runtime_node(state: _FakeGraphState) -> _FakeGraphState:
    return {
        "owner_id": state["owner_id"],
        "run_id": state["run_id"],
        "entrypoint": state["entrypoint"],
        "steps": [*state["steps"], "langgraph_invoked"],
        "provider_calls": 0,
        "db_business_writes": 0,
        "formal_business_writes": 0,
    }


def _runtime_metadata(state: _FakeGraphState, gate: dict[str, bool]) -> dict[str, Any]:
    return {
        "runtime_enabled": gate["runtime_enabled"],
        "langgraph_enabled": gate["langgraph_enabled"],
        "provider_gate_enabled": gate["provider_gate_enabled"],
        "provider_calls": state["provider_calls"],
        "db_business_writes": state["db_business_writes"],
        "formal_business_writes": state["formal_business_writes"],
        "steps": tuple(state["steps"]),
    }


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


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:16]
