from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.application.agents.contracts import (
    AgentExecutionPlan,
    AgentExecutionResult,
    AgentHandoffEnvelope,
    AgentRuntimeLoopPolicy,
    CROSS_AGENT_ALLOWED_SIDE_EFFECT_POLICIES,
    CrossAgentHandoffRoute,
    HandoffContract,
)

if TYPE_CHECKING:
    from app.application.agents.runtime import AgentExecutor


_BLOCKED_METADATA_KEY_PARTS = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "full_source_body",
    "full_resume",
    "full_jd",
    "full_answer",
    "full_asset_body",
    "formal_refs",
    "formal_outputs",
    "formal_write_count",
    "formal_write_result",
    "formal_write_payload",
    "api_key",
    "token",
    "cookie",
    "secret",
)

_FORMAL_METADATA_KEY_EXCEPTIONS = {
    "formal_write_blocked",
    "formal_write_blocked_until",
}

_CROSS_AGENT_REFS_ONLY_KEYS = {
    "candidate_ref",
    "candidate_refs",
    "handoff_ref",
    "handoff_refs",
    "input_ref",
    "input_refs",
    "interrupt_ref",
    "interrupt_refs",
    "low_confidence_flags",
    "owner_id",
    "owner_ref",
    "plan_id",
    "plan_ref",
    "plan_refs",
    "policy_ref",
    "policy_refs",
    "provider_ref",
    "provider_refs",
    "skill_ref",
    "skill_refs",
    "source_agent_id",
    "source_run_id",
    "target_agent_id",
    "tool_ref",
    "tool_refs",
    "trace_ref",
    "trace_refs",
    "validation_ref",
    "validation_refs",
}


def build_agent_handoff_plan(
    *,
    source_result: AgentExecutionResult,
    handoff_contract: HandoffContract,
    target_plan_id: str,
    target_agent_id: str,
    owner_id: str,
    objective: str,
    runtime_loop_policy: AgentRuntimeLoopPolicy,
    actor_id: str = "",
    run_id: str = "",
    ai_task_id: str = "",
    graph_name: str = "",
    graph_version: str = "",
    candidate_ref: str = "",
    idempotency_key: str = "",
    metadata: dict[str, Any] | None = None,
) -> AgentExecutionPlan:
    """Create a target AgentExecutionPlan from a typed source candidate handoff."""

    descriptor = _select_candidate_descriptor(source_result, candidate_ref=candidate_ref)
    selected_candidate_ref = str(descriptor["candidate_ref"])
    candidate_type = str(descriptor["candidate_type"])
    payload_schema_id = str(descriptor["payload_schema_id"])
    route = handoff_contract.cross_agent_route
    _reject_unsafe_handoff_metadata(descriptor, label="handoff descriptor")
    _reject_unsafe_handoff_metadata(metadata or {}, label="handoff metadata")
    descriptor_trace_refs = _unique_refs(*_as_refs(descriptor.get("trace_refs")))
    validation_refs = _unique_refs(
        *handoff_contract.validation_refs,
        *_as_refs(descriptor.get("validation_refs")),
    )
    asset_handoff_fields = _asset_handoff_fields(descriptor)
    _validate_contract_match(
        handoff_contract=handoff_contract,
        candidate_ref=selected_candidate_ref,
        candidate_type=candidate_type,
        payload_schema_id=payload_schema_id,
        source_result=source_result,
        target_agent_id=target_agent_id,
        descriptor_trace_refs=descriptor_trace_refs,
        validation_refs=validation_refs,
    )
    envelope_trace_refs = (
        descriptor_trace_refs
        if route is not None
        else _unique_refs(*descriptor_trace_refs, source_result.trace.trace_id)
    )
    envelope = AgentHandoffEnvelope(
        candidate_ref=selected_candidate_ref,
        candidate_type=candidate_type,
        payload_schema_id=payload_schema_id,
        trace_refs=envelope_trace_refs,
        validation_refs=validation_refs,
        side_effect_key=handoff_contract.side_effect_key,
        idempotency_key=handoff_contract.idempotency_key or idempotency_key,
        **asset_handoff_fields,
        metadata={
            "source_run_id": source_result.run_id,
            "source_agent_id": source_result.trace.agent_id,
            "target_agent_id": target_agent_id,
        },
    )
    handoff_metadata = {
        "handoff_ref": envelope.handoff_ref,
        "candidate_ref": envelope.candidate_ref,
        "candidate_type": envelope.candidate_type,
        "payload_schema_id": envelope.payload_schema_id,
        "trace_refs": envelope.trace_refs,
        "validation_refs": envelope.validation_refs,
        "side_effect_key": envelope.side_effect_key,
        "idempotency_key": envelope.idempotency_key,
        **_asset_handoff_metadata(envelope),
    }
    caller_metadata = (
        _cross_agent_refs_only_metadata(metadata or {})
        if route is not None
        else dict(metadata or {})
    )
    return AgentExecutionPlan(
        plan_id=target_plan_id,
        agent_id=target_agent_id,
        owner_id=owner_id,
        objective=objective,
        run_id=run_id,
        ai_task_id=ai_task_id,
        actor_id=actor_id,
        graph_name=graph_name or target_agent_id,
        graph_version=graph_version,
        input_refs=(envelope.handoff_ref,),
        requested_outputs=("candidate_refs",),
        idempotency_key=idempotency_key or envelope.idempotency_key,
        runtime_loop_policy=runtime_loop_policy,
        handoff_contract=handoff_contract,
        metadata=_safe_handoff_metadata(
            {
                **caller_metadata,
                "source_run_id": source_result.run_id,
                "source_agent_id": source_result.trace.agent_id,
                "handoff_refs": (envelope.handoff_ref,),
                "handoff_envelope": handoff_metadata,
            }
        ),
    )


