from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.application.agents.contracts import (
    AgentExecutionPlan,
    AgentExecutionResult,
    AgentExecutionStatus,
    AgentExecutionTimeline,
    AgentExecutionTrace,
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
    validate_agent_runtime_status,
)


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
        result = self._runner.resume(context, interrupt_ref=interrupt_ref, resume_payload=resume_payload)
        return self._result_from_run(context, result)

    def resume_from_context(
        self, context: AgentRunContext, *, interrupt_ref: str, resume_payload: dict[str, object]
    ) -> AgentExecutionResult:
        self._contexts[context.run_id] = context
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


__all__ = ["AgentExecutor", "AgentGraphRunnerExecutorAdapter"]
