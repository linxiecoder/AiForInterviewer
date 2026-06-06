"""Owner-scoped interrupt and resume contract service."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any

from app.application.ai_runtime.contracts import (
    AgentInterruptRef,
    AgentTaskStatusRef,
    OwnerScopeError,
    RuntimeConflictError,
    RuntimeValidationError,
    sanitize_payload,
)


@dataclass(frozen=True)
class _ResumeSchemaDescriptor:
    schema_id: str
    allowed_actions: frozenset[str]
    required_fields_by_action: dict[str, tuple[str, ...]]


_RESUME_SCHEMA_DESCRIPTORS = {
    "agent.resume.user_confirmation.v1": _ResumeSchemaDescriptor(
        schema_id="agent.resume.user_confirmation.v1",
        allowed_actions=frozenset({"approve", "edit", "reject"}),
        required_fields_by_action={"edit": ("edits",)},
    ),
    "agent.resume.hitl.v1": _ResumeSchemaDescriptor(
        schema_id="agent.resume.hitl.v1",
        allowed_actions=frozenset({"continue_as_candidate", "edit_candidate", "reject", "defer_to_handoff"}),
        required_fields_by_action={"edit_candidate": ("edits",)},
    ),
}

P8_HITL_INTERRUPT_TYPES = (
    "formal_write_attempt",
    "asset_conflict",
    "low_confidence_formal_update",
    "ambiguous_ownership",
    "validation_failed_partial_result",
)


class AgentInterruptService:
    def __init__(self) -> None:
        self._interrupts: dict[str, AgentInterruptRef] = {}
        self._resume_cache: dict[tuple[str, str, str], tuple[str, AgentTaskStatusRef]] = {}

    def create_interrupt(
        self,
        *,
        owner_id: str,
        actor_id: str,
        run_id: str,
        node_name: str,
        interrupt_type: str,
        resume_schema_id: str,
        drawer_payload: dict[str, Any],
        base_version: int,
        checkpoint_ref: str = "",
    ) -> AgentInterruptRef:
        if not owner_id or not run_id or not resume_schema_id:
            raise RuntimeValidationError("owner, run, and resume schema are required")
        interrupt_id = "aint_" + _stable_id(owner_id, run_id, node_name, interrupt_type, str(base_version))
        interrupt = AgentInterruptRef(
            interrupt_id=interrupt_id,
            run_id=run_id,
            owner_id=owner_id,
            interrupt_type=interrupt_type,
            resume_schema_id=resume_schema_id,
            status="open",
            record_version=base_version,
            checkpoint_ref=checkpoint_ref,
            drawer_payload=sanitize_payload(drawer_payload),
            trace_refs=("atrace_" + _stable_id(actor_id, interrupt_id),),
            formal_refs=(),
        )
        self._interrupts[interrupt_id] = interrupt
        return interrupt

    def create_hitl_interrupt(
        self,
        *,
        owner_id: str,
        actor_id: str,
        run_id: str,
        node_name: str,
        interrupt_type: str,
        checkpoint_ref: str,
        base_version: int,
        candidate_refs: tuple[str, ...] = (),
        validation_refs: tuple[str, ...] = (),
        low_confidence_flags: tuple[str, ...] = (),
        drawer_payload: dict[str, Any] | None = None,
    ) -> AgentInterruptRef:
        if interrupt_type not in P8_HITL_INTERRUPT_TYPES:
            raise RuntimeValidationError("unsupported P8 HITL interrupt type")
        if not checkpoint_ref.strip():
            raise RuntimeValidationError("checkpoint_ref is required for P8 HITL interrupt")
        payload = {
            **(drawer_payload or {}),
            "trigger_type": interrupt_type,
            "checkpoint_ref": checkpoint_ref,
            "candidate_refs": tuple(candidate_refs),
            "validation_refs": tuple(validation_refs),
            "low_confidence_flags": tuple(low_confidence_flags),
            "formal_write_blocked": True,
        }
        return self.create_interrupt(
            owner_id=owner_id,
            actor_id=actor_id,
            run_id=run_id,
            node_name=node_name,
            interrupt_type=interrupt_type,
            resume_schema_id="agent.resume.hitl.v1",
            drawer_payload=payload,
            base_version=base_version,
            checkpoint_ref=checkpoint_ref,
        )

    def get_interrupt(self, interrupt_id: str, *, owner_id: str) -> AgentInterruptRef | None:
        interrupt = self._interrupts.get(interrupt_id)
        if not interrupt or interrupt.owner_id != owner_id:
            return None
        return interrupt

    def validate_resume_payload(
        self,
        *,
        interrupt_id: str,
        owner_id: str,
        resume_payload: dict[str, Any],
        base_version: int,
        checkpoint_ref: str | None = None,
    ) -> dict[str, Any]:
        interrupt = self._require_interrupt(interrupt_id, owner_id=owner_id)
        if interrupt.checkpoint_ref:
            if not checkpoint_ref:
                raise RuntimeValidationError("checkpoint_ref is required for interrupt resume")
            if checkpoint_ref != interrupt.checkpoint_ref:
                raise RuntimeConflictError("checkpoint ref mismatch")
        if base_version != interrupt.record_version:
            raise RuntimeConflictError("stale base version")
        if not isinstance(resume_payload, dict):
            raise RuntimeValidationError("resume payload must be an object")
        descriptor = _RESUME_SCHEMA_DESCRIPTORS.get(interrupt.resume_schema_id)
        if descriptor is None:
            raise RuntimeValidationError(f"unknown resume schema: {interrupt.resume_schema_id}")
        sanitized_payload = sanitize_payload(resume_payload)
        action = sanitized_payload.get("action")
        if not isinstance(action, str) or action not in descriptor.allowed_actions:
            raise RuntimeValidationError("unsupported resume action")
        for field_name in descriptor.required_fields_by_action.get(action, ()):
            if field_name not in sanitized_payload:
                raise RuntimeValidationError(f"resume action {action} requires {field_name}")
            if not isinstance(sanitized_payload[field_name], dict):
                raise RuntimeValidationError(f"resume action {action} field {field_name} must be an object")
        return sanitized_payload

    def resume_interrupt(
        self,
        *,
        run_id: str,
        interrupt_id: str,
        owner_id: str,
        actor_id: str,
        resume_payload: dict[str, Any],
        base_version: int,
        idempotency_key: str,
        checkpoint_ref: str | None = None,
    ) -> AgentTaskStatusRef:
        interrupt = self._require_interrupt(interrupt_id, owner_id=owner_id)
        if interrupt.run_id != run_id:
            raise OwnerScopeError("interrupt does not belong to run")
        sanitized_payload = self.validate_resume_payload(
            interrupt_id=interrupt_id,
            owner_id=owner_id,
            resume_payload=resume_payload,
            base_version=base_version,
            checkpoint_ref=checkpoint_ref,
        )
        body_hash = _payload_hash(sanitized_payload)
        cache_key = (owner_id, interrupt_id, idempotency_key)
        cached = self._resume_cache.get(cache_key)
        if cached:
            cached_hash, cached_result = cached
            if cached_hash != body_hash:
                raise RuntimeConflictError("idempotency key reused with different resume body")
            return cached_result

        result = AgentTaskStatusRef(
            ai_task_id="aitask_resume_" + _stable_id(owner_id, interrupt_id, idempotency_key),
            agent_run_id=run_id,
            status="running",
            trace_refs=("atrace_" + _stable_id(actor_id, interrupt_id, body_hash),),
            candidate_refs=(),
            interrupt_refs=(interrupt_id,),
            formal_refs=(),
        )
        self._resume_cache[cache_key] = (body_hash, result)
        self._interrupts[interrupt_id] = replace(interrupt, status="resumed")
        return result

    def reject_interrupt(self, run_id: str, interrupt_id: str, owner_id: str, reason: str) -> AgentInterruptRef:
        interrupt = self._require_interrupt(interrupt_id, owner_id=owner_id)
        if interrupt.run_id != run_id:
            raise OwnerScopeError("interrupt does not belong to run")
        updated = replace(
            interrupt,
            status="rejected",
            drawer_payload={**interrupt.drawer_payload, "reject_reason": reason},
            formal_refs=(),
        )
        self._interrupts[interrupt_id] = updated
        return updated

    def expire_interrupts(self, run_id: str, owner_id: str, *, reason: str) -> int:
        count = 0
        for interrupt_id, interrupt in list(self._interrupts.items()):
            if interrupt.owner_id == owner_id and interrupt.run_id == run_id and interrupt.status == "open":
                self._interrupts[interrupt_id] = replace(
                    interrupt,
                    status="expired",
                    drawer_payload={**interrupt.drawer_payload, "expire_reason": reason},
                    formal_refs=(),
                )
                count += 1
        return count

    def _require_interrupt(self, interrupt_id: str, *, owner_id: str) -> AgentInterruptRef:
        interrupt = self._interrupts.get(interrupt_id)
        if not interrupt or interrupt.owner_id != owner_id:
            raise OwnerScopeError("interrupt not found or inaccessible")
        return interrupt


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()[:16]


def _payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
