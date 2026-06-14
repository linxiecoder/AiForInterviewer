"""Phase 6 Feedback Agent planned guarded workflow bridge."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from app.application.polish.feedback_generation_service import FeedbackGenerationContext, FeedbackGenerationResult
from app.domain.shared.refs import ResourceRef


FEEDBACK_PLANNED_WORKFLOW = "phase6_feedback_agent_l2"
FEEDBACK_AGENT_ID = "polish_feedback_agent"
FEEDBACK_CANDIDATE_SCHEMA_ID = "agent.polish_feedback.handoff_payload.v1"
FEEDBACK_HANDOFF_CONTRACT_ID = "handoff.polish_feedback_agent.v1"
FEEDBACK_TRACE_CONTRACT_ID = "trace.polish_feedback_agent.v1"
FEEDBACK_POLICY_REFS = (
    "asset_consistency_policy.v1",
    "answer_coverage_policy.v1",
    "answer_change_policy.v1",
    "feedback_next_action_policy.v1",
)


@dataclass(frozen=True)
class FeedbackPlannedHandoff:
    payload: dict[str, Any]
    task_candidate_refs: tuple[ResourceRef, ...]
    feedback_candidate_ref: str
    asset_update_candidate_refs: tuple[str, ...]
    validation_refs: tuple[str, ...]
    trace_refs: tuple[str, ...]


def build_feedback_planned_handoff(
    *,
    payload: dict[str, Any],
    generation_result: FeedbackGenerationResult,
    context: FeedbackGenerationContext,
    task_id: str,
    feedback_id: str,
) -> FeedbackPlannedHandoff:
    stored = dict(payload)
    feedback_candidate_ref = _feedback_candidate_ref(
        context=context,
        task_id=task_id,
        feedback_id=feedback_id,
    )
    trace_refs = _feedback_trace_refs(stored, generation_result)
    validation_refs = _feedback_validation_refs(stored, trace_refs=trace_refs)
    asset_source = stored.get("project_asset_update_candidates")
    if not isinstance(asset_source, (list, tuple)):
        asset_source = _asset_update_candidates_from_cards(stored.get("feedback_cards"))
    asset_update_candidates, asset_candidate_refs = _normalized_asset_update_candidates(
        asset_source,
        feedback_candidate_ref=feedback_candidate_ref,
    )
    _replace_asset_update_candidates_card(stored, asset_update_candidates)
    stored.pop("project_asset_update_candidates", None)
    stored.pop("candidate_refs", None)

    metadata = dict(stored.get("feedback_metadata")) if isinstance(stored.get("feedback_metadata"), dict) else {}
    metadata.update(_safe_generation_metadata(generation_result.metadata))
    metadata.update(
        {
            "planned_workflow": FEEDBACK_PLANNED_WORKFLOW,
            "agent_id": FEEDBACK_AGENT_ID,
            "candidate_output": "feedback_candidate",
            "candidate_schema_id": FEEDBACK_CANDIDATE_SCHEMA_ID,
            "candidate_ref": feedback_candidate_ref,
            "asset_update_candidate_refs": list(asset_candidate_refs),
            "handoff_contract": FEEDBACK_HANDOFF_CONTRACT_ID,
            "trace_contract": FEEDBACK_TRACE_CONTRACT_ID,
            "policy_refs": list(FEEDBACK_POLICY_REFS),
            "validation_refs": list(validation_refs),
            "trace_refs": list(trace_refs),
            "formal_write_boundary": "Application Service -> Feedback planned handoff",
            "asset_update_formal_write_performed": False,
            "asset_update_user_confirmation_required": bool(asset_candidate_refs),
            "silent_degradation_reported_as_generated_success": False,
        }
    )
    stored["feedback_metadata"] = metadata

    return FeedbackPlannedHandoff(
        payload=stored,
        task_candidate_refs=_task_candidate_refs(
            context=context,
            feedback_candidate_ref=feedback_candidate_ref,
            asset_candidate_refs=asset_candidate_refs,
            validation_refs=validation_refs,
            trace_refs=trace_refs,
        ),
        feedback_candidate_ref=feedback_candidate_ref,
        asset_update_candidate_refs=asset_candidate_refs,
        validation_refs=validation_refs,
        trace_refs=trace_refs,
    )


def _feedback_candidate_ref(
    *,
    context: FeedbackGenerationContext,
    task_id: str,
    feedback_id: str,
) -> str:
    return "feedback_candidate_ref_" + _digest(
        {
            "session_id": context.session_id,
            "question_id": context.question_id,
            "answer_id": context.answer_id,
            "task_id": task_id,
            "feedback_id": feedback_id,
        }
    )


def _normalized_asset_update_candidates(
    value: object,
    *,
    feedback_candidate_ref: str,
) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    if not isinstance(value, (list, tuple)):
        return [], ()
    candidates: list[dict[str, Any]] = []
    refs: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            continue
        candidate = dict(item)
        candidate["candidate_type"] = "project_asset_update_candidate"
        candidate["user_confirmation_required"] = True
        candidate_ref = str(candidate.get("candidate_ref") or "").strip()
        if not candidate_ref:
            candidate_ref = "asset_update_candidate_ref_" + _digest(
                {
                    "feedback_candidate_ref": feedback_candidate_ref,
                    "index": index,
                    "summary": candidate.get("summary"),
                    "target_asset_ref": candidate.get("target_asset_ref"),
                }
            )
            candidate["candidate_ref"] = candidate_ref
        candidate.setdefault("handoff_contract", FEEDBACK_HANDOFF_CONTRACT_ID)
        candidate.setdefault("formal_write_blocked_until", "user_confirmation")
        candidates.append(candidate)
        refs.append(candidate_ref)
    return candidates, tuple(dict.fromkeys(refs))


def _replace_asset_update_candidates_card(
    payload: dict[str, Any],
    asset_update_candidates: list[dict[str, Any]],
) -> None:
    cards = payload.get("feedback_cards")
    if not isinstance(cards, list):
        cards = []
    preserved_cards = [
        card
        for card in cards
        if not (isinstance(card, dict) and card.get("card_type") == "asset_update_candidates")
    ]
    if asset_update_candidates:
        preserved_cards.append(
            {
                "card_type": "asset_update_candidates",
                "status": "candidate",
                "payload": asset_update_candidates,
            }
        )
    payload["feedback_cards"] = preserved_cards


def _asset_update_candidates_from_cards(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    for card in value:
        if not isinstance(card, dict) or card.get("card_type") != "asset_update_candidates":
            continue
        payload = card.get("payload")
        if isinstance(payload, list):
            return [dict(item) for item in payload if isinstance(item, dict)]
    return []


def _feedback_trace_refs(
    payload: dict[str, Any],
    generation_result: FeedbackGenerationResult,
) -> tuple[str, ...]:
    refs: list[str] = []
    refs.extend(str(ref).strip() for ref in generation_result.trace_refs if str(ref).strip())
    trace_refs = payload.get("trace_refs")
    if isinstance(trace_refs, (list, tuple)):
        for item in trace_refs:
            if isinstance(item, dict):
                ref = str(item.get("resource_id") or item.get("trace_ref_id") or "").strip()
            else:
                ref = str(item).strip()
            if ref:
                refs.append(ref)
    return tuple(dict.fromkeys(refs))


def _feedback_validation_refs(payload: dict[str, Any], *, trace_refs: tuple[str, ...]) -> tuple[str, ...]:
    refs = [
        "validation_ref_asset_consistency",
        "validation_ref_answer_coverage",
        "validation_ref_answer_change",
        "validation_ref_feedback_next_action",
    ]
    if payload.get("feedback_cards"):
        refs.append("validation_ref_feedback_cards")
    refs.extend(ref for ref in trace_refs if ref.startswith("validation_ref_"))
    return tuple(dict.fromkeys(refs))


def _task_candidate_refs(
    *,
    context: FeedbackGenerationContext,
    feedback_candidate_ref: str,
    asset_candidate_refs: tuple[str, ...],
    validation_refs: tuple[str, ...],
    trace_refs: tuple[str, ...],
) -> tuple[ResourceRef, ...]:
    refs: list[ResourceRef] = [
        ResourceRef(resource_type="feedback_candidate", resource_id=feedback_candidate_ref),
        ResourceRef(resource_type="answer", resource_id=context.answer_id),
        ResourceRef(resource_type="question", resource_id=context.question_id),
    ]
    if context.progress_node_ref:
        refs.append(ResourceRef(resource_type="progress_node", resource_id=context.progress_node_ref))
    refs.extend(ResourceRef(resource_type="evidence", resource_id=ref) for ref in _clean_refs(context.evidence_refs))
    refs.extend(ResourceRef(resource_type="asset_update_candidate", resource_id=ref) for ref in asset_candidate_refs)
    refs.extend(ResourceRef(resource_type="validation_result", resource_id=ref) for ref in validation_refs)
    refs.extend(ResourceRef(resource_type="trace", resource_id=ref) for ref in trace_refs)
    return tuple(refs)


def _safe_generation_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        key_text = str(key)
        if any(forbidden in key_text for forbidden in ("prompt", "completion", "payload", "token", "secret")):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key_text] = value
        elif isinstance(value, (list, tuple)):
            safe[key_text] = [str(item) for item in value[:20]]
    return safe


def _clean_refs(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))


def _digest(value: dict[str, Any]) -> str:
    return sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
