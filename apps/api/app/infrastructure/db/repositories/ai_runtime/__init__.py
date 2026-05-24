"""Inert AI Runtime repositories for PR2 persistence tests."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.shared.clock import utc_now
from app.infrastructure.db.models.ai_runtime import (
    AgentCheckpointRef,
    AgentInterrupt,
    AgentNodeRun,
    AgentRun,
    LlmCall,
    LlmCallPayload,
)
from app.infrastructure.db.session import get_session_factory


REDACTED = "redacted_sensitive_detail"


class AiRuntimeRepositoryError(RuntimeError):
    pass


class IdempotencyConflict(AiRuntimeRepositoryError):
    pass


class RecordVersionConflict(AiRuntimeRepositoryError):
    pass


class RuntimePolicyError(AiRuntimeRepositoryError):
    pass


class AgentRunRepository:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def create_run(
        self,
        *,
        owner_id: str,
        actor_id: str | None,
        ai_task_id: str | None,
        graph_name: str,
        graph_version: str,
        entrypoint_name: str,
        thread_id: str,
        idempotency_key_hash: str | None,
        input_refs_json: list[dict[str, Any]] | None = None,
        trace_ref_ids: list[str] | None = None,
        evidence_ref_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        input_refs = list(input_refs_json or [])
        with self._session_factory() as session:
            existing = self._find_run_by_idempotency(session, owner_id, graph_name, idempotency_key_hash)
            if existing is not None:
                if existing.thread_id != thread_id or existing.input_refs_json != input_refs:
                    raise IdempotencyConflict("agent run idempotency key conflicts with existing run")
                return _agent_run_to_dict(existing)
            existing_thread = session.scalar(
                select(AgentRun).where(AgentRun.owner_id == owner_id, AgentRun.thread_id == thread_id)
            )
            if existing_thread is not None:
                raise IdempotencyConflict("agent run thread already exists for owner")
            run = AgentRun(
                id=_new_id("arun"),
                owner_id=owner_id,
                actor_id=actor_id,
                record_version=1,
                status="queued",
                trace_ref_ids=trace_ref_ids,
                evidence_ref_ids=evidence_ref_ids,
                created_at=now,
                updated_at=now,
                ai_task_id=ai_task_id,
                graph_name=graph_name,
                graph_version=graph_version,
                entrypoint_name=entrypoint_name,
                thread_id=thread_id,
                idempotency_key_hash=idempotency_key_hash,
                input_refs_json=input_refs,
                output_refs_json=[],
                pending_writes_json=[],
                error_summary_json=None,
                started_at=None,
                completed_at=None,
                interrupted_at=None,
            )
            session.add(run)
            session.commit()
            return _agent_run_to_dict(run)

    def get_run_for_owner(self, owner_id: str, run_id: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            run = _get_owner_scoped(session, AgentRun, owner_id, run_id)
            return _agent_run_to_dict(run) if run is not None else None

    def get_by_ai_task(self, owner_id: str, ai_task_id: str) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            runs = session.scalars(
                select(AgentRun)
                .where(AgentRun.owner_id == owner_id, AgentRun.ai_task_id == ai_task_id)
                .order_by(AgentRun.created_at, AgentRun.id)
            ).all()
            return [_agent_run_to_dict(run) for run in runs]

    def mark_running(self, owner_id: str, run_id: str, *, base_record_version: int) -> dict[str, Any]:
        return self._transition_run(owner_id, run_id, base_record_version, status="running", started_at=utc_now())

    def mark_interrupted(self, owner_id: str, run_id: str, *, base_record_version: int) -> dict[str, Any]:
        return self._transition_run(owner_id, run_id, base_record_version, status="interrupted", interrupted_at=utc_now())

    def mark_succeeded(
        self,
        owner_id: str,
        run_id: str,
        *,
        base_record_version: int,
        output_refs_json: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return self._transition_run(
            owner_id,
            run_id,
            base_record_version,
            status="succeeded",
            completed_at=utc_now(),
            output_refs_json=list(output_refs_json or []),
        )

    def mark_failed(
        self,
        owner_id: str,
        run_id: str,
        *,
        base_record_version: int,
        error_summary_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._transition_run(
            owner_id,
            run_id,
            base_record_version,
            status="failed",
            completed_at=utc_now(),
            error_summary_json=_sanitize_json(error_summary_json),
        )

    def list_timeline_runs(self, owner_id: str) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            runs = session.scalars(
                select(AgentRun)
                .where(AgentRun.owner_id == owner_id)
                .order_by(AgentRun.created_at.desc(), AgentRun.id.desc())
            ).all()
            return [_agent_run_to_dict(run) for run in runs]

    def cleanup_expired_runs(self, owner_id: str, *, before: datetime) -> int:
        with self._session_factory() as session:
            runs = session.scalars(
                select(AgentRun).where(
                    AgentRun.owner_id == owner_id,
                    AgentRun.completed_at.is_not(None),
                    AgentRun.completed_at < before,
                )
            ).all()
            count = 0
            for run in runs:
                run.pending_writes_json = []
                run.error_summary_json = None
                run.updated_at = utc_now()
                count += 1
            session.commit()
            return count

    def _transition_run(self, owner_id: str, run_id: str, base_record_version: int, **updates: Any) -> dict[str, Any]:
        with self._session_factory() as session:
            run = _require_owner_scoped(session, AgentRun, owner_id, run_id)
            _ensure_record_version(run, base_record_version)
            for key, value in updates.items():
                setattr(run, key, value)
            run.record_version += 1
            run.updated_at = utc_now()
            session.commit()
            return _agent_run_to_dict(run)

    def _find_run_by_idempotency(
        self,
        session: Session,
        owner_id: str,
        graph_name: str,
        idempotency_key_hash: str | None,
    ) -> AgentRun | None:
        if idempotency_key_hash is None:
            return None
        return session.scalar(
            select(AgentRun).where(
                AgentRun.owner_id == owner_id,
                AgentRun.graph_name == graph_name,
                AgentRun.idempotency_key_hash == idempotency_key_hash,
            )
        )


class AgentNodeRunRepository:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def start_node(
        self,
        *,
        owner_id: str,
        actor_id: str | None,
        agent_run_id: str,
        graph_name: str,
        node_name: str,
        node_version: str,
        attempt_number: int = 1,
        input_digest: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        with self._session_factory() as session:
            existing = session.scalar(
                select(AgentNodeRun).where(
                    AgentNodeRun.owner_id == owner_id,
                    AgentNodeRun.agent_run_id == agent_run_id,
                    AgentNodeRun.node_name == node_name,
                    AgentNodeRun.attempt_number == attempt_number,
                )
            )
            if existing is not None:
                return _agent_node_run_to_dict(existing)
            node_run = AgentNodeRun(
                id=_new_id("anode"),
                owner_id=owner_id,
                actor_id=actor_id,
                record_version=1,
                status="running",
                trace_ref_ids=None,
                evidence_ref_ids=None,
                created_at=now,
                updated_at=now,
                agent_run_id=agent_run_id,
                graph_name=graph_name,
                node_name=node_name,
                node_version=node_version,
                attempt_number=attempt_number,
                llm_call_ids_json=[],
                side_effect_keys_json=[],
                input_digest=input_digest,
                output_digest=None,
                validation_summary_json=None,
                started_at=now,
                completed_at=None,
            )
            session.add(node_run)
            session.commit()
            return _agent_node_run_to_dict(node_run)

    def finish_node(
        self,
        owner_id: str,
        node_run_id: str,
        *,
        base_record_version: int,
        output_digest: str | None,
        validation_summary_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._transition_node(
            owner_id,
            node_run_id,
            base_record_version,
            status="succeeded",
            output_digest=output_digest,
            validation_summary_json=_sanitize_json(validation_summary_json),
            completed_at=utc_now(),
        )

    def fail_node(
        self,
        owner_id: str,
        node_run_id: str,
        *,
        base_record_version: int,
        validation_summary_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._transition_node(
            owner_id,
            node_run_id,
            base_record_version,
            status="failed",
            validation_summary_json=_sanitize_json(validation_summary_json),
            completed_at=utc_now(),
        )

    def append_llm_call_ref(
        self,
        owner_id: str,
        node_run_id: str,
        *,
        base_record_version: int,
        llm_call_id: str,
    ) -> dict[str, Any]:
        with self._session_factory() as session:
            node_run = _require_owner_scoped(session, AgentNodeRun, owner_id, node_run_id)
            _ensure_record_version(node_run, base_record_version)
            refs = list(node_run.llm_call_ids_json or [])
            if llm_call_id not in refs:
                refs.append(llm_call_id)
            node_run.llm_call_ids_json = refs
            node_run.record_version += 1
            node_run.updated_at = utc_now()
            session.commit()
            return _agent_node_run_to_dict(node_run)

    def record_side_effect_key(
        self,
        owner_id: str,
        node_run_id: str,
        *,
        base_record_version: int,
        side_effect_key_hash: str,
        body_digest: str,
        ref_id: str,
    ) -> dict[str, Any]:
        with self._session_factory() as session:
            node_run = _require_owner_scoped(session, AgentNodeRun, owner_id, node_run_id)
            _ensure_record_version(node_run, base_record_version)
            keys = list(node_run.side_effect_keys_json or [])
            for item in keys:
                if item.get("side_effect_key_hash") == side_effect_key_hash:
                    if item.get("body_digest") != body_digest:
                        raise IdempotencyConflict("side effect key conflicts with existing node metadata")
                    return _agent_node_run_to_dict(node_run)
            keys.append(
                {
                    "side_effect_key_hash": side_effect_key_hash,
                    "body_digest": body_digest,
                    "ref_id": ref_id,
                    "status": "recorded",
                }
            )
            node_run.side_effect_keys_json = keys
            node_run.record_version += 1
            node_run.updated_at = utc_now()
            session.commit()
            return _agent_node_run_to_dict(node_run)

    def list_by_run(self, owner_id: str, agent_run_id: str) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            node_runs = session.scalars(
                select(AgentNodeRun)
                .where(AgentNodeRun.owner_id == owner_id, AgentNodeRun.agent_run_id == agent_run_id)
                .order_by(AgentNodeRun.created_at, AgentNodeRun.id)
            ).all()
            return [_agent_node_run_to_dict(node_run) for node_run in node_runs]

    def _transition_node(self, owner_id: str, node_run_id: str, base_record_version: int, **updates: Any) -> dict[str, Any]:
        with self._session_factory() as session:
            node_run = _require_owner_scoped(session, AgentNodeRun, owner_id, node_run_id)
            _ensure_record_version(node_run, base_record_version)
            for key, value in updates.items():
                setattr(node_run, key, value)
            node_run.record_version += 1
            node_run.updated_at = utc_now()
            session.commit()
            return _agent_node_run_to_dict(node_run)


class AgentInterruptRepository:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def create_interrupt(
        self,
        *,
        owner_id: str,
        actor_id: str | None,
        agent_run_id: str,
        agent_node_run_id: str | None,
        node_name: str,
        interrupt_type: str,
        resume_schema_id: str,
        prompt_summary_json: dict[str, Any],
        idempotency_key_hash: str | None,
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        with self._session_factory() as session:
            existing = self._find_interrupt_by_key(session, owner_id, agent_run_id, node_name, idempotency_key_hash)
            sanitized_prompt = _sanitize_json(prompt_summary_json)
            if existing is not None:
                if existing.prompt_summary_json != sanitized_prompt:
                    raise IdempotencyConflict("interrupt idempotency key conflicts with existing prompt")
                return _agent_interrupt_to_dict(existing)
            interrupt = AgentInterrupt(
                id=_new_id("aint"),
                owner_id=owner_id,
                actor_id=actor_id,
                record_version=1,
                status="open",
                trace_ref_ids=None,
                evidence_ref_ids=None,
                created_at=now,
                updated_at=now,
                agent_run_id=agent_run_id,
                agent_node_run_id=agent_node_run_id,
                node_name=node_name,
                interrupt_type=interrupt_type,
                resume_schema_id=resume_schema_id,
                prompt_summary_json=sanitized_prompt,
                resume_payload_summary_json=None,
                expires_at=expires_at,
                resumed_at=None,
                idempotency_key_hash=idempotency_key_hash,
            )
            session.add(interrupt)
            session.commit()
            return _agent_interrupt_to_dict(interrupt)

    def get_open_interrupt_for_owner(self, owner_id: str, interrupt_id: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            interrupt = session.scalar(
                select(AgentInterrupt).where(
                    AgentInterrupt.owner_id == owner_id,
                    AgentInterrupt.id == interrupt_id,
                    AgentInterrupt.status == "open",
                )
            )
            return _agent_interrupt_to_dict(interrupt) if interrupt is not None else None

    def resume_interrupt_once(
        self,
        *,
        owner_id: str,
        interrupt_id: str,
        base_record_version: int,
        idempotency_key_hash: str,
        resume_payload_summary_json: dict[str, Any],
    ) -> dict[str, Any]:
        sanitized_payload = _sanitize_json(resume_payload_summary_json)
        with self._session_factory() as session:
            interrupt = _require_owner_scoped(session, AgentInterrupt, owner_id, interrupt_id)
            if interrupt.status == "resumed":
                if (
                    interrupt.idempotency_key_hash == idempotency_key_hash
                    and interrupt.resume_payload_summary_json == sanitized_payload
                ):
                    return _agent_interrupt_to_dict(interrupt)
                raise IdempotencyConflict("interrupt already resumed with a different key or payload")
            _ensure_record_version(interrupt, base_record_version)
            interrupt.status = "resumed"
            interrupt.idempotency_key_hash = idempotency_key_hash
            interrupt.resume_payload_summary_json = sanitized_payload
            interrupt.resumed_at = utc_now()
            interrupt.record_version += 1
            interrupt.updated_at = utc_now()
            session.commit()
            return _agent_interrupt_to_dict(interrupt)

    def expire_interrupts(self, owner_id: str, *, now: datetime | None = None) -> int:
        resolved_now = now or utc_now()
        with self._session_factory() as session:
            interrupts = session.scalars(
                select(AgentInterrupt).where(
                    AgentInterrupt.owner_id == owner_id,
                    AgentInterrupt.status == "open",
                    AgentInterrupt.expires_at.is_not(None),
                    AgentInterrupt.expires_at < resolved_now,
                )
            ).all()
            for interrupt in interrupts:
                interrupt.status = "expired"
                interrupt.updated_at = resolved_now
                interrupt.record_version += 1
            session.commit()
            return len(interrupts)

    def _find_interrupt_by_key(
        self,
        session: Session,
        owner_id: str,
        agent_run_id: str,
        node_name: str,
        idempotency_key_hash: str | None,
    ) -> AgentInterrupt | None:
        if idempotency_key_hash is None:
            return None
        return session.scalar(
            select(AgentInterrupt).where(
                AgentInterrupt.owner_id == owner_id,
                AgentInterrupt.agent_run_id == agent_run_id,
                AgentInterrupt.node_name == node_name,
                AgentInterrupt.idempotency_key_hash == idempotency_key_hash,
            )
        )


class AgentCheckpointRefRepository:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def record_checkpoint_ref(
        self,
        *,
        owner_id: str,
        actor_id: str | None,
        agent_run_id: str,
        agent_node_run_id: str | None,
        graph_name: str,
        node_name: str | None,
        checkpoint_namespace: str,
        thread_id: str,
        checkpoint_id: str,
        checkpoint_metadata_json: dict[str, Any],
        retention_expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        sanitized_metadata = _sanitize_json(checkpoint_metadata_json)
        with self._session_factory() as session:
            existing = session.scalar(
                select(AgentCheckpointRef).where(
                    AgentCheckpointRef.owner_id == owner_id,
                    AgentCheckpointRef.checkpoint_namespace == checkpoint_namespace,
                    AgentCheckpointRef.thread_id == thread_id,
                    AgentCheckpointRef.checkpoint_id == checkpoint_id,
                )
            )
            if existing is not None:
                return _agent_checkpoint_ref_to_dict(existing)
            checkpoint_ref = AgentCheckpointRef(
                id=_new_id("ackpt"),
                owner_id=owner_id,
                actor_id=actor_id,
                record_version=1,
                status="created",
                trace_ref_ids=None,
                evidence_ref_ids=None,
                created_at=now,
                updated_at=now,
                agent_run_id=agent_run_id,
                agent_node_run_id=agent_node_run_id,
                graph_name=graph_name,
                node_name=node_name,
                checkpoint_namespace=checkpoint_namespace,
                thread_id=thread_id,
                checkpoint_id=checkpoint_id,
                checkpoint_metadata_json=sanitized_metadata,
                retention_expires_at=retention_expires_at,
            )
            session.add(checkpoint_ref)
            session.commit()
            return _agent_checkpoint_ref_to_dict(checkpoint_ref)

    def list_refs_by_run(self, owner_id: str, agent_run_id: str) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            refs = session.scalars(
                select(AgentCheckpointRef)
                .where(AgentCheckpointRef.owner_id == owner_id, AgentCheckpointRef.agent_run_id == agent_run_id)
                .order_by(AgentCheckpointRef.created_at, AgentCheckpointRef.id)
            ).all()
            return [_agent_checkpoint_ref_to_dict(ref) for ref in refs]

    def get_latest_ref(self, owner_id: str, checkpoint_namespace: str, thread_id: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            ref = session.scalar(
                select(AgentCheckpointRef)
                .where(
                    AgentCheckpointRef.owner_id == owner_id,
                    AgentCheckpointRef.checkpoint_namespace == checkpoint_namespace,
                    AgentCheckpointRef.thread_id == thread_id,
                )
                .order_by(AgentCheckpointRef.created_at.desc(), AgentCheckpointRef.id.desc())
            )
            return _agent_checkpoint_ref_to_dict(ref) if ref is not None else None

    def expire_refs(self, owner_id: str, *, before: datetime) -> int:
        with self._session_factory() as session:
            refs = session.scalars(
                select(AgentCheckpointRef).where(
                    AgentCheckpointRef.owner_id == owner_id,
                    AgentCheckpointRef.retention_expires_at.is_not(None),
                    AgentCheckpointRef.retention_expires_at < before,
                )
            ).all()
            for ref in refs:
                ref.status = "expired"
                ref.updated_at = utc_now()
                ref.record_version += 1
            session.commit()
            return len(refs)


class LlmCallRepository:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def create_planned_call(
        self,
        *,
        owner_id: str,
        actor_id: str | None,
        ai_task_id: str | None,
        agent_run_id: str | None,
        agent_node_run_id: str | None,
        graph_name: str | None,
        node_name: str | None,
        contract_ids_json: list[str],
        configured_model: str | None,
        provider_model: str | None,
        prompt_version: str | None,
        schema_id: str | None,
        request_hash: str | None,
        validation_errors_json: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        now = utc_now()
        call = LlmCall(
            id=_new_id("llmc"),
            owner_id=owner_id,
            actor_id=actor_id,
            record_version=1,
            status="planned",
            trace_ref_ids=None,
            evidence_ref_ids=None,
            created_at=now,
            updated_at=now,
            ai_task_id=ai_task_id,
            agent_run_id=agent_run_id,
            agent_node_run_id=agent_node_run_id,
            graph_name=graph_name,
            node_name=node_name,
            contract_ids_json=list(contract_ids_json),
            configured_model=configured_model,
            provider_model=provider_model,
            prompt_version=prompt_version,
            schema_id=schema_id,
            request_hash=request_hash,
            response_hash=None,
            evidence_hash=None,
            usage_json=None,
            fallback_reason=None,
            validation_errors_json=_sanitize_json(validation_errors_json),
            low_confidence_flags_json=None,
            error_summary_json=None,
            started_at=None,
            completed_at=None,
        )
        with self._session_factory() as session:
            session.add(call)
            session.commit()
            return _llm_call_to_summary(call)

    def mark_running(self, owner_id: str, llm_call_id: str, *, base_record_version: int) -> dict[str, Any]:
        return self._transition_call(owner_id, llm_call_id, base_record_version, status="running", started_at=utc_now())

    def mark_succeeded(
        self,
        owner_id: str,
        llm_call_id: str,
        *,
        base_record_version: int,
        response_hash: str | None,
        evidence_hash: str | None,
        usage_json: dict[str, Any] | None,
        low_confidence_flags_json: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._transition_call(
            owner_id,
            llm_call_id,
            base_record_version,
            status="succeeded",
            response_hash=response_hash,
            evidence_hash=evidence_hash,
            usage_json=_sanitize_json(usage_json),
            low_confidence_flags_json=_sanitize_json(low_confidence_flags_json),
            completed_at=utc_now(),
        )

    def mark_failed(
        self,
        owner_id: str,
        llm_call_id: str,
        *,
        base_record_version: int,
        error_summary_json: dict[str, Any],
        fallback_reason: str | None = None,
    ) -> dict[str, Any]:
        return self._transition_call(
            owner_id,
            llm_call_id,
            base_record_version,
            status="failed",
            error_summary_json=_sanitize_json(error_summary_json),
            fallback_reason=_sanitize_text(fallback_reason),
            completed_at=utc_now(),
        )

    def mark_replay_reused(
        self,
        owner_id: str,
        llm_call_id: str,
        *,
        base_record_version: int,
        replay_reason: str,
    ) -> dict[str, Any]:
        return self._transition_call(
            owner_id,
            llm_call_id,
            base_record_version,
            status="replay_reused",
            fallback_reason=_sanitize_text(replay_reason),
            completed_at=utc_now(),
        )

    def get_summary_for_owner(self, owner_id: str, llm_call_id: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            call = _get_owner_scoped(session, LlmCall, owner_id, llm_call_id)
            return _llm_call_to_summary(call) if call is not None else None

    def list_by_run(self, owner_id: str, agent_run_id: str) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            calls = session.scalars(
                select(LlmCall)
                .where(LlmCall.owner_id == owner_id, LlmCall.agent_run_id == agent_run_id)
                .order_by(LlmCall.created_at, LlmCall.id)
            ).all()
            return [_llm_call_to_summary(call) for call in calls]

    def _transition_call(self, owner_id: str, llm_call_id: str, base_record_version: int, **updates: Any) -> dict[str, Any]:
        with self._session_factory() as session:
            call = _require_owner_scoped(session, LlmCall, owner_id, llm_call_id)
            _ensure_record_version(call, base_record_version)
            for key, value in updates.items():
                setattr(call, key, value)
            call.record_version += 1
            call.updated_at = utc_now()
            session.commit()
            return _llm_call_to_summary(call)


class LlmCallPayloadRepository:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def capture_sanitized_summary(
        self,
        *,
        owner_id: str,
        actor_id: str | None,
        llm_call_id: str,
        payload_kind: str,
        payload_summary_json: dict[str, Any],
        payload_hash: str | None,
        capture_policy_version: str = "pr2-raw-off",
        retention_expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        sanitized_summary = _sanitize_json(payload_summary_json)
        now = utc_now()
        with self._session_factory() as session:
            existing = session.scalar(
                select(LlmCallPayload).where(
                    LlmCallPayload.owner_id == owner_id,
                    LlmCallPayload.llm_call_id == llm_call_id,
                    LlmCallPayload.payload_kind == payload_kind,
                )
            )
            if existing is not None:
                if existing.payload_hash != payload_hash:
                    raise IdempotencyConflict("LLM payload capture conflicts with existing payload hash")
                return _llm_payload_to_summary(existing)
            payload = LlmCallPayload(
                id=_new_id("llmp"),
                owner_id=owner_id,
                actor_id=actor_id,
                record_version=1,
                status="captured",
                trace_ref_ids=None,
                evidence_ref_ids=None,
                created_at=now,
                updated_at=now,
                llm_call_id=llm_call_id,
                payload_kind=payload_kind,
                capture_policy_version=capture_policy_version,
                sanitized=True,
                raw_enabled=False,
                payload_summary_json=sanitized_summary,
                payload_hash=payload_hash,
                raw_payload_ciphertext_ref=None,
                encryption_key_ref=None,
                retention_expires_at=retention_expires_at,
                access_audit_ref_id=None,
            )
            session.add(payload)
            session.commit()
            return _llm_payload_to_summary(payload)

    def capture_debug_raw_ref(
        self,
        *,
        owner_id: str,
        actor_id: str | None,
        llm_call_id: str,
        payload_kind: str,
        raw_payload_ciphertext_ref: str,
        encryption_key_ref: str,
    ) -> dict[str, Any]:
        raise RuntimePolicyError("PR2 raw debug capture is fail-closed and deferred to PR4+")

    def expire_payloads(self, owner_id: str, *, before: datetime) -> int:
        with self._session_factory() as session:
            payloads = session.scalars(
                select(LlmCallPayload).where(
                    LlmCallPayload.owner_id == owner_id,
                    LlmCallPayload.retention_expires_at.is_not(None),
                    LlmCallPayload.retention_expires_at < before,
                )
            ).all()
            for payload in payloads:
                payload.status = "expired"
                payload.payload_summary_json = {}
                payload.raw_payload_ciphertext_ref = None
                payload.encryption_key_ref = None
                payload.record_version += 1
                payload.updated_at = utc_now()
            session.commit()
            return len(payloads)

    def audit_payload_access(self, owner_id: str, llm_call_payload_id: str, *, access_audit_ref_id: str) -> dict[str, Any]:
        with self._session_factory() as session:
            payload = _require_owner_scoped(session, LlmCallPayload, owner_id, llm_call_payload_id)
            payload.access_audit_ref_id = access_audit_ref_id
            payload.record_version += 1
            payload.updated_at = utc_now()
            session.commit()
            return _llm_payload_to_summary(payload)


class AgentSideEffectRepository:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def record_pending_write(
        self,
        *,
        owner_id: str,
        agent_run_id: str,
        side_effect_key_hash: str,
        body_digest: str,
        target_kind: str,
        target_ref_id: str,
    ) -> dict[str, Any]:
        with self._session_factory() as session:
            run = _require_owner_scoped(session, AgentRun, owner_id, agent_run_id)
            pending_writes = list(run.pending_writes_json or [])
            for item in pending_writes:
                if item.get("side_effect_key_hash") == side_effect_key_hash:
                    if item.get("body_digest") != body_digest:
                        raise IdempotencyConflict("side effect key conflicts with existing pending metadata")
                    return dict(item)
            pending = {
                "pending_write_ref_id": _new_id("apw"),
                "side_effect_key_hash": side_effect_key_hash,
                "body_digest": body_digest,
                "target_kind": target_kind,
                "target_ref_id": target_ref_id,
                "status": "pending",
                "formal_write": False,
            }
            pending_writes.append(pending)
            run.pending_writes_json = pending_writes
            run.record_version += 1
            run.updated_at = utc_now()
            session.commit()
            return dict(pending)

    def finalize_pending_write(
        self,
        *,
        owner_id: str,
        agent_run_id: str,
        side_effect_key_hash: str,
        finalized_ref_id: str,
    ) -> dict[str, Any]:
        return self._update_pending_write(
            owner_id=owner_id,
            agent_run_id=agent_run_id,
            side_effect_key_hash=side_effect_key_hash,
            status="finalized",
            finalized_ref_id=finalized_ref_id,
        )

    def mark_pending_write_failed(
        self,
        *,
        owner_id: str,
        agent_run_id: str,
        side_effect_key_hash: str,
        failure_summary: dict[str, Any],
    ) -> dict[str, Any]:
        return self._update_pending_write(
            owner_id=owner_id,
            agent_run_id=agent_run_id,
            side_effect_key_hash=side_effect_key_hash,
            status="failed",
            failure_summary=_sanitize_json(failure_summary),
        )

    def _update_pending_write(
        self,
        *,
        owner_id: str,
        agent_run_id: str,
        side_effect_key_hash: str,
        status: str,
        **updates: Any,
    ) -> dict[str, Any]:
        with self._session_factory() as session:
            run = _require_owner_scoped(session, AgentRun, owner_id, agent_run_id)
            pending_writes = list(run.pending_writes_json or [])
            for index, item in enumerate(pending_writes):
                if item.get("side_effect_key_hash") == side_effect_key_hash:
                    updated = dict(item)
                    updated["status"] = status
                    updated.update(updates)
                    pending_writes[index] = updated
                    run.pending_writes_json = pending_writes
                    run.record_version += 1
                    run.updated_at = utc_now()
                    session.commit()
                    return updated
        raise RuntimePolicyError("pending write metadata not found")


def _get_owner_scoped(session: Session, model_type: Any, owner_id: str, record_id: str) -> Any | None:
    return session.scalar(select(model_type).where(model_type.owner_id == owner_id, model_type.id == record_id))


def _require_owner_scoped(session: Session, model_type: Any, owner_id: str, record_id: str) -> Any:
    record = _get_owner_scoped(session, model_type, owner_id, record_id)
    if record is None:
        raise RuntimePolicyError("runtime record not found for owner")
    return record


def _ensure_record_version(record: Any, base_record_version: int) -> None:
    if record.record_version != base_record_version:
        raise RecordVersionConflict("runtime record version conflict")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _agent_run_to_dict(run: AgentRun) -> dict[str, Any]:
    return _common_dict(run) | {
        "ai_task_id": run.ai_task_id,
        "graph_name": run.graph_name,
        "graph_version": run.graph_version,
        "entrypoint_name": run.entrypoint_name,
        "thread_id": run.thread_id,
        "idempotency_key_hash": run.idempotency_key_hash,
        "input_refs_json": list(run.input_refs_json or []),
        "output_refs_json": list(run.output_refs_json or []),
        "pending_writes_json": list(run.pending_writes_json or []),
        "error_summary_json": run.error_summary_json,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "interrupted_at": run.interrupted_at,
    }


def _agent_node_run_to_dict(node_run: AgentNodeRun) -> dict[str, Any]:
    return _common_dict(node_run) | {
        "agent_run_id": node_run.agent_run_id,
        "graph_name": node_run.graph_name,
        "node_name": node_run.node_name,
        "node_version": node_run.node_version,
        "attempt_number": node_run.attempt_number,
        "llm_call_ids_json": list(node_run.llm_call_ids_json or []),
        "side_effect_keys_json": list(node_run.side_effect_keys_json or []),
        "input_digest": node_run.input_digest,
        "output_digest": node_run.output_digest,
        "validation_summary_json": node_run.validation_summary_json,
        "started_at": node_run.started_at,
        "completed_at": node_run.completed_at,
    }


def _agent_interrupt_to_dict(interrupt: AgentInterrupt) -> dict[str, Any]:
    return _common_dict(interrupt) | {
        "agent_run_id": interrupt.agent_run_id,
        "agent_node_run_id": interrupt.agent_node_run_id,
        "node_name": interrupt.node_name,
        "interrupt_type": interrupt.interrupt_type,
        "resume_schema_id": interrupt.resume_schema_id,
        "prompt_summary_json": interrupt.prompt_summary_json,
        "resume_payload_summary_json": interrupt.resume_payload_summary_json,
        "expires_at": interrupt.expires_at,
        "resumed_at": interrupt.resumed_at,
        "idempotency_key_hash": interrupt.idempotency_key_hash,
    }


def _agent_checkpoint_ref_to_dict(ref: AgentCheckpointRef) -> dict[str, Any]:
    return _common_dict(ref) | {
        "agent_run_id": ref.agent_run_id,
        "agent_node_run_id": ref.agent_node_run_id,
        "graph_name": ref.graph_name,
        "node_name": ref.node_name,
        "checkpoint_namespace": ref.checkpoint_namespace,
        "thread_id": ref.thread_id,
        "checkpoint_id": ref.checkpoint_id,
        "checkpoint_metadata_json": ref.checkpoint_metadata_json,
        "retention_expires_at": ref.retention_expires_at,
    }


def _llm_call_to_summary(call: LlmCall) -> dict[str, Any]:
    return _common_dict(call) | {
        "ai_task_id": call.ai_task_id,
        "agent_run_id": call.agent_run_id,
        "agent_node_run_id": call.agent_node_run_id,
        "graph_name": call.graph_name,
        "node_name": call.node_name,
        "contract_ids_json": list(call.contract_ids_json or []),
        "configured_model": call.configured_model,
        "provider_model": call.provider_model,
        "prompt_version": call.prompt_version,
        "schema_id": call.schema_id,
        "request_hash": call.request_hash,
        "response_hash": call.response_hash,
        "evidence_hash": call.evidence_hash,
        "usage_json": call.usage_json,
        "fallback_reason": call.fallback_reason,
        "validation_errors_json": call.validation_errors_json,
        "low_confidence_flags_json": call.low_confidence_flags_json,
        "error_summary_json": call.error_summary_json,
        "started_at": call.started_at,
        "completed_at": call.completed_at,
    }


def _llm_payload_to_summary(payload: LlmCallPayload) -> dict[str, Any]:
    return _common_dict(payload) | {
        "llm_call_id": payload.llm_call_id,
        "payload_kind": payload.payload_kind,
        "capture_policy_version": payload.capture_policy_version,
        "sanitized": payload.sanitized,
        "raw_enabled": payload.raw_enabled,
        "payload_summary_json": payload.payload_summary_json,
        "payload_hash": payload.payload_hash,
        "raw_payload_ciphertext_ref": payload.raw_payload_ciphertext_ref,
        "encryption_key_ref": payload.encryption_key_ref,
        "retention_expires_at": payload.retention_expires_at,
        "access_audit_ref_id": payload.access_audit_ref_id,
    }


def _common_dict(record: Any) -> dict[str, Any]:
    return {
        "id": record.id,
        "owner_id": record.owner_id,
        "actor_id": record.actor_id,
        "record_version": record.record_version,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "trace_ref_ids": record.trace_ref_ids,
        "evidence_ref_ids": record.evidence_ref_ids,
    }


def _sanitize_json(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        redacted = False
        for key, item in value.items():
            if _is_sensitive_key(str(key)):
                redacted = True
                continue
            sanitized[str(key)] = _sanitize_json(item)
        if redacted:
            sanitized[REDACTED] = True
        return sanitized
    if isinstance(value, list):
        return [_sanitize_json(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_json(item) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value)
    return value


def _sanitize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.lower().replace("-", "_").replace(" ", "_")
    if any(marker in normalized for marker in _SENSITIVE_VALUE_MARKERS):
        return REDACTED
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(fragment in normalized for fragment in _SENSITIVE_KEY_FRAGMENTS)


_SENSITIVE_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "system_prompt",
    "hidden_rubric",
    "api_key",
    "cookie",
    "secret",
    "full_resume",
    "full_jd",
    "request_body",
    "response_body",
    "checkpoint_payload",
    "payload",
    "prompt",
    "completion",
)

_SENSITIVE_VALUE_MARKERS = (
    "raw_prompt",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "system_prompt",
    "hidden_rubric",
    "api_key",
    "token=",
    "cookie=",
    "secret=",
    "full_resume",
    "full_jd",
    "request_body",
    "response_body",
)


__all__ = [
    "AgentCheckpointRefRepository",
    "AgentInterruptRepository",
    "AgentNodeRunRepository",
    "AgentRunRepository",
    "AgentSideEffectRepository",
    "AiRuntimeRepositoryError",
    "IdempotencyConflict",
    "LlmCallPayloadRepository",
    "LlmCallRepository",
    "RecordVersionConflict",
    "RuntimePolicyError",
]
