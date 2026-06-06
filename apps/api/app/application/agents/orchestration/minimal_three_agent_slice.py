"""Deterministic refs-only Phase 11 minimal three-agent product slice."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any

from app.application.agents.definitions.asset_candidate import ASSET_CANDIDATE_AGENT_ID
from app.application.agents.definitions.orchestrator import INTERVIEW_ORCHESTRATOR_AGENT_ID
from app.application.agents.definitions.polish.feedback import POLISH_FEEDBACK_AGENT_ID
from app.application.agents.definitions.training_plan import TRAINING_PLAN_AGENT_ID


PRODUCT_SLICE_STATUS_READY = "candidate_product_slice_ready"
PRODUCT_SLICE_STATUS_BLOCKED = "blocked"
PRODUCT_SLICE_STATUS_FAILED_CLOSED = "failed_closed"

FEEDBACK_TO_ASSET_HANDOFF_TYPE = "feedback_candidate_to_asset_update_candidate"
ASSET_TO_TRAINING_HANDOFF_TYPE = "asset_update_candidate_to_training_plan_candidate"

BUSINESS_AGENT_IDS = (
    POLISH_FEEDBACK_AGENT_ID,
    ASSET_CANDIDATE_AGENT_ID,
    TRAINING_PLAN_AGENT_ID,
)

_BLOCKED_METADATA_KEY_PARTS = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "checkpoint_payload",
    "full_source_body",
    "full_resume",
    "full_jd",
    "full_answer",
    "full_asset_body",
    "hidden_rubric",
    "formal_ref",
    "formal_output",
    "formal_write_count",
    "formal_write_result",
    "formal_write_payload",
    "api_key",
    "token",
    "cookie",
    "secret",
)

_METADATA_KEY_EXCEPTIONS = {
    "formal_write_blocked",
    "formal_write_blocked_until",
}


@dataclass(frozen=True)
class MinimalThreeAgentCandidate:
    """Candidate ref emitted by the deterministic product slice."""

    candidate_type: str
    candidate_ref: str
    source_agent_id: str
    trace_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_refs: tuple[str, ...] = field(default_factory=tuple)
    depends_on_candidate_refs: tuple[str, ...] = field(default_factory=tuple)
    formal_write_blocked: bool = True
    user_confirmation_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace_refs", _clean_refs(self.trace_refs))
        object.__setattr__(self, "validation_refs", _clean_refs(self.validation_refs))
        object.__setattr__(self, "depends_on_candidate_refs", _clean_refs(self.depends_on_candidate_refs))
        object.__setattr__(self, "metadata", _safe_metadata(self.metadata))


@dataclass(frozen=True)
class MinimalThreeAgentHandoff:
    """Typed refs-only handoff metadata between business agents."""

    handoff_ref: str
    source_agent_id: str
    target_agent_id: str
    handoff_type: str
    candidate_type: str
    candidate_ref: str
    source_candidate_ref: str
    trace_refs: tuple[str, ...]
    validation_refs: tuple[str, ...]
    side_effect_policy: str = "candidate_write"
    formal_write_blocked: bool = True
    user_confirmation_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace_refs", _clean_refs(self.trace_refs))
        object.__setattr__(self, "validation_refs", _clean_refs(self.validation_refs))
        object.__setattr__(self, "metadata", _safe_metadata(self.metadata))


@dataclass(frozen=True)
class MinimalThreeAgentProductSliceResult:
    """Refs-only candidate workflow result; it is not a formal write result."""

    workflow_ref: str
    orchestrator_agent_id: str
    participant_agent_ids: tuple[str, ...]
    candidate_refs: dict[str, str]
    handoff_refs: tuple[MinimalThreeAgentHandoff, ...]
    validation_refs: tuple[str, ...]
    trace_refs: tuple[str, ...]
    timeline_events: tuple[dict[str, Any], ...]
    hitl_required: bool
    blocking_reasons: tuple[str, ...]
    formal_write_blocked: bool
    asset_update_user_confirmation_required: bool
    status: str
    failure_reason: str
    metadata: dict[str, Any] = field(default_factory=dict)
    candidates: tuple[MinimalThreeAgentCandidate, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "participant_agent_ids", _clean_refs(self.participant_agent_ids))
        object.__setattr__(self, "validation_refs", _clean_refs(self.validation_refs))
        object.__setattr__(self, "trace_refs", _clean_refs(self.trace_refs))
        object.__setattr__(self, "blocking_reasons", _clean_refs(self.blocking_reasons))
        object.__setattr__(
            self,
            "timeline_events",
            tuple(_safe_metadata(event) for event in self.timeline_events),
        )
        object.__setattr__(self, "metadata", _safe_metadata(self.metadata))
        object.__setattr__(self, "candidates", tuple(self.candidates))


def build_minimal_three_agent_product_slice(
    *,
    owner_id: str,
    session_ref: str,
    feedback_candidate_ref: str,
    answer_ref: str,
    question_ref: str,
    evidence_refs: tuple[str, ...] | list[str],
    source_trace_refs: tuple[str, ...] | list[str],
    validation_refs: tuple[str, ...] | list[str],
    asset_conflict_ref: str = "",
    low_confidence_flags: tuple[str, ...] | list[str] = (),
    idempotency_key: str = "",
    formal_write_requested: bool = False,
    formal_write_requested_ref: str = "",
    metadata: dict[str, Any] | None = None,
) -> MinimalThreeAgentProductSliceResult:
    """Build a deterministic candidate-only product slice from refs.

    The function constructs refs and metadata only. It does not execute agents,
    call providers, render prompts, read storage or write formal business facts.
    """

    base_refs = {
        "owner_id": owner_id,
        "session_ref": session_ref,
        "feedback_candidate_ref": feedback_candidate_ref,
        "answer_ref": answer_ref,
        "question_ref": question_ref,
        "evidence_refs": _clean_refs(evidence_refs),
        "source_trace_refs": _clean_refs(source_trace_refs),
        "validation_refs": _clean_refs(validation_refs),
        "idempotency_key": idempotency_key,
    }
    workflow_ref = "workflow_ref_" + _digest(base_refs)
    safe_metadata = _safe_metadata(metadata)
    low_confidence = _clean_refs(low_confidence_flags)
    asset_conflict_ref = str(asset_conflict_ref).strip()
    formal_write_requested_ref = str(formal_write_requested_ref).strip()

    missing_required_refs = _missing_required_refs(base_refs)
    if missing_required_refs:
        return _blocked_result(
            workflow_ref=workflow_ref,
            status=PRODUCT_SLICE_STATUS_FAILED_CLOSED,
            failure_reason="missing_required_refs",
            blocking_reasons=tuple(f"missing:{item}" for item in missing_required_refs),
            trace_refs=base_refs["source_trace_refs"],
            validation_refs=base_refs["validation_refs"],
            low_confidence_flags=low_confidence,
            metadata={**safe_metadata, "missing_required_refs": missing_required_refs},
        )

    trace_refs = _unique_refs(
        *base_refs["source_trace_refs"],
        f"trace.{workflow_ref}.plan",
        f"trace.{workflow_ref}.feedback_to_asset",
        f"trace.{workflow_ref}.asset_to_training",
    )
    policy_refs = (
        "candidate_only_policy",
        "formal_write_blocked_policy",
        "asset_update_user_confirmation_policy",
    )

    if formal_write_requested or formal_write_requested_ref:
        interrupt_ref = formal_write_requested_ref or f"interrupt_ref_{_digest({'workflow_ref': workflow_ref, 'reason': 'formal_write_requested'})}"
        return _blocked_result(
            workflow_ref=workflow_ref,
            status=PRODUCT_SLICE_STATUS_BLOCKED,
            failure_reason="formal_write_requested",
            blocking_reasons=("formal_write_requested",),
            trace_refs=trace_refs,
            validation_refs=base_refs["validation_refs"],
            low_confidence_flags=low_confidence,
            interrupt_refs=(interrupt_ref,),
            metadata={
                **safe_metadata,
                "policy_refs": policy_refs,
                "formal_write_blocked": True,
                "formal_write_requested_ref": interrupt_ref,
            },
        )

    if asset_conflict_ref:
        return _blocked_result(
            workflow_ref=workflow_ref,
            status=PRODUCT_SLICE_STATUS_BLOCKED,
            failure_reason="asset_conflict",
            blocking_reasons=("asset_conflict",),
            trace_refs=trace_refs,
            validation_refs=base_refs["validation_refs"],
            low_confidence_flags=low_confidence,
            interrupt_refs=(asset_conflict_ref,),
            candidate_refs={"feedback_candidate": feedback_candidate_ref},
            candidates=(
                MinimalThreeAgentCandidate(
                    candidate_type="feedback_candidate",
                    candidate_ref=feedback_candidate_ref,
                    source_agent_id=POLISH_FEEDBACK_AGENT_ID,
                    trace_refs=trace_refs,
                    validation_refs=base_refs["validation_refs"],
                ),
            ),
            metadata={
                **safe_metadata,
                "asset_conflict_ref": asset_conflict_ref,
                "policy_refs": policy_refs,
                "formal_write_blocked": True,
            },
        )

    asset_update_candidate_ref = "asset_update_candidate_ref_" + _digest(
        {
            "workflow_ref": workflow_ref,
            "feedback_candidate_ref": feedback_candidate_ref,
            "answer_ref": answer_ref,
            "question_ref": question_ref,
        }
    )
    training_plan_candidate_ref = "training_plan_candidate_ref_" + _digest(
        {
            "workflow_ref": workflow_ref,
            "feedback_candidate_ref": feedback_candidate_ref,
            "asset_update_candidate_ref": asset_update_candidate_ref,
            "evidence_refs": base_refs["evidence_refs"],
        }
    )
    feedback_to_asset_handoff = MinimalThreeAgentHandoff(
        handoff_ref="handoff_ref_" + _digest(
            {
                "workflow_ref": workflow_ref,
                "handoff_type": FEEDBACK_TO_ASSET_HANDOFF_TYPE,
                "source": feedback_candidate_ref,
                "target": asset_update_candidate_ref,
            }
        ),
        source_agent_id=POLISH_FEEDBACK_AGENT_ID,
        target_agent_id=ASSET_CANDIDATE_AGENT_ID,
        handoff_type=FEEDBACK_TO_ASSET_HANDOFF_TYPE,
        candidate_type="asset_update_candidate",
        candidate_ref=asset_update_candidate_ref,
        source_candidate_ref=feedback_candidate_ref,
        trace_refs=trace_refs,
        validation_refs=base_refs["validation_refs"],
        user_confirmation_required=True,
        metadata={"policy_refs": policy_refs, "formal_write_blocked": True},
    )
    asset_to_training_handoff = MinimalThreeAgentHandoff(
        handoff_ref="handoff_ref_" + _digest(
            {
                "workflow_ref": workflow_ref,
                "handoff_type": ASSET_TO_TRAINING_HANDOFF_TYPE,
                "source": asset_update_candidate_ref,
                "target": training_plan_candidate_ref,
            }
        ),
        source_agent_id=ASSET_CANDIDATE_AGENT_ID,
        target_agent_id=TRAINING_PLAN_AGENT_ID,
        handoff_type=ASSET_TO_TRAINING_HANDOFF_TYPE,
        candidate_type="training_plan_candidate",
        candidate_ref=training_plan_candidate_ref,
        source_candidate_ref=asset_update_candidate_ref,
        trace_refs=trace_refs,
        validation_refs=base_refs["validation_refs"],
        user_confirmation_required=False,
        metadata={"policy_refs": policy_refs, "formal_write_blocked": True},
    )
    candidates = (
        MinimalThreeAgentCandidate(
            candidate_type="feedback_candidate",
            candidate_ref=feedback_candidate_ref,
            source_agent_id=POLISH_FEEDBACK_AGENT_ID,
            trace_refs=trace_refs,
            validation_refs=base_refs["validation_refs"],
            metadata={"source_input_ref": "feedback_candidate_ref"},
        ),
        MinimalThreeAgentCandidate(
            candidate_type="asset_update_candidate",
            candidate_ref=asset_update_candidate_ref,
            source_agent_id=ASSET_CANDIDATE_AGENT_ID,
            trace_refs=trace_refs,
            validation_refs=base_refs["validation_refs"],
            depends_on_candidate_refs=(feedback_candidate_ref,),
            user_confirmation_required=True,
            metadata={"formal_write_blocked_until": "user_confirmation"},
        ),
        MinimalThreeAgentCandidate(
            candidate_type="training_plan_candidate",
            candidate_ref=training_plan_candidate_ref,
            source_agent_id=TRAINING_PLAN_AGENT_ID,
            trace_refs=trace_refs,
            validation_refs=base_refs["validation_refs"],
            depends_on_candidate_refs=(feedback_candidate_ref, asset_update_candidate_ref),
            user_confirmation_required=False,
        ),
    )
    candidate_refs = {candidate.candidate_type: candidate.candidate_ref for candidate in candidates}
    handoff_refs = (feedback_to_asset_handoff, asset_to_training_handoff)
    timeline_events = _timeline_events(
        workflow_ref=workflow_ref,
        candidate_refs=candidate_refs,
        handoff_refs=tuple(handoff.handoff_ref for handoff in handoff_refs),
        validation_refs=base_refs["validation_refs"],
        trace_refs=trace_refs,
        policy_refs=policy_refs,
        low_confidence_flags=low_confidence,
    )
    return MinimalThreeAgentProductSliceResult(
        workflow_ref=workflow_ref,
        orchestrator_agent_id=INTERVIEW_ORCHESTRATOR_AGENT_ID,
        participant_agent_ids=BUSINESS_AGENT_IDS,
        candidate_refs=candidate_refs,
        handoff_refs=handoff_refs,
        validation_refs=base_refs["validation_refs"],
        trace_refs=trace_refs,
        timeline_events=timeline_events,
        hitl_required=True,
        blocking_reasons=(),
        formal_write_blocked=True,
        asset_update_user_confirmation_required=True,
        status=PRODUCT_SLICE_STATUS_READY,
        failure_reason="",
        metadata={
            **safe_metadata,
            "plan_refs": (workflow_ref,),
            "policy_refs": policy_refs,
            "low_confidence_flags": low_confidence,
            "candidate_only": True,
            "formal_write_blocked": True,
            "asset_update_user_confirmation_required": True,
            "llm_call_count": 0,
            "provider_call_count": 0,
            "external_call_count": 0,
        },
        candidates=candidates,
    )


def _blocked_result(
    *,
    workflow_ref: str,
    status: str,
    failure_reason: str,
    blocking_reasons: tuple[str, ...],
    trace_refs: tuple[str, ...],
    validation_refs: tuple[str, ...],
    low_confidence_flags: tuple[str, ...],
    interrupt_refs: tuple[str, ...] = (),
    candidate_refs: dict[str, str] | None = None,
    candidates: tuple[MinimalThreeAgentCandidate, ...] = (),
    metadata: dict[str, Any] | None = None,
) -> MinimalThreeAgentProductSliceResult:
    timeline_event = {
        "event_type": "workflow_blocked" if status == PRODUCT_SLICE_STATUS_BLOCKED else "workflow_failed_closed",
        "plan_refs": (workflow_ref,),
        "candidate_refs": tuple((candidate_refs or {}).values()),
        "handoff_refs": (),
        "validation_refs": validation_refs,
        "trace_refs": trace_refs,
        "interrupt_refs": _clean_refs(interrupt_refs),
        "low_confidence_flags": low_confidence_flags,
        "failure_reason": failure_reason,
        "status": status,
    }
    return MinimalThreeAgentProductSliceResult(
        workflow_ref=workflow_ref,
        orchestrator_agent_id=INTERVIEW_ORCHESTRATOR_AGENT_ID,
        participant_agent_ids=BUSINESS_AGENT_IDS,
        candidate_refs=dict(candidate_refs or {}),
        handoff_refs=(),
        validation_refs=validation_refs,
        trace_refs=trace_refs,
        timeline_events=(timeline_event,),
        hitl_required=status == PRODUCT_SLICE_STATUS_BLOCKED,
        blocking_reasons=blocking_reasons,
        formal_write_blocked=True,
        asset_update_user_confirmation_required=False,
        status=status,
        failure_reason=failure_reason,
        metadata={
            **_safe_metadata(metadata),
            "low_confidence_flags": low_confidence_flags,
            "interrupt_refs": _clean_refs(interrupt_refs),
            "candidate_only": True,
            "formal_write_blocked": True,
        },
        candidates=candidates,
    )


def _missing_required_refs(base_refs: dict[str, object]) -> tuple[str, ...]:
    missing: list[str] = []
    for key in ("owner_id", "session_ref", "feedback_candidate_ref", "answer_ref", "question_ref"):
        if not str(base_refs[key]).strip():
            missing.append(key)
    for key in ("evidence_refs", "source_trace_refs", "validation_refs"):
        if not base_refs[key]:
            missing.append(key)
    return tuple(missing)


def _timeline_events(
    *,
    workflow_ref: str,
    candidate_refs: dict[str, str],
    handoff_refs: tuple[str, ...],
    validation_refs: tuple[str, ...],
    trace_refs: tuple[str, ...],
    policy_refs: tuple[str, ...],
    low_confidence_flags: tuple[str, ...],
) -> tuple[dict[str, Any], ...]:
    base = {
        "plan_refs": (workflow_ref,),
        "candidate_refs": tuple(candidate_refs.values()),
        "handoff_refs": handoff_refs,
        "validation_refs": validation_refs,
        "trace_refs": trace_refs,
        "policy_refs": policy_refs,
        "low_confidence_flags": low_confidence_flags,
        "formal_write_blocked": True,
    }
    return (
        {"event_type": "orchestrator_plan_candidate_created", "agent_id": INTERVIEW_ORCHESTRATOR_AGENT_ID, **base},
        {"event_type": "feedback_candidate_ref_accepted", "agent_id": POLISH_FEEDBACK_AGENT_ID, **base},
        {"event_type": "asset_update_candidate_ref_created", "agent_id": ASSET_CANDIDATE_AGENT_ID, **base},
        {"event_type": "training_plan_candidate_ref_created", "agent_id": TRAINING_PLAN_AGENT_ID, **base},
    )


def _clean_refs(value: tuple[str, ...] | list[str] | set[str] | str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values = (value,)
    else:
        values = tuple(value)
    return tuple(dict.fromkeys(str(item).strip() for item in values if str(item).strip()))


def _unique_refs(*values: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def _safe_metadata(values: dict[str, Any] | None) -> dict[str, Any]:
    return _safe_metadata_value(dict(values or {}))


def _safe_metadata_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _safe_metadata_value(item)
            for key, item in value.items()
            if not _metadata_key_is_blocked(key)
        }
    if isinstance(value, list):
        return [_safe_metadata_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_safe_metadata_value(item) for item in value)
    if isinstance(value, set):
        return tuple(_safe_metadata_value(item) for item in sorted(value, key=str))
    return value


def _metadata_key_is_blocked(key: Any) -> bool:
    normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in _METADATA_KEY_EXCEPTIONS:
        return False
    return any(part in normalized for part in _BLOCKED_METADATA_KEY_PARTS)


def _digest(value: dict[str, Any]) -> str:
    return sha256(
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]


__all__ = [
    "ASSET_TO_TRAINING_HANDOFF_TYPE",
    "BUSINESS_AGENT_IDS",
    "FEEDBACK_TO_ASSET_HANDOFF_TYPE",
    "MinimalThreeAgentCandidate",
    "MinimalThreeAgentHandoff",
    "MinimalThreeAgentProductSliceResult",
    "PRODUCT_SLICE_STATUS_BLOCKED",
    "PRODUCT_SLICE_STATUS_FAILED_CLOSED",
    "PRODUCT_SLICE_STATUS_READY",
    "build_minimal_three_agent_product_slice",
]
