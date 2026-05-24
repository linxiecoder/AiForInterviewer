"""Refs-only PR4 LangGraph checkpointer boundary."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from app.application.ai_runtime.contracts import RuntimePolicyError, contains_sensitive_payload, sanitize_payload
from app.application.ai_runtime.side_effect_guard import sanitize_checkpoint_metadata


@dataclass(frozen=True)
class RuntimeCheckpointRef:
    checkpoint_ref: str
    owner_id: str
    actor_id: str | None
    agent_run_id: str
    agent_node_run_id: str | None
    graph_name: str
    graph_version: str
    node_name: str | None
    checkpoint_namespace: str
    thread_id: str
    checkpoint_id: str
    state_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)
    formal_business_ref: str | None = None

    def public_payload(self) -> dict[str, Any]:
        return {
            "checkpoint_ref": self.checkpoint_ref,
            "agent_run_id": self.agent_run_id,
            "graph_name": self.graph_name,
            "graph_version": self.graph_version,
            "node_name": self.node_name,
            "checkpoint_namespace": self.checkpoint_namespace,
            "thread_id": self.thread_id,
            "checkpoint_id": self.checkpoint_id,
            "state_hash": self.state_hash,
            "metadata": sanitize_payload(self.metadata),
            "formal_business_ref": self.formal_business_ref,
        }


class RefsOnlyLangGraphCheckpointer:
    """Stores checkpoint references and metadata, never raw graph state."""

    def __init__(self) -> None:
        self._refs: dict[tuple[str, str, str, str], RuntimeCheckpointRef] = {}
        self._disabled_reason: str | None = None

    def record_ref(
        self,
        *,
        owner_id: str,
        actor_id: str | None,
        agent_run_id: str,
        agent_node_run_id: str | None,
        graph_name: str,
        graph_version: str,
        node_name: str | None,
        checkpoint_namespace: str,
        thread_id: str,
        checkpoint_id: str,
        state_hash: str,
        metadata: dict[str, Any] | None = None,
        raw_state: Any | None = None,
    ) -> RuntimeCheckpointRef:
        if self._disabled_reason is not None:
            raise RuntimePolicyError(f"checkpointer disabled: {self._disabled_reason}")
        if raw_state is not None:
            raise RuntimePolicyError("raw graph state cannot be written to checkpoint refs")
        if not owner_id or not agent_run_id or not checkpoint_namespace or not thread_id or not checkpoint_id:
            raise RuntimePolicyError("owner, run, namespace, thread, and checkpoint id are required")
        if contains_sensitive_payload(metadata or {}):
            raise RuntimePolicyError("checkpoint metadata cannot carry sensitive payload")

        full_metadata = {
            "checkpoint_namespace": checkpoint_namespace,
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "graph_name": graph_name,
            "graph_version": graph_version,
            "node_name": node_name,
            "state_hash": state_hash,
        } | dict(metadata or {})
        sanitized_metadata = sanitize_checkpoint_metadata(full_metadata)
        key = (owner_id, checkpoint_namespace, thread_id, checkpoint_id)
        existing = self._refs.get(key)
        if existing is not None:
            return existing

        ref = RuntimeCheckpointRef(
            checkpoint_ref="ackpt_" + _stable_id(owner_id, checkpoint_namespace, thread_id, checkpoint_id),
            owner_id=owner_id,
            actor_id=actor_id,
            agent_run_id=agent_run_id,
            agent_node_run_id=agent_node_run_id,
            graph_name=graph_name,
            graph_version=graph_version,
            node_name=node_name,
            checkpoint_namespace=checkpoint_namespace,
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
            state_hash=state_hash,
            metadata=sanitized_metadata,
            formal_business_ref=None,
        )
        self._refs[key] = ref
        return ref

    def list_refs(self, owner_id: str, agent_run_id: str) -> tuple[RuntimeCheckpointRef, ...]:
        return tuple(
            ref
            for ref in self._refs.values()
            if ref.owner_id == owner_id and ref.agent_run_id == agent_run_id
        )

    def latest(self, owner_id: str, checkpoint_namespace: str, thread_id: str) -> RuntimeCheckpointRef | None:
        matches = [
            ref
            for ref in self._refs.values()
            if ref.owner_id == owner_id
            and ref.checkpoint_namespace == checkpoint_namespace
            and ref.thread_id == thread_id
        ]
        return matches[-1] if matches else None

    def get_by_ref(self, owner_id: str, checkpoint_ref: str) -> RuntimeCheckpointRef | None:
        for ref in self._refs.values():
            if ref.owner_id == owner_id and ref.checkpoint_ref == checkpoint_ref:
                return ref
        return None

    def disable_new_writes(self, *, reason: str) -> None:
        self._disabled_reason = reason or "runtime disabled"

    def snapshot(self) -> tuple[dict[str, Any], ...]:
        return tuple(ref.public_payload() for ref in self._refs.values())


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:16]