def execute_agent_handoff(
    *,
    source_result: AgentExecutionResult,
    handoff_contract: HandoffContract,
    target_executor: AgentExecutor,
    target_plan_id: str,
    target_agent_id: str,
    owner_id: str,
    objective: str,
    runtime_loop_policy: AgentRuntimeLoopPolicy,
    actor_id: str = "",
    run_id: str = "",
    ai_task_id: str = "",
    graph_name: str = "",
    graph_version: str = "",
    candidate_ref: str = "",
    idempotency_key: str = "",
    metadata: dict[str, Any] | None = None,
) -> AgentExecutionResult:
    """Start a target AgentExecutor from a typed candidate handoff plan."""

    target_plan = build_agent_handoff_plan(
        source_result=source_result,
        handoff_contract=handoff_contract,
        target_plan_id=target_plan_id,
        target_agent_id=target_agent_id,
        owner_id=owner_id,
        objective=objective,
        runtime_loop_policy=runtime_loop_policy,
        actor_id=actor_id,
        run_id=run_id,
        ai_task_id=ai_task_id,
        graph_name=graph_name,
        graph_version=graph_version,
        candidate_ref=candidate_ref,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )
    return target_executor.start(target_plan)


def _select_candidate_descriptor(source_result: AgentExecutionResult, *, candidate_ref: str) -> dict[str, object]:
    descriptors = tuple(
        descriptor
        for descriptor in source_result.metadata.get("handoff_candidate_descriptors", ())
        if isinstance(descriptor, dict)
    )
    if candidate_ref:
        for descriptor in descriptors:
            if str(descriptor.get("candidate_ref") or "") == candidate_ref:
                return descriptor
        raise ValueError("candidate descriptor is required for handoff")
    if len(descriptors) != 1:
        raise ValueError("exactly one candidate descriptor is required for handoff")
    return descriptors[0]


def _validate_contract_match(
    *,
    handoff_contract: HandoffContract,
    candidate_ref: str,
    candidate_type: str,
    payload_schema_id: str,
    source_result: AgentExecutionResult,
    target_agent_id: str,
    descriptor_trace_refs: tuple[str, ...],
    validation_refs: tuple[str, ...],
) -> None:
    if candidate_ref not in source_result.candidate_refs:
        raise ValueError("candidate_ref must come from source AgentExecutionResult")
    if handoff_contract.candidate_ref_types and candidate_type not in handoff_contract.candidate_ref_types:
        raise ValueError("candidate type is not allowed by handoff contract")
    if handoff_contract.payload_schema_id and payload_schema_id != handoff_contract.payload_schema_id:
        raise ValueError("payload schema is not allowed by handoff contract")
    if not handoff_contract.side_effect_key:
        raise ValueError("handoff side_effect_key is required")
    if not (handoff_contract.idempotency_key):
        raise ValueError("handoff idempotency_key is required")
    route = handoff_contract.cross_agent_route
    if route is None:
        return
    _validate_cross_agent_route_match(
        route=route,
        source_result=source_result,
        target_agent_id=target_agent_id,
        candidate_type=candidate_type,
        payload_schema_id=payload_schema_id,
        trace_refs=descriptor_trace_refs,
        validation_refs=validation_refs,
    )


def _validate_cross_agent_route_match(
    *,
    route: CrossAgentHandoffRoute,
    source_result: AgentExecutionResult,
    target_agent_id: str,
    candidate_type: str,
    payload_schema_id: str,
    trace_refs: tuple[str, ...],
    validation_refs: tuple[str, ...],
) -> None:
    source_agent_id = str(source_result.trace.agent_id).strip()
    if route.source_agent_id != source_agent_id:
        raise ValueError("source_agent_id does not match cross-agent handoff route")
    if route.target_agent_id != str(target_agent_id).strip():
        raise ValueError("target_agent_id does not match cross-agent handoff route")
    if candidate_type not in route.allowed_candidate_types:
        raise ValueError("candidate type is not allowed by cross-agent handoff route")
    if payload_schema_id != route.payload_schema_id:
        raise ValueError("payload schema does not match cross-agent handoff route")
    if route.side_effect_policy not in CROSS_AGENT_ALLOWED_SIDE_EFFECT_POLICIES:
        raise ValueError("cross-agent handoff route side_effect_policy is not allowed")
    if not trace_refs:
        raise ValueError("trace refs are required for cross-agent handoff")
    missing_trace_refs = tuple(ref for ref in route.required_trace_refs if ref not in trace_refs)
    if missing_trace_refs:
        raise ValueError("required trace refs are missing for cross-agent handoff")
    if not validation_refs:
        raise ValueError("validation refs are required for cross-agent handoff")
    missing_validation_refs = tuple(ref for ref in route.required_validation_refs if ref not in validation_refs)
    if missing_validation_refs:
        raise ValueError("required validation refs are missing for cross-agent handoff")


