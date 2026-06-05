"""Phase 5 Question Agent planned guarded workflow bridge."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from app.application.ai_runtime.business_graphs.polish_question_graph import (
    build_polish_question_candidate_from_draft,
    question_candidate_quality_gate,
)
from app.application.ai_runtime.contracts import RuntimeValidationError
from app.application.polish.entities import PolishTaskStatus
from app.application.polish.question_generation_policy import (
    DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY,
    QuestionGenerationRuntimePolicy,
)
from app.application.polish.question_generation_service import QuestionGenerationResult
from app.domain.polish.policies.question_grounding_policy import (
    QuestionGroundingInput,
    QuestionGroundingPolicy,
)
from app.domain.polish.policies.source_support_policy import (
    SourceSupportEvidence,
    SourceSupportPolicy,
    SourceSupportTarget,
)
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.refs import ResourceRef, TraceRef


QUESTION_PLANNED_WORKFLOW = "phase5_question_agent_l2"
QUESTION_AGENT_ID = "polish_question_agent"
QUESTION_CANDIDATE_SCHEMA_ID = "agent.polish_question.handoff_payload.v1"
QUESTION_HANDOFF_CONTRACT_ID = "handoff.polish_question_agent.v1"
QUESTION_TRACE_CONTRACT_ID = "trace.polish_question_agent.v1"
QUESTION_POLICY_REFS = (
    "source_support_policy.v1",
    "question_grounding_policy.v1",
    "follow_up_coverage_policy.v1",
    "question_anti_repetition_policy.v1",
)
QUESTION_SKILL_REFS = (
    "qag_source_support_classification_skill",
    "qag_question_intent_planning_skill",
    "qag_question_kind_selection_skill",
    "qag_evidence_grounding_skill",
    "qag_follow_up_coverage_skill",
    "qag_anti_repetition_skill",
    "qag_expected_point_drafting_skill",
    "qag_rubric_drafting_skill",
)
QUESTION_TOOL_REFS = (
    "qag_canonical_evidence_pack",
    "qag_progress_node",
    "qag_prior_questions",
    "qag_prior_feedback",
    "qag_same_focus_history",
    "qag_source_support_classifier",
    "qag_question_grounding_validator",
    "qag_follow_up_coverage_evaluator",
)


@dataclass(frozen=True)
class QuestionPlannedWorkflowResult:
    candidate: dict[str, Any]
    task_candidate_refs: tuple[ResourceRef, ...]
    question_candidate_ref: str
    validation_errors: tuple[str, ...]
    validation_refs: tuple[str, ...]
    trace_refs: tuple[str, ...]
    policy_refs: tuple[str, ...] = QUESTION_POLICY_REFS


def run_question_planned_workflow(
    *,
    owner_id: str,
    session_id: str,
    ai_task_id: str,
    agent_run_id: str,
    progress_context: dict[str, Any],
    requested_progress_node_ref: str | None,
    generation_result: QuestionGenerationResult | None = None,
    candidate_payload: dict[str, Any] | None = None,
    graph_fallback_reason: str | None = None,
    trace_refs: tuple[str, ...] = (),
    follow_up_context: dict[str, Any] | None = None,
    runtime_policy: QuestionGenerationRuntimePolicy | None = None,
) -> QuestionPlannedWorkflowResult:
    """Build and validate a Phase 5 question_candidate without writing formal data."""

    policy = runtime_policy or DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY
    if candidate_payload is None:
        if generation_result is None:
            raise RuntimeValidationError("question planned workflow requires a candidate or generation result")
        candidate = _question_candidate_from_generation_result(
            owner_id=owner_id,
            session_id=session_id,
            ai_task_id=ai_task_id,
            agent_run_id=agent_run_id,
            result=generation_result,
            graph_fallback_reason=graph_fallback_reason,
        )
    else:
        candidate = dict(candidate_payload)

    candidate = _with_planned_workflow_metadata(
        candidate,
        progress_context=progress_context,
        graph_fallback_reason=graph_fallback_reason,
        follow_up_context=follow_up_context,
        runtime_policy=policy,
    )
    combined_trace_refs = _clean_ref_tuple((*trace_refs, *(_clean_ref_tuple(candidate.get("trace_refs", ())))))
    validation_refs = _validation_refs(candidate, trace_refs=combined_trace_refs, follow_up_context=follow_up_context)
    metadata = dict(candidate.get("question_metadata")) if isinstance(candidate.get("question_metadata"), dict) else {}
    metadata["validation_refs"] = list(validation_refs)
    metadata["trace_refs"] = list(combined_trace_refs)
    candidate["question_metadata"] = metadata

    validation_errors = _non_success_reasons(candidate)
    return QuestionPlannedWorkflowResult(
        candidate=candidate,
        task_candidate_refs=_task_candidate_refs(
            agent_run_id=agent_run_id,
            candidate=candidate,
            trace_refs=combined_trace_refs,
            validation_refs=validation_refs,
            requested_progress_node_ref=requested_progress_node_ref,
        ),
        question_candidate_ref=str(candidate.get("candidate_ref") or ai_task_id),
        validation_errors=validation_errors,
        validation_refs=validation_refs,
        trace_refs=combined_trace_refs,
    )


def build_question_candidate_validation_task(
    *,
    ai_task_id: str,
    workflow_result: QuestionPlannedWorkflowResult,
    validation_errors: tuple[str, ...] | None,
    created_at: Any,
    runtime_policy: QuestionGenerationRuntimePolicy,
) -> PolishTaskStatus:
    errors = validation_errors if validation_errors is not None else workflow_result.validation_errors
    return PolishTaskStatus(
        ai_task_id=ai_task_id,
        task_type=runtime_policy.task_type,
        status=AiTaskStatus.VALIDATION_FAILED,
        contract_ids=runtime_policy.contract_ids,
        retryable=False,
        result_ref=TraceRef(
            trace_ref_id=workflow_result.question_candidate_ref,
            trace_type="question_candidate",
            created_at=created_at,
        ),
        user_visible_status="题目生成降级为候选，未写入正式题目",
        candidate_refs=workflow_result.task_candidate_refs,
        validation_errors=tuple(dict.fromkeys(error for error in (errors or ()) if error)),
    )


def _question_candidate_from_generation_result(
    *,
    owner_id: str,
    session_id: str,
    ai_task_id: str,
    agent_run_id: str,
    result: QuestionGenerationResult,
    graph_fallback_reason: str | None,
) -> dict[str, Any]:
    if result.draft is None:
        raise RuntimeValidationError("question generation result has no draft")
    draft = result.draft
    metadata = draft.question_metadata if isinstance(draft.question_metadata, dict) else {}
    scenario = {
        "session_ref": session_id,
        "scenario_title": metadata.get("focus_dimension")
        or metadata.get("question_kind")
        or draft.progress_node_ref
        or "question_candidate",
        "scenario_summary": draft.question_text[:240],
        "scenario_mode": _scenario_mode(metadata.get("source_support_level")),
        "source_refs": tuple(str(ref) for ref in draft.evidence_refs if str(ref).strip()),
        "source_types": tuple(
            dict.fromkeys(
                str(source.source_type)
                for source in draft.question_sources
                if str(source.source_type).strip()
            )
        ),
        "selected_progress_node_summary": metadata.get("focus_dimension") or "",
        "selected_evidence_refs": tuple(str(ref) for ref in draft.evidence_refs if str(ref).strip()),
        "allowed_entities": (),
        "forbidden_entities": (),
        "confidence_level": draft.confidence_level or metadata.get("confidence_level") or "medium",
        "low_confidence_flags": tuple(draft.low_confidence_flags),
        "source_support_summary": metadata.get("source_support_summary"),
        "source_support_level": metadata.get("source_support_level"),
        "context_source": "question_generation_service",
        "context_source_version": metadata.get("generation_service"),
        "repository_backed_context": True,
    }
    provider_trace_refs = tuple(
        str(ref)
        for ref in metadata.get("llm_trace_refs", ())
        if isinstance(ref, str) and ref.strip()
    )
    candidate = build_polish_question_candidate_from_draft(
        owner_id=owner_id,
        run_id=agent_run_id,
        ai_task_id=ai_task_id,
        session_ref=session_id,
        draft=draft,
        scenario=scenario,
        provider_trace_refs=provider_trace_refs,
    )
    candidate["quality_gate"] = question_candidate_quality_gate(candidate)
    if graph_fallback_reason is None:
        return candidate
    question_metadata = (
        dict(candidate.get("question_metadata")) if isinstance(candidate.get("question_metadata"), dict) else {}
    )
    question_metadata.setdefault("graph_fallback_reason", graph_fallback_reason)
    candidate = dict(candidate)
    candidate["question_metadata"] = question_metadata
    return candidate


def _with_planned_workflow_metadata(
    candidate: dict[str, Any],
    *,
    progress_context: dict[str, Any],
    graph_fallback_reason: str | None,
    follow_up_context: dict[str, Any] | None,
    runtime_policy: QuestionGenerationRuntimePolicy,
) -> dict[str, Any]:
    candidate_payload = dict(candidate)
    metadata = (
        dict(candidate_payload.get("question_metadata"))
        if isinstance(candidate_payload.get("question_metadata"), dict)
        else {}
    )
    source_summary = _source_support_summary(
        candidate_payload,
        progress_context=progress_context,
        metadata=metadata,
    )
    source_support_level = metadata.get("source_support_level") or source_summary.get("level")
    metadata.setdefault("source_support_summary", source_summary)
    if source_support_level:
        metadata.setdefault("source_support_level", source_support_level)
    if graph_fallback_reason is not None:
        metadata.setdefault("graph_fallback_reason", graph_fallback_reason)
        metadata.setdefault("graph_status", "disabled_fallback")
    candidate_payload["question_metadata"] = metadata

    grounding_decision = _grounding_decision(
        candidate_payload,
        source_support_level=source_support_level,
        progress_context=progress_context,
        metadata=metadata,
    )
    candidate_payload = _apply_grounding_gate(
        candidate_payload,
        grounding_decision=grounding_decision,
        source_support_level=source_support_level,
    )
    metadata = (
        {**metadata, **dict(candidate_payload.get("question_metadata"))}
        if isinstance(candidate_payload.get("question_metadata"), dict)
        else metadata
    )
    metadata.update(
        {
            "planned_workflow": QUESTION_PLANNED_WORKFLOW,
            "agent_id": QUESTION_AGENT_ID,
            "candidate_output": "question_candidate",
            "candidate_schema_id": QUESTION_CANDIDATE_SCHEMA_ID,
            "candidate_ref": candidate_payload.get("candidate_ref"),
            "handoff_contract": QUESTION_HANDOFF_CONTRACT_ID,
            "trace_contract": QUESTION_TRACE_CONTRACT_ID,
            "policy_refs": list(QUESTION_POLICY_REFS),
            "skill_refs": list(QUESTION_SKILL_REFS),
            "tool_refs": list(QUESTION_TOOL_REFS),
            "runtime_task_type": runtime_policy.task_type,
            "grounding_policy_result": _grounding_payload(grounding_decision),
            "follow_up_coverage_policy_result": _follow_up_policy_result(follow_up_context),
            "anti_repetition_policy_result": _anti_repetition_policy_result(follow_up_context),
            "formal_write_boundary": "Application Service -> AgentPersistenceHandoff",
            "fallback_reported_as_generated_success": False,
        }
    )
    candidate_payload["question_metadata"] = metadata
    return candidate_payload


def _source_support_summary(
    candidate: dict[str, Any],
    *,
    progress_context: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    for value in (
        metadata.get("source_support_summary"),
        candidate.get("source_support_summary"),
        _canonical_pack(progress_context).get("source_support_summary"),
    ):
        if isinstance(value, dict) and value.get("level"):
            return dict(value)
    decision = SourceSupportPolicy.classify_question_context(
        target=SourceSupportTarget(
            title=str(candidate.get("question_text") or ""),
            expected_capability=str(metadata.get("focus_dimension") or metadata.get("question_kind") or ""),
            missing_points=tuple(str(item) for item in metadata.get("expected_answer_dimensions", ()) if str(item)),
        ),
        evidence=_source_support_evidence(candidate),
        canonical_project_assets_available=_canonical_assets_available(progress_context),
        canonical_project_asset_texts=_canonical_asset_texts(progress_context),
        existing_level=metadata.get("source_support_level") or _canonical_pack(progress_context).get("source_support_level"),
    )
    return decision.to_summary().to_dict()


def _grounding_decision(
    candidate: dict[str, Any],
    *,
    source_support_level: object,
    progress_context: dict[str, Any],
    metadata: dict[str, Any],
):
    evidence_refs = _clean_ref_tuple(candidate.get("evidence_refs", ()))
    primary_evidence_ref = (
        str(metadata.get("primary_question_evidence_ref") or metadata.get("primary_evidence_ref") or "").strip()
        or (evidence_refs[0] if evidence_refs else None)
    )
    primary_source = _primary_source(candidate, primary_evidence_ref=primary_evidence_ref)
    return QuestionGroundingPolicy.evaluate(
        QuestionGroundingInput(
            question_text=str(candidate.get("question_text") or ""),
            claim_mode=str(metadata.get("claim_mode") or "") or None,
            primary_evidence_ref=primary_evidence_ref,
            primary_evidence_text=str(primary_source.get("excerpt") or primary_source.get("title") or "") or None,
            evidence_refs=evidence_refs,
            primary_source_type=str(primary_source.get("source_type") or metadata.get("primary_source_type") or "") or None,
            source_support_level=source_support_level,
            confirmed_asset_texts=_canonical_asset_texts(progress_context),
        )
    )


def _apply_grounding_gate(
    candidate: dict[str, Any],
    *,
    grounding_decision: Any,
    source_support_level: object,
) -> dict[str, Any]:
    candidate_payload = dict(candidate)
    quality_gate = (
        dict(candidate_payload.get("quality_gate"))
        if isinstance(candidate_payload.get("quality_gate"), dict)
        else {}
    )
    existing_blocking = _clean_ref_tuple(quality_gate.get("blocking_reasons", ()))
    policy_blocking = tuple(grounding_decision.blocking_reason_codes)
    if (
        str(source_support_level or "") == "direct_project_evidence"
        and not existing_blocking
        and policy_blocking == ("source_contamination_or_ungrounded_question",)
        and quality_gate.get("passed") is True
    ):
        policy_blocking = ()
    blocking = tuple(
        dict.fromkeys(
            (*existing_blocking, *policy_blocking)
        )
    )
    low_confidence = tuple(
        dict.fromkeys(
            (*_clean_ref_tuple(quality_gate.get("low_confidence_reasons", ())), *grounding_decision.warning_reason_codes)
        )
    )
    if blocking:
        quality_gate["passed"] = False
        quality_gate["status"] = "blocked"
        quality_gate["blocking_reasons"] = blocking
    else:
        quality_gate.setdefault("passed", True)
        quality_gate.setdefault("status", "accepted")
    if low_confidence:
        quality_gate["low_confidence_reasons"] = low_confidence
    candidate_payload["quality_gate"] = quality_gate

    metadata = (
        dict(candidate_payload.get("question_metadata"))
        if isinstance(candidate_payload.get("question_metadata"), dict)
        else {}
    )
    metadata["grounding_policy_result"] = _grounding_payload(grounding_decision)
    if grounding_decision.requires_clarification:
        flags = list(_clean_ref_tuple(candidate_payload.get("low_confidence_flags", ())))
        flags.append("insufficient_context")
        candidate_payload["low_confidence_flags"] = tuple(dict.fromkeys(flags))
        metadata["manual_review_required"] = True
        metadata.setdefault("manual_review_reason", "insufficient_context")
    candidate_payload["question_metadata"] = metadata
    return candidate_payload


def _validation_refs(
    candidate: dict[str, Any],
    *,
    trace_refs: tuple[str, ...],
    follow_up_context: dict[str, Any] | None,
) -> tuple[str, ...]:
    refs = [
        "validation_ref_source_support",
        "validation_ref_question_grounding",
    ]
    if follow_up_context is not None:
        refs.extend(("validation_ref_follow_up_coverage", "validation_ref_question_anti_repetition"))
    refs.extend(ref for ref in trace_refs if ref.startswith("validation_ref_"))
    refs.extend(
        ref
        for ref in _clean_ref_tuple(candidate.get("trace_refs", ()))
        if ref.startswith("validation_ref_")
    )
    return tuple(dict.fromkeys(refs))


def _non_success_reasons(candidate: dict[str, Any]) -> tuple[str, ...]:
    metadata = candidate.get("question_metadata") if isinstance(candidate.get("question_metadata"), dict) else {}
    reasons: list[str] = []
    provider_status = str(metadata.get("provider_status") or "").strip()
    generation_mode = str(metadata.get("llm_generation_mode") or "").strip()
    fallback_reason = str(metadata.get("fallback_reason") or "").strip()
    fallback_visible = metadata.get("fallback_visible") is True
    if fallback_visible and fallback_reason:
        reasons.append(fallback_reason)
    if provider_status in {"not_configured", "fake_transport", "failed", "not_called"}:
        reasons.append(provider_status)
    if "deterministic" in generation_mode or "fake" in generation_mode:
        reasons.append(generation_mode)
    return tuple(dict.fromkeys(reason for reason in reasons if reason))


def _task_candidate_refs(
    *,
    agent_run_id: str,
    candidate: dict[str, Any],
    trace_refs: tuple[str, ...],
    validation_refs: tuple[str, ...],
    requested_progress_node_ref: str | None,
) -> tuple[ResourceRef, ...]:
    refs: list[ResourceRef] = []
    if agent_run_id:
        refs.append(ResourceRef(resource_type="agent_run", resource_id=agent_run_id))
    candidate_ref = str(candidate.get("candidate_ref") or "").strip()
    if candidate_ref:
        refs.append(ResourceRef(resource_type="question_candidate", resource_id=candidate_ref))
    progress_node_ref = str(candidate.get("progress_node_ref") or requested_progress_node_ref or "").strip()
    if progress_node_ref:
        refs.append(ResourceRef(resource_type="progress_node", resource_id=progress_node_ref))
    refs.extend(
        ResourceRef(resource_type="evidence", resource_id=ref)
        for ref in _clean_ref_tuple(candidate.get("evidence_refs", ()))
    )
    refs.extend(ResourceRef(resource_type="validation_result", resource_id=ref) for ref in validation_refs)
    refs.extend(ResourceRef(resource_type="trace", resource_id=ref) for ref in _clean_ref_tuple(trace_refs))
    return tuple(refs)


def _source_support_evidence(candidate: dict[str, Any]) -> tuple[SourceSupportEvidence, ...]:
    sources = candidate.get("question_sources")
    if not isinstance(sources, (list, tuple)):
        return ()
    evidence: list[SourceSupportEvidence] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        evidence.append(
            SourceSupportEvidence(
                source_type=str(source.get("source_type") or ""),
                text=" ".join(
                    str(item)
                    for item in (source.get("title"), source.get("excerpt"))
                    if str(item or "").strip()
                ),
                ref=str(source.get("ref_id") or source.get("resource_id") or "") or None,
            )
        )
    return tuple(evidence)


def _primary_source(candidate: dict[str, Any], *, primary_evidence_ref: str | None) -> dict[str, Any]:
    sources = candidate.get("question_sources")
    if not isinstance(sources, (list, tuple)):
        return {}
    fallback: dict[str, Any] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        if not fallback:
            fallback = source
        ref = str(source.get("ref_id") or source.get("resource_id") or "").strip()
        if primary_evidence_ref and ref == primary_evidence_ref:
            return source
    return fallback


def _canonical_pack(progress_context: dict[str, Any]) -> dict[str, Any]:
    pack = progress_context.get("canonical_evidence_pack")
    return dict(pack) if isinstance(pack, dict) else {}


def _canonical_assets_available(progress_context: dict[str, Any]) -> bool:
    assets = _canonical_pack(progress_context).get("canonical_project_assets")
    if isinstance(assets, dict):
        return bool(assets.get("available") or assets.get("items"))
    return bool(assets)


def _canonical_asset_texts(progress_context: dict[str, Any]) -> tuple[str, ...]:
    assets = _canonical_pack(progress_context).get("canonical_project_assets")
    items: list[object]
    if isinstance(assets, dict):
        raw_items = assets.get("items") or assets.get("assets") or ()
        items = list(raw_items) if isinstance(raw_items, (list, tuple)) else []
    elif isinstance(assets, (list, tuple)):
        items = list(assets)
    else:
        items = []
    texts: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = " ".join(
                str(value)
                for value in (item.get("title"), item.get("summary"), item.get("excerpt"))
                if str(value or "").strip()
            )
        else:
            text = str(item)
        if text.strip():
            texts.append(text.strip())
    return tuple(dict.fromkeys(texts))


def _follow_up_policy_result(follow_up_context: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(follow_up_context, dict):
        return {"status": "not_applicable", "policy": "follow_up_coverage_policy.v1"}
    matrix = follow_up_context.get("coverage_matrix")
    return {
        "status": "evaluated",
        "policy": "follow_up_coverage_policy.v1",
        "focus_key": follow_up_context.get("focus_key"),
        "focus_source": follow_up_context.get("focus_source"),
        "recommended_action": follow_up_context.get("recommended_action"),
        "completion_status": follow_up_context.get("completion_status"),
        "coverage_matrix": matrix if isinstance(matrix, dict) else {},
    }


def _anti_repetition_policy_result(follow_up_context: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(follow_up_context, dict):
        return {"status": "not_applicable", "policy": "question_anti_repetition_policy.v1"}
    used_focus_refs = _clean_ref_tuple(follow_up_context.get("completed_focus_refs", ()))
    return {
        "status": "passed",
        "policy": "question_anti_repetition_policy.v1",
        "focus_key": follow_up_context.get("focus_key"),
        "anti_repeat_refs": list(used_focus_refs),
    }


def _grounding_payload(decision: Any) -> dict[str, Any]:
    return {
        "action": str(getattr(decision, "action", "")),
        "passed": bool(getattr(decision, "passed", False)),
        "reason_codes": list(getattr(decision, "reason_codes", ())),
        "blocking_reason_codes": list(getattr(decision, "blocking_reason_codes", ())),
        "warning_reason_codes": list(getattr(decision, "warning_reason_codes", ())),
        "requires_clarification": bool(getattr(decision, "requires_clarification", False)),
        "manual_review_recommended": bool(getattr(decision, "manual_review_recommended", False)),
    }


def _scenario_mode(source_support_level: object) -> str:
    level = str(source_support_level or "").strip()
    if level in {"job_gap_only", "insufficient_context"}:
        return "job_gap"
    if level == "adjacent_project_evidence":
        return "learning_gap"
    return "resume_project"


def _clean_ref_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, set)):
        return ()
    return tuple(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))


def build_direct_question_agent_run_id(
    *,
    owner_id: str,
    session_id: str,
    ai_task_id: str,
    progress_node_ref: str | None,
) -> str:
    return "arun_question_candidate_" + sha256(
        json.dumps(
            {
                "owner_id": owner_id,
                "session_id": session_id,
                "ai_task_id": ai_task_id,
                "progress_node_ref": progress_node_ref or "",
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:16]
