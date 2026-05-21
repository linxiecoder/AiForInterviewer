"""Structured contract objects for polish feedback consistency checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


FEEDBACK_SCHEMA_ID = "polish_feedback_payload_v1"
FEEDBACK_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class FeedbackInput:
    owner_id: str
    actor_id: str
    session_id: str
    question_id: str
    answer_id: str
    answer_round: int
    question_text: str
    question_metadata: dict[str, Any]
    question_pattern: str
    expected_answer_dimensions: tuple[str, ...]
    interview_intent: str
    question_sources: tuple[dict[str, Any], ...]
    evidence_refs: tuple[dict[str, Any], ...]
    answer_text: str
    polish_theme: str
    source_availability: str
    low_confidence_flags: tuple[dict[str, Any], ...]
    feedback_generation_mode: str

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RetryFeedbackInput(FeedbackInput):
    previous_answer_rounds: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    previous_feedbacks: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    previous_score_results: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    previous_dimension_scores: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    previous_loss_points: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    previous_reference_answer: str = ""
    previous_oral_script: str = ""
    repeated_gaps: tuple[str, ...] = field(default_factory=tuple)
    fixed_gaps: tuple[str, ...] = field(default_factory=tuple)
    regression_signals: tuple[str, ...] = field(default_factory=tuple)
    mastery_threshold: str = ""


@dataclass(frozen=True)
class AnswerDiagnosis:
    strengths: tuple[str, ...] = field(default_factory=tuple)
    weaknesses: tuple[str, ...] = field(default_factory=tuple)
    risks: tuple[str, ...] = field(default_factory=tuple)
    recommendations: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ScoringDimension:
    dimension_id: str
    score_value: int
    max_score: int
    weight: float = 1.0
    is_critical: bool = False
    rationale: str | None = None


@dataclass(frozen=True)
class PositiveEvidencePoint:
    point_id: str
    title: str
    evidence_excerpt: str
    dimension_id: str | None = None
    related_dimension: str | None = None
    evidence_source: str | None = None
    location: str = "both"


@dataclass(frozen=True)
class FeedbackLossPoint:
    loss_point_id: str
    title: str
    deducted_points: int
    reason: str
    critical: bool = False
    dimension_id: str | None = None
    related_answer_ref: dict[str, Any] | None = None
    required_reference_terms: tuple[str, ...] = field(default_factory=tuple)
    required_oral_terms: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MissingAnswerDimension:
    dimension: str
    reason: str
    impact_scope: str | None = None


@dataclass(frozen=True)
class ReferenceAnswerRequirement:
    requirement_id: str
    requirement: str
    required_coverage_terms: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OralScriptRequirement:
    requirement_id: str
    requirement: str
    required_coverage_terms: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RetryFocus:
    focus_area: str
    priority: int = 1
    related_dimension: str | None = None


@dataclass(frozen=True)
class AnswerDelta:
    score_delta: int = 0
    dimension_delta: dict[str, int] = field(default_factory=dict)
    improved_points: tuple[str, ...] = field(default_factory=tuple)
    remaining_gaps: tuple[str, ...] = field(default_factory=tuple)
    repeated_loss_points: tuple[str, ...] = field(default_factory=tuple)
    regressed_points: tuple[str, ...] = field(default_factory=tuple)
    mastery_status: str | None = None
    should_continue_same_question: bool = False
    should_generate_next_question: bool = False
    next_retry_focus: tuple[RetryFocus, ...] = field(default_factory=tuple)
    updated_reference_answer: str | None = None
    updated_oral_script: str | None = None


@dataclass(frozen=True)
class StructuredFeedbackPayload:
    schema_id: str
    schema_version: str
    status: str
    feedback_id: str
    feedback_text: str
    feedback_summary: str
    answer_diagnosis: dict[str, Any]
    scoring_dimensions: tuple[ScoringDimension, ...]
    score_result: dict[str, Any]
    positive_evidence_points: tuple[PositiveEvidencePoint, ...]
    loss_points: tuple[FeedbackLossPoint, ...]
    missing_answer_dimensions: tuple[MissingAnswerDimension, ...]
    interview_intent: str | None
    p7_reference_answer: str
    reference_answer_requirements: tuple[ReferenceAnswerRequirement, ...]
    oral_script: str
    oral_script_requirements: tuple[OralScriptRequirement, ...]
    knowledge_points: tuple[dict[str, Any], ...]
    technical_principles: tuple[dict[str, Any], ...]
    technical_gaps: tuple[str, ...]
    communication_gaps: tuple[str, ...]
    next_recommended_actions: tuple[str, ...]
    weakness_candidates: tuple[dict[str, Any], ...]
    asset_candidates: tuple[dict[str, Any], ...]
    validation_result_ref: dict[str, Any] | None
    trace_refs: tuple[dict[str, Any], ...]
    low_confidence_flags: tuple[dict[str, Any], ...]
    feedback_metadata: dict[str, Any]

    score_delta: int = 0
    dimension_delta: dict[str, int] = field(default_factory=dict)
    improved_points: tuple[str, ...] = field(default_factory=tuple)
    remaining_gaps: tuple[str, ...] = field(default_factory=tuple)
    repeated_loss_points: tuple[str, ...] = field(default_factory=tuple)
    regressed_points: tuple[str, ...] = field(default_factory=tuple)
    mastery_status: str | None = None
    should_continue_same_question: bool = False
    should_generate_next_question: bool = False
    next_retry_focus: tuple[RetryFocus, ...] = field(default_factory=tuple)
    updated_reference_answer: str | None = None
    updated_oral_script: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)