def _asset_handoff_fields(descriptor: dict[str, object]) -> dict[str, object]:
    candidate_type = str(descriptor.get("candidate_type") or "").strip()
    if candidate_type != "asset_update_candidate":
        return {}

    candidate_ref = str(descriptor.get("candidate_ref") or "").strip()
    asset_update_candidate_ref = _optional_ref(
        descriptor.get("asset_update_candidate_ref"),
        field_name="asset_update_candidate_ref",
        allowed_prefixes=("asset_update_candidate_ref_",),
    )
    if not asset_update_candidate_ref:
        asset_update_candidate_ref = candidate_ref
    if asset_update_candidate_ref != candidate_ref:
        raise ValueError("asset_update_candidate_ref must match candidate_ref")

    fields: dict[str, object] = {
        "asset_update_candidate_ref": asset_update_candidate_ref,
    }
    asset_body_ref = _optional_ref(
        descriptor.get("asset_body_ref"),
        field_name="asset_body_ref",
        allowed_prefixes=("asset_body_ref_", "project_asset_body_ref_"),
    )
    if asset_body_ref:
        fields["asset_body_ref"] = asset_body_ref

    asset_schema_id = str(descriptor.get("asset_schema_id") or "").strip()
    if asset_schema_id:
        fields["asset_schema_id"] = asset_schema_id

    formal_write_blocked_until = str(descriptor.get("formal_write_blocked_until") or "").strip()
    if formal_write_blocked_until:
        fields["formal_write_blocked_until"] = formal_write_blocked_until

    user_confirmation_required = descriptor.get("user_confirmation_required")
    if isinstance(user_confirmation_required, bool):
        fields["user_confirmation_required"] = user_confirmation_required
    return fields


def _asset_handoff_metadata(envelope: AgentHandoffEnvelope) -> dict[str, object]:
    metadata: dict[str, object] = {}
    for key in ("asset_update_candidate_ref", "asset_body_ref", "asset_schema_id", "formal_write_blocked_until"):
        value = getattr(envelope, key)
        if isinstance(value, str) and value.strip():
            metadata[key] = value
    if envelope.user_confirmation_required is not None:
        metadata["user_confirmation_required"] = envelope.user_confirmation_required
    return metadata


def _optional_ref(value: object, *, field_name: str, allowed_prefixes: tuple[str, ...]) -> str:
    if value in (None, ""):
        return ""
    ref = str(value).strip()
    if not any(ref.startswith(prefix) for prefix in allowed_prefixes):
        raise ValueError(f"{field_name} must be a ref")
    return ref


def _as_refs(values: object) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        return (values,)
    if isinstance(values, (tuple, list, set)):
        return tuple(str(value) for value in values if str(value).strip())
    return ()


def _unique_refs(*refs: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(ref for ref in refs if str(ref).strip()))


def _safe_handoff_metadata(values: dict[str, Any]) -> dict[str, Any]:
    return {
        str(key): value
        for key, value in values.items()
        if not _metadata_key_is_blocked(key)
    }


def _cross_agent_refs_only_metadata(values: dict[str, Any]) -> dict[str, Any]:
    refs_only: dict[str, Any] = {}
    for key, value in values.items():
        key_text = str(key)
        if not _metadata_key_is_refs_only(key_text):
            continue
        if key_text.endswith("_refs") or key_text == "low_confidence_flags":
            refs_only[key_text] = _as_refs(value)
        elif key_text.endswith("_ref"):
            ref = str(value).strip()
            if ref:
                refs_only[key_text] = ref
        elif key_text.endswith("_id"):
            normalized = str(value).strip()
            if normalized:
                refs_only[key_text] = normalized
    return refs_only


def _metadata_key_is_refs_only(key: str) -> bool:
    return key in _CROSS_AGENT_REFS_ONLY_KEYS or key.endswith(("_ref", "_refs", "_id"))


def _reject_unsafe_handoff_metadata(value: object, *, label: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _metadata_key_is_blocked(key):
                raise ValueError(f"{label} contains unsafe metadata")
            _reject_unsafe_handoff_metadata(item, label=label)
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            _reject_unsafe_handoff_metadata(item, label=label)


def _metadata_key_is_blocked(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in _FORMAL_METADATA_KEY_EXCEPTIONS:
        return False
    return any(part in normalized for part in _BLOCKED_METADATA_KEY_PARTS)


__all__ = ["AgentHandoffEnvelope", "HandoffContract", "build_agent_handoff_plan", "execute_agent_handoff"]
