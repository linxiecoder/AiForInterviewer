"""Phase 1 Polish question generation service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.application.llm.ports import LlmTransport
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish.entities import PolishQuestionDraft, PolishQuestionSource, PolishSession
from app.application.polish.progress_evidence import ProgressEvidenceChunk, select_progress_tree_evidence_chunks
from app.application.polish.question_blueprint import (
    CLAIM_MODE_CLARIFICATION_NEEDED,
    EvidenceScope,
    QuestionBlueprint,
    build_question_blueprint,
)
from app.application.polish.question_generation_prompts import (
    build_question_prompt_asset,
    build_question_prompt_metadata,
    render_blueprint_question,
)
from app.application.polish.question_generation_policy import (
    DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY,
    QuestionGenerationRuntimePolicy,
)
from app.application.polish.question_grounding import GroundingResult, validate_question_grounding


QUESTION_GENERATION_SERVICE_VERSION = "polish_question_generation.v1"


@dataclass(frozen=True)
class QuestionGenerationResult:
    succeeded: bool
    draft: PolishQuestionDraft | None
    blueprint: QuestionBlueprint | None
    grounding_result: GroundingResult
    validation_errors: tuple[str, ...] = ()
    progress_node_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()


class QuestionGenerationService:
    def __init__(
        self,
        *,
        llm_transport: LlmTransport | None = None,
        surface_question_builder: Callable[[QuestionBlueprint, EvidenceScope], str] | None = None,
        runtime_policy: QuestionGenerationRuntimePolicy | None = None,
    ) -> None:
        self._llm_transport = llm_transport
        self._surface_question_builder = surface_question_builder or render_blueprint_question
        self._runtime_policy = runtime_policy or DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY

    def generate(
        self,
        *,
        session: PolishSession,
        context: dict[str, Any],
        plan: dict[str, Any],
        state: dict[str, Any],
        requested_ref: str,
    ) -> QuestionGenerationResult:
        node = _resolve_progress_node(plan=plan, state=state, requested_ref=requested_ref)
        if node is None:
            return _validation_failed("progress_node_not_found", progress_node_ref=requested_ref)
        scope = _build_evidence_scope(
            context=context,
            plan=plan,
            state=state,
            node=node,
            requested_ref=requested_ref,
            source_priority_policy=self._runtime_policy.source_priority_by_purpose,
        )
        blueprint = build_question_blueprint(
            scope,
            question_kind_taxonomy=self._runtime_policy.question_kind_taxonomy,
        )
        prompt_asset = build_question_prompt_asset(blueprint, scope, runtime_policy=self._runtime_policy)
        prompt_metadata = build_question_prompt_metadata(prompt_asset, runtime_policy=self._runtime_policy)
        llm_payload: dict[str, Any] | None = None
        llm_result: LlmTransportResult | None = None
        generation_metadata: dict[str, Any]
        if self._llm_transport is not None:
            llm_result = _generate_llm_question(
                transport=self._llm_transport,
                prompt_asset=prompt_asset,
                blueprint=blueprint,
                scope=scope,
                runtime_policy=self._runtime_policy,
            )
            if isinstance(llm_result, QuestionGenerationResult):
                return llm_result
            llm_payload, validation_errors = _parse_llm_question_payload(
                llm_result.result,
                blueprint=blueprint,
            )
            if validation_errors:
                return QuestionGenerationResult(
                    succeeded=False,
                    draft=None,
                    blueprint=blueprint,
                    grounding_result=GroundingResult(False, validation_errors),
                    validation_errors=validation_errors,
                    progress_node_ref=scope.progress_node_ref,
                    evidence_refs=blueprint.evidence_refs,
                )
            question_text = str(llm_payload["question_text"]).strip()
            transport_kind = _clean(llm_result.result.get("transport"))
            is_fake_transport = transport_kind == "fake"
            generation_metadata = {
                "llm_task_type": self._runtime_policy.task_type,
                "prompt_version": self._runtime_policy.prompt_version,
                "llm_output_validation_status": "valid",
                "llm_generation_mode": (
                    "deterministic_fake_transport" if is_fake_transport else "provider_structured_json"
                ),
                "fallback_visible": is_fake_transport,
                "provider_status": "fake_transport" if is_fake_transport else "called",
                "llm_trace_refs": list(llm_result.trace_refs),
                "llm_evidence_refs": list(llm_result.evidence_refs),
            }
            if is_fake_transport:
                generation_metadata["fallback_reason"] = "fake_transport_configured"
        else:
            question_text = self._surface_question_builder(blueprint, scope)
            generation_metadata = {
                "llm_generation_mode": "deterministic_degraded_generation",
                "fallback_reason": "llm_transport_unavailable",
                "fallback_visible": True,
            }
        grounding_result = validate_question_grounding(
            blueprint=blueprint,
            question_text=question_text,
            primary_source_type=scope.primary_source_type,
        )
        if not grounding_result.passed:
            return QuestionGenerationResult(
                succeeded=False,
                draft=None,
                blueprint=blueprint,
                grounding_result=grounding_result,
                validation_errors=grounding_result.validation_errors,
                progress_node_ref=scope.progress_node_ref,
                evidence_refs=blueprint.evidence_refs,
            )
        draft = PolishQuestionDraft(
            question_text=question_text.strip(),
            question_sources=scope.question_sources,
            progress_node_ref=scope.progress_node_ref,
            evidence_refs=blueprint.evidence_refs,
            context_digest=scope.context_digest,
            question_pattern=blueprint.question_kind,
            quality_score=None,
            confidence_level="medium" if blueprint.evidence_refs else "low",
            low_confidence_flags=() if blueprint.evidence_refs else ("clarification_needed",),
            expected_answer_dimensions=_expected_answer_dimensions(blueprint),
            question_metadata={
                "question_pattern": blueprint.question_kind,
                "quality_score": None,
                "quality_warnings": [],
                "confidence_level": "medium" if blueprint.evidence_refs else "low",
                "low_confidence_flags": [] if blueprint.evidence_refs else ["clarification_needed"],
                "expected_answer_dimensions": list(_expected_answer_dimensions(blueprint)),
                "builder_version": QUESTION_GENERATION_SERVICE_VERSION,
                "validator_version": "polish_question_grounding.v1",
                "signal_version": "evidence_grounded_blueprint.v1",
                "source_availability": "available" if blueprint.evidence_refs else "partial",
                "generation_service": QUESTION_GENERATION_SERVICE_VERSION,
                "blueprint_version": blueprint.metadata.get("blueprint_version"),
                **prompt_metadata,
                **generation_metadata,
                "question_kind": blueprint.question_kind,
                "claim_mode": blueprint.claim_mode,
                "llm_difficulty": llm_payload.get("difficulty") if llm_payload else None,
                "llm_skill_dimension": llm_payload.get("skill_dimension") if llm_payload else None,
                "llm_expected_signal": llm_payload.get("expected_signal") if llm_payload else None,
                "llm_missing_context": list(llm_payload.get("missing_context", ())) if llm_payload else [],
                "llm_clarification_needed": bool(llm_payload.get("clarification_needed")) if llm_payload else None,
                "primary_evidence_ref": blueprint.primary_evidence_ref,
                "primary_source_type": scope.primary_source_type,
                "grounding_status": "passed",
                "validation_errors": [],
            },
            builder_version=QUESTION_GENERATION_SERVICE_VERSION,
            validator_version="polish_question_grounding.v1",
        )
        return QuestionGenerationResult(
            succeeded=True,
            draft=draft,
            blueprint=blueprint,
            grounding_result=grounding_result,
            validation_errors=(),
            progress_node_ref=scope.progress_node_ref,
            evidence_refs=blueprint.evidence_refs,
        )


def _generate_llm_question(
    *,
    transport: LlmTransport,
    prompt_asset: dict[str, Any],
    blueprint: QuestionBlueprint,
    scope: EvidenceScope,
    runtime_policy: QuestionGenerationRuntimePolicy,
) -> LlmTransportResult | QuestionGenerationResult:
    request = LlmTransportRequest(
        contract_ids=runtime_policy.contract_ids,
        task_type=runtime_policy.task_type,
        input_refs=(scope.progress_node_ref, *blueprint.evidence_refs),
        evidence_bundle=prompt_asset,
        prompt_version=runtime_policy.prompt_version,
        schema_id=runtime_policy.prompt_schema_id,
    )
    try:
        return transport.generate(request)
    except Exception:
        validation_errors = ("llm_transport_generation_failed",)
        return QuestionGenerationResult(
            succeeded=False,
            draft=None,
            blueprint=blueprint,
            grounding_result=GroundingResult(False, validation_errors),
            validation_errors=validation_errors,
            progress_node_ref=scope.progress_node_ref,
            evidence_refs=blueprint.evidence_refs,
        )


def _parse_llm_question_payload(
    payload: dict[str, Any],
    *,
    blueprint: QuestionBlueprint,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    errors: list[str] = []
    question_text = _clean(payload.get("question_text"))
    if not question_text:
        errors.append("llm_question_text_required")

    question_kind = _clean(payload.get("question_kind"))
    if question_kind and question_kind != blueprint.question_kind:
        errors.append("llm_question_kind_mismatch")
    if not question_kind:
        question_kind = blueprint.question_kind

    focus_dimension = _clean(payload.get("focus_dimension")) or blueprint.question_kind
    difficulty = _clean(payload.get("difficulty"))
    if difficulty not in {"easy", "medium", "hard", "clarification"}:
        errors.append("llm_difficulty_invalid")

    skill_dimension = _clean(payload.get("skill_dimension")) or _clean(blueprint.expected_capability)
    if not skill_dimension:
        errors.append("llm_skill_dimension_required")

    expected_signal = _clean(payload.get("expected_signal"))
    if not expected_signal:
        errors.append("llm_expected_signal_required")

    follow_ups = _string_list(payload.get("follow_ups"), max_items=3)
    if not follow_ups:
        errors.append("llm_follow_ups_required")

    scoring_rubric = _scoring_rubric(payload.get("scoring_rubric"))
    if not scoring_rubric:
        errors.append("llm_scoring_rubric_required")

    missing_context = _string_list(payload.get("missing_context"), max_items=8)
    confidence = _clean(payload.get("confidence"))
    if confidence not in {"high", "medium", "low"}:
        errors.append("llm_confidence_invalid")

    clarification_needed = payload.get("clarification_needed")
    if not isinstance(clarification_needed, bool):
        errors.append("llm_clarification_needed_required")

    evidence_refs = _string_list(payload.get("evidence_refs"), max_items=8)
    allowed_refs = set(blueprint.evidence_refs)
    unknown_refs = [ref for ref in evidence_refs if ref not in allowed_refs]
    if unknown_refs:
        errors.append("llm_evidence_ref_unknown")
    if blueprint.claim_mode != CLAIM_MODE_CLARIFICATION_NEEDED and not evidence_refs:
        errors.append("llm_evidence_refs_required")

    if errors:
        return None, tuple(dict.fromkeys(errors))
    return (
        {
            "question_text": question_text,
            "question_kind": question_kind,
            "focus_dimension": focus_dimension,
            "difficulty": difficulty,
            "skill_dimension": skill_dimension,
            "expected_signal": expected_signal,
            "follow_ups": follow_ups,
            "scoring_rubric": scoring_rubric,
            "missing_context": missing_context,
            "evidence_refs": evidence_refs,
            "confidence": confidence,
            "clarification_needed": clarification_needed,
        },
        (),
    )


def _scoring_rubric(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    items: list[dict[str, Any]] = []
    for raw_item in value[:4]:
        if not isinstance(raw_item, dict):
            continue
        dimension = _clean(raw_item.get("dimension"))
        signals = _string_list(raw_item.get("signals"), max_items=4)
        if dimension and signals:
            items.append({"dimension": dimension, "signals": signals})
    return items


def _validation_failed(reason: str, *, progress_node_ref: str | None = None) -> QuestionGenerationResult:
    grounding_result = GroundingResult(passed=False, validation_errors=(reason,))
    return QuestionGenerationResult(
        succeeded=False,
        draft=None,
        blueprint=None,
        grounding_result=grounding_result,
        validation_errors=grounding_result.validation_errors,
        progress_node_ref=progress_node_ref,
        evidence_refs=(),
    )


def _build_evidence_scope(
    *,
    context: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
    node: dict[str, Any],
    requested_ref: str,
    source_priority_policy: dict[str, dict[str, int]],
) -> EvidenceScope:
    selection = select_progress_tree_evidence_chunks(
        context,
        purpose="next_question",
        max_chunks=4,
        max_chars=1800,
        existing_plan=plan,
        existing_state=state,
        progress_node_ref=requested_ref,
        source_priority_policy=source_priority_policy,
    )
    chunks = tuple(chunk for chunk in selection.selected_chunks if _clean(chunk.text))
    primary = _primary_chunk(chunks, source_priority_policy=source_priority_policy)
    evidence_refs = tuple(chunk.chunk_id for chunk in chunks)
    sources = tuple(_question_source(index=index, chunk=chunk) for index, chunk in enumerate(chunks, start=1))
    node_title = _first_text(node.get("display_title"), node.get("title"), node.get("exam_point"), requested_ref)
    expected_capability = _first_text(node.get("expected_capability"), node.get("description"), node_title)
    return EvidenceScope(
        progress_node_ref=requested_ref,
        node_title=node_title,
        expected_capability=expected_capability,
        missing_points=tuple(_string_list(node.get("missing_points"))),
        primary_evidence_ref=primary.chunk_id if primary is not None else None,
        primary_evidence_text=primary.text if primary is not None else None,
        primary_source_type=primary.source_type if primary is not None else None,
        evidence_refs=evidence_refs,
        question_sources=sources,
        context_digest=_first_text(plan.get("context_digest"), context.get("content_digest"), None),
        dropped_context_summary=selection.dropped_context_summary,
    )


def _resolve_progress_node(
    *,
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str,
) -> dict[str, Any] | None:
    nodes = plan.get("nodes")
    if not isinstance(nodes, list):
        return None
    requested = _find_progress_node(nodes, requested_ref)
    if requested is not None:
        return requested
    priority = state.get("current_priority")
    if isinstance(priority, dict):
        priority_ref = _clean(priority.get("progress_node_ref"))
        if priority_ref:
            return _find_progress_node(nodes, priority_ref)
    leaves = _flatten_leaf_nodes(nodes)
    return leaves[0] if leaves else None


def _find_progress_node(nodes: list[dict[str, Any]], progress_node_ref: str) -> dict[str, Any] | None:
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if _clean(node.get("progress_node_ref")) == progress_node_ref:
            return node
        child = _find_progress_node(node.get("children", []), progress_node_ref)
        if child is not None:
            return child
    return None


def _flatten_leaf_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    leaves: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        children = [child for child in node.get("children", []) if isinstance(child, dict)]
        if children:
            leaves.extend(_flatten_leaf_nodes(children))
        else:
            leaves.append(node)
    return leaves


def _primary_chunk(
    chunks: tuple[ProgressEvidenceChunk, ...],
    *,
    source_priority_policy: dict[str, dict[str, int]],
) -> ProgressEvidenceChunk | None:
    if not chunks:
        return None
    order = source_priority_policy.get("next_question", {})
    return min(chunks, key=lambda chunk: (order.get(chunk.source_type, 99), chunk.sequence))


def _question_source(*, index: int, chunk: ProgressEvidenceChunk) -> PolishQuestionSource:
    return PolishQuestionSource(
        index=index,
        source_type=chunk.source_type,
        title=chunk.title,
        excerpt=chunk.text,
        ref_id=chunk.chunk_id,
        availability="available",
    )


def _expected_answer_dimensions(blueprint: QuestionBlueprint) -> tuple[str, ...]:
    if blueprint.required_answer_materials:
        return blueprint.required_answer_materials
    return ("业务背景", "关键技术链路", "异常处理或取舍", "验证指标")


def _string_list(value: object, *, max_items: int | None = None) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned = [_clean(item) for item in value if _clean(item)]
    if max_items is None:
        return cleaned
    return cleaned[:max_items]


def _first_text(*values: object) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _clean(value: object) -> str:
    return str(value or "").strip()
