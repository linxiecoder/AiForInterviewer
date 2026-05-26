"""Phase 1 Polish question generation service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.application.polish.entities import PolishQuestionDraft, PolishQuestionSource, PolishSession
from app.application.polish.progress_evidence import ProgressEvidenceChunk, select_progress_tree_evidence_chunks
from app.application.polish.question_blueprint import EvidenceScope, QuestionBlueprint, build_question_blueprint
from app.application.polish.question_generation_prompts import (
    build_question_prompt_asset,
    build_question_prompt_metadata,
    render_blueprint_question,
)
from app.application.polish.question_grounding import GroundingResult, validate_question_grounding


QUESTION_GENERATION_SERVICE_VERSION = "polish_question_generation.phase1"


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
        surface_question_builder: Callable[[QuestionBlueprint, EvidenceScope], str] | None = None,
    ) -> None:
        self._surface_question_builder = surface_question_builder or render_blueprint_question

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
        )
        blueprint = build_question_blueprint(scope)
        prompt_asset = build_question_prompt_asset(blueprint, scope)
        prompt_metadata = build_question_prompt_metadata(prompt_asset)
        question_text = self._surface_question_builder(blueprint, scope)
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
                "validator_version": "polish_question_grounding.phase1",
                "signal_version": "phase1_blueprint_only",
                "source_availability": "available" if blueprint.evidence_refs else "partial",
                "generation_service": QUESTION_GENERATION_SERVICE_VERSION,
                "blueprint_version": blueprint.metadata.get("blueprint_version"),
                **prompt_metadata,
                "llm_generation_mode": "deterministic_fallback",
                "fallback_reason": "local_blueprint_renderer",
                "fallback_visible": True,
                "question_kind": blueprint.question_kind,
                "claim_mode": blueprint.claim_mode,
                "primary_evidence_ref": blueprint.primary_evidence_ref,
                "primary_source_type": scope.primary_source_type,
                "grounding_status": "passed",
                "validation_errors": [],
            },
            builder_version=QUESTION_GENERATION_SERVICE_VERSION,
            validator_version="polish_question_grounding.phase1",
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
) -> EvidenceScope:
    selection = select_progress_tree_evidence_chunks(
        context,
        purpose="next_question",
        max_chunks=4,
        max_chars=1800,
        existing_plan=plan,
        existing_state=state,
        progress_node_ref=requested_ref,
    )
    chunks = tuple(chunk for chunk in selection.selected_chunks if _clean(chunk.text))
    primary = _primary_chunk(chunks)
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


def _primary_chunk(chunks: tuple[ProgressEvidenceChunk, ...]) -> ProgressEvidenceChunk | None:
    for source_type in (
        "resume_project",
        "resume_work_experience",
        "resume_skill",
        "job_requirement",
        "match_gap",
        "match_focus",
    ):
        for chunk in chunks:
            if chunk.source_type == source_type:
                return chunk
    return chunks[0] if chunks else None


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


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_clean(item) for item in value if _clean(item)]


def _first_text(*values: object) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _clean(value: object) -> str:
    return str(value or "").strip()
