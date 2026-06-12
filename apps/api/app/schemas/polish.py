"""Polish API DTOs."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.shared.enums import AiTaskStatus, ScoreType
from app.schemas.refs import LowConfidenceFlagSchema, ResourceRef, TraceRefSchema, VersionRef


class PolishSubtopicResponse(BaseModel):
    subtopic_id: str
    topic_id: str
    title: str
    description: str | None = None
    disabled_reason: str | None = None


class PolishTopicResponse(BaseModel):
    topic_id: str
    title: str
    description: str | None = None
    requires_job_binding: bool
    disabled_reason: str | None = None
    subtopics: list[PolishSubtopicResponse] = Field(default_factory=list)


class PolishTopicRefResponse(BaseModel):
    topic_id: str
    title: str | None = None


class PolishSubtopicRefResponse(BaseModel):
    subtopic_id: str
    topic_id: str
    title: str | None = None


class CreatePolishSessionRequest(BaseModel):
    resume_job_binding_id: str = Field(min_length=1)
    topic_id: str | None = Field(default=None, min_length=1)
    subtopic_id: str | None = Field(default=None, min_length=1)
    custom_topic_text: str | None = Field(default=None, max_length=240)
    polish_theme: str | None = Field(default=None)


class PolishProgressTreeNodeResponse(BaseModel):
    progress_node_ref: str
    title: str
    expected_capability: str
    node_code: str | None = None
    category: str | None = None
    display_category_title: str | None = None
    display_title: str | None = None
    exam_point: str | None = None
    basis_type: str | None = None
    resume_signal: str | None = None
    jd_basis: str | None = None
    depth_goal: str | None = None
    preparation_goal: str | None = None
    first_question: str | None = None
    follow_up_focus: list[str] = Field(default_factory=list)
    common_loss_risks: list[str] = Field(default_factory=list)
    node_type: str | None = None
    interview_intent: str | None = None
    interview_method: str | None = None
    follow_up_method: str | None = None
    attack_style: str | None = None
    difficulty_level: str | None = None
    priority: int | None = None
    priority_reason: str | None = None
    related_job_requirements: list[str] = Field(default_factory=list)
    related_resume_evidence: list[str] = Field(default_factory=list)
    related_match_gaps: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    expected_answer_signals: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    recommended_first_question: str | None = None
    follow_up_directions: list[str] = Field(default_factory=list)
    evidence_chunk_ids: list[str] = Field(default_factory=list)
    evidence_bindings: list[dict[str, Any]] = Field(default_factory=list)
    grounding_status: str | None = None
    confidence_level: str | None = None
    low_confidence_flags: list[str] = Field(default_factory=list)
    children: list["PolishProgressTreeNodeResponse"] = Field(default_factory=list)


class PolishProgressTreePlanResponse(BaseModel):
    schema_id: str | None = None
    schema_version: str | None = None
    prompt_version: str | None = None
    status: str
    context_digest: str
    nodes: list[PolishProgressTreeNodeResponse] = Field(default_factory=list)
    failure_reason: str | None = None
    v2_metadata: dict[str, Any] | None = None


class PolishProgressTreeNodeStateResponse(BaseModel):
    progress_node_ref: str
    status: str
    completed_questions_count: int = 0
    latest_feedback_summary: str | None = None


class PolishCurrentPriorityResponse(BaseModel):
    progress_node_ref: str
    title: str
    expected_capability: str


class PolishProgressResponse(BaseModel):
    progress_percent: int = Field(ge=0, le=100)


class PolishProgressTreeStateResponse(BaseModel):
    schema_id: str | None = None
    schema_version: str | None = None
    prompt_version: str | None = None
    status: str
    node_states: list[PolishProgressTreeNodeStateResponse] = Field(default_factory=list)
    current_priority: PolishCurrentPriorityResponse | None = None
    updated_from_turns_count: int = 0
    progress: PolishProgressResponse = Field(default_factory=lambda: PolishProgressResponse(progress_percent=0))
    completed_focus_refs: list[dict[str, Any]] = Field(default_factory=list)
    summary: str | None = None
    failure_reason: str | None = None


class PolishContextHygieneMetadataResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    context_hygiene_status: str | None = None
    safe_context_metadata: dict[str, Any] = Field(default_factory=dict)
    fallback_reason: str | None = None
    validation_signals: dict[str, Any] = Field(default_factory=dict)


class PolishSessionContinuitySummaryResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    restored_turn_count: int = 0
    has_progress_plan: bool = False
    has_progress_state: bool = False
    progress_tree_status: str | None = None
    fallback_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)
    computed_at: str | None = None


class PolishSessionRestoredRefsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    current_question_id: str | None = None
    current_progress_node_ref: str | None = None
    evidence_refs: list[ResourceRef | str] = Field(default_factory=list)
    context_digest: str | None = None


class PolishSessionResponse(BaseModel):
    session_id: str
    mode: str = "polish"
    session_status: str
    resume_job_binding_id: str
    resume_id: str
    resume_version_id: str
    job_id: str
    job_version_id: str
    job_title: str
    job_company: str
    resume_title: str
    binding_label: str
    polish_theme: str
    polish_theme_label: str
    explicit_weight: int
    implicit_weight: int
    turns: list[PolishSessionTurnResponse] = Field(default_factory=list)
    progress_tree_status: str
    progress_percent: int = Field(ge=0, le=100)
    progress_tree_plan: PolishProgressTreePlanResponse
    progress_tree_state: PolishProgressTreeStateResponse
    topic_ref: PolishTopicRefResponse | None = None
    subtopic_ref: PolishSubtopicRefResponse | None = None
    custom_topic_text_summary: str | None = None
    current_question_ref: ResourceRef | None = None
    active_question_ref: ResourceRef | None = None
    progress_position_ref: ResourceRef | None = None
    current_node_ref: ResourceRef | None = None
    current_node_progress_node_ref: str | None = None
    active_question_refs: list[ResourceRef] = Field(default_factory=list)
    active_question_progress_node_ref: str | None = None
    active_question_evidence_refs: list[ResourceRef | str] = Field(default_factory=list)
    active_question_context_digest: str | None = None
    continuity_status: str | None = None
    continuity_summary: PolishSessionContinuitySummaryResponse | None = None
    restored_refs: PolishSessionRestoredRefsResponse | None = None
    report_id: str | None = None
    report_status: str | None = None
    report_generated_at: datetime | None = None
    low_confidence_flags: list[LowConfidenceFlagSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PolishSessionSummaryResponse(BaseModel):
    id: str
    session_id: str
    title: str
    mode: str = "polish"
    status: str
    resume_job_binding_id: str
    resume_id: str
    resume_version_id: str
    job_id: str
    job_version_id: str
    job_title: str
    job_company: str
    resume_title: str
    binding_label: str
    polish_theme: str
    polish_theme_label: str
    explicit_weight: int
    implicit_weight: int
    topic_id: str | None = None
    subtopic_id: str | None = None
    custom_topic_text_summary: str | None = None
    report_id: str | None = None
    report_status: str | None = None
    report_generated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


QUESTION_REF_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_:\-.]{0,127}$"
_QUESTION_REF_RE = re.compile(QUESTION_REF_PATTERN)
QUESTION_GENERATION_MODES = {"new_question", "follow_up", "regenerate_current_node"}
QUESTION_REQUEST_INJECTION_MARKERS = (
    "ignore previous",
    "ignore all previous",
    "system_prompt",
    "developer_prompt",
    "raw_prompt",
    "provider_payload",
    "prompt injection",
    "reveal prompt",
    "泄露",
    "忽略以上",
)


class CreateQuestionTaskRequest(BaseModel):
    progress_node_ref: str | None = Field(default=None, min_length=1, max_length=128, pattern=QUESTION_REF_PATTERN)
    generation_mode: str | None = Field(default=None, min_length=1, max_length=32)
    selected_primary_category_ref: str | None = Field(default=None, min_length=1, max_length=128, pattern=QUESTION_REF_PATTERN)
    selected_secondary_category_ref: str | None = Field(default=None, min_length=1, max_length=128, pattern=QUESTION_REF_PATTERN)
    selected_progress_node_ref: str | None = Field(default=None, min_length=1, max_length=128, pattern=QUESTION_REF_PATTERN)
    selected_category_path: list[str] = Field(default_factory=list, max_length=6)
    parent_question_id: str | None = Field(default=None, min_length=1, max_length=128, pattern=QUESTION_REF_PATTERN)
    parent_answer_id: str | None = Field(default=None, min_length=1, max_length=128, pattern=QUESTION_REF_PATTERN)
    parent_feedback_id: str | None = Field(default=None, min_length=1, max_length=128, pattern=QUESTION_REF_PATTERN)
    exclude_question_refs: list[str] = Field(default_factory=list, max_length=20)
    completed_focus_refs: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("selected_category_path")
    @classmethod
    def _validate_selected_category_path(cls, value: list[str]) -> list[str]:
        for item in value:
            if not isinstance(item, str) or not item.strip() or len(item.strip()) > 80:
                raise ValueError("selected_category_path entries must be non-empty and at most 80 chars")
            if _contains_question_request_injection_marker(item):
                raise ValueError("selected_category_path entries must not contain prompt injection markers")
        return value

    @field_validator("exclude_question_refs", "completed_focus_refs")
    @classmethod
    def _validate_ref_list(cls, value: list[str]) -> list[str]:
        for item in value:
            if not isinstance(item, str) or not _QUESTION_REF_RE.fullmatch(item.strip()):
                raise ValueError("ref entries must match the allowed ref pattern")
        return value

    @model_validator(mode="after")
    def _validate_generation_mode_combinations(self) -> "CreateQuestionTaskRequest":
        if self.generation_mode is not None and self.generation_mode not in QUESTION_GENERATION_MODES:
            raise ValueError("generation_mode must be new_question, follow_up or regenerate_current_node")
        if self.generation_mode == "new_question" and (
            self.parent_question_id is not None
            or self.parent_answer_id is not None
            or self.parent_feedback_id is not None
        ):
            raise ValueError("new_question mode must not include follow_up parent refs")
        return self


def _contains_question_request_injection_marker(value: str) -> bool:
    normalized = value.strip().lower()
    return any(marker in normalized for marker in QUESTION_REQUEST_INJECTION_MARKERS)


class CreateAnswerRequest(BaseModel):
    question_id: str = Field(min_length=1)
    answer_text: str
    base_question_version_ref: VersionRef | None = None


class PolishAnswerResponse(BaseModel):
    answer_id: str
    session_id: str
    question_id: str
    answer_round: int = Field(ge=1)
    answer_text: str
    created_at: datetime
    updated_at: datetime


class PolishFeedbackPayload(BaseModel):
    schema_id: str | None = None
    schema_version: str | None = None
    contract_ids: list[str] | None = None
    status: str | None = None
    feedback_id: str | None = None
    feedback_text: str | None = None
    answer_summary: str | None = None
    score_reasoning: str | None = None
    score_result: dict[str, Any] | None = None
    explicit_score: int | float | None = None
    implicit_score: int | float | None = None
    scoring_dimensions: list[dict[str, Any]] | None = None
    loss_points: list[dict[str, Any]] | None = None
    reference_answer: Any | None = None
    knowledge_points: list[str] | None = None
    technical_principles: list[str] | None = None
    asset_consistency_check: dict[str, Any] | None = None
    project_asset_consistency_check: dict[str, Any] | None = None
    answer_coverage: dict[str, Any] | None = None
    answer_change_analysis: dict[str, Any] | None = None
    feedback_cards: list[dict[str, Any]] | None = None
    next_recommended_actions: list[str] | None = None
    same_question_effect: dict[str, Any] | str | None = None
    session_similarity_check: dict[str, Any] | None = None
    project_asset_update_candidates: list[dict[str, Any]] | None = None
    evidence_refs: list[str] | None = None
    trace_refs: list[dict[str, Any]] | None = None
    low_confidence_flags: list[dict[str, Any]] | None = None
    answer_diagnosis: dict[str, Any] | None = None
    positive_evidence_points: list[dict[str, Any]] | None = None
    missing_answer_dimensions: list[dict[str, Any]] | None = None
    p7_reference_answer: str | None = None
    reference_answer_requirements: list[dict[str, Any]] | None = None
    oral_script: str | None = None
    oral_script_requirements: list[dict[str, Any]] | None = None
    mastery_status: str | None = None
    score_delta: int | None = None
    dimension_delta: dict[str, int] | None = None
    improved_points: list[str] | None = None
    remaining_gaps: list[str] | None = None
    repeated_loss_points: list[str] | None = None
    regressed_points: list[str] | None = None
    next_retry_focus: list[dict[str, Any]] | None = None
    polish_theme: str | None = None
    polish_theme_label: str | None = None
    explicit_weight: int | None = None
    implicit_weight: int | None = None
    weight_explanation: str | None = None
    interview_intent: str | None = None
    feedback_metadata: PolishContextHygieneMetadataResponse | None = None
    weakness_candidates: list[dict[str, Any]] | None = None
    asset_candidates: list[dict[str, Any]] | None = None
    oral_script_candidates: list[dict[str, Any]] | None = None
    polished_answer_candidates: list[dict[str, Any]] | None = None
    technical_gaps: list[str] | None = None
    communication_gaps: list[str] | None = None
    updated_reference_answer: str | None = None
    updated_oral_script: str | None = None


class PolishSessionAnswerResponse(BaseModel):
    answer_id: str
    answer_round: int = Field(ge=1)
    answer_text: str
    answer_created_at: datetime
    feedback_text: str
    feedback_id: str | None = None
    score_result_id: str | None = None
    feedback_created_at: datetime | None = None
    feedback_payload: PolishFeedbackPayload | None = None
    next_recommended_actions: list[str] = Field(default_factory=list)
    low_confidence_flags: list[dict[str, Any]] = Field(default_factory=list)
    trace_refs: list[dict[str, Any]] = Field(default_factory=list)


class PolishQuestionSourceResponse(BaseModel):
    index: int = Field(ge=1)
    source_type: str
    title: str
    excerpt: str
    ref_id: str | None = None
    availability: str


class PolishSessionTurnResponse(BaseModel):
    question_id: str
    question_text: str
    question_sources: list[PolishQuestionSourceResponse] = Field(default_factory=list)
    question_created_at: datetime
    question_metadata: PolishContextHygieneMetadataResponse | None = None
    answers: list[PolishSessionAnswerResponse] = Field(default_factory=list)


class CreateFeedbackTaskRequest(BaseModel):
    answer_id: str = Field(min_length=1)
    scoring_context: dict[str, Any] | None = None


class PolishTaskStatusResponse(BaseModel):
    ai_task_id: str
    task_type: str
    status: AiTaskStatus
    contract_ids: list[str] = Field(default_factory=list)
    retryable: bool = False
    result_ref: TraceRefSchema | None = None
    user_visible_status: str
    score_type: ScoreType | None = None
    candidate_refs: list[ResourceRef] = Field(default_factory=list)
    suggestion_refs: list[ResourceRef] = Field(default_factory=list)
    active_question_refs: list[ResourceRef] = Field(default_factory=list)
    active_question_progress_node_ref: str | None = None
    active_question_evidence_refs: list[ResourceRef] = Field(default_factory=list)
    active_question_context_digest: str | None = None
    validation_errors: list[str] = Field(default_factory=list)
    feedback_id: str | None = None
    feedback_status: str | None = None
    session_id: str | None = None
    question_id: str | None = None
    answer_id: str | None = None
    answer_round: int | None = Field(default=None, ge=1)
    feedback_text: str | None = None
    feedback_created_at: datetime | None = None
    score_result_id: str | None = None
    score_result: dict[str, Any] | None = None
    feedback_payload: PolishFeedbackPayload | None = None
    next_recommended_actions: list[str] = Field(default_factory=list)
    low_confidence_flags: list[dict[str, Any]] = Field(default_factory=list)
    trace_refs: list[dict[str, Any]] = Field(default_factory=list)
