"""Deterministic PR4 fake LangGraph runtime."""

from __future__ import annotations

import hashlib
import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.application.ai_runtime.contracts import (
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
    sanitize_payload,
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
