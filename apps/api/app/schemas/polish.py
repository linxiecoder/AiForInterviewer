"""Polish API DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

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


class PolishProgressTreeNodeResponse(BaseModel):
    progress_node_ref: str
    title: str
    expected_capability: str
    related_job_requirements: list[str] = Field(default_factory=list)
    related_resume_evidence: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    children: list["PolishProgressTreeNodeResponse"] = Field(default_factory=list)


class PolishProgressTreePlanResponse(BaseModel):
    schema_id: str | None = None
    schema_version: str | None = None
    prompt_version: str | None = None
    status: str
    context_digest: str
    nodes: list[PolishProgressTreeNodeResponse] = Field(default_factory=list)
    failure_reason: str | None = None


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
    summary: str | None = None
    failure_reason: str | None = None


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
    turns: list[PolishSessionTurnResponse] = Field(default_factory=list)
    progress_tree_status: str
    progress_percent: int = Field(ge=0, le=100)
    progress_tree_plan: PolishProgressTreePlanResponse
    progress_tree_state: PolishProgressTreeStateResponse
    topic_ref: PolishTopicRefResponse | None = None
    subtopic_ref: PolishSubtopicRefResponse | None = None
    custom_topic_text_summary: str | None = None
    current_question_ref: ResourceRef | None = None
    progress_position_ref: ResourceRef | None = None
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
    topic_id: str | None = None
    subtopic_id: str | None = None
    custom_topic_text_summary: str | None = None
    created_at: datetime
    updated_at: datetime


class CreateQuestionTaskRequest(BaseModel):
    progress_node_ref: str | None = Field(default=None, min_length=1)


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


class PolishSessionAnswerResponse(BaseModel):
    answer_id: str
    answer_round: int = Field(ge=1)
    answer_text: str
    answer_created_at: datetime
    feedback_text: str
    feedback_id: str | None = None
    score_result_id: str | None = None
    feedback_created_at: datetime | None = None


class PolishSessionTurnResponse(BaseModel):
    question_id: str
    question_text: str
    question_created_at: datetime
    answers: list[PolishSessionAnswerResponse] = Field(default_factory=list)


class CreateFeedbackTaskRequest(BaseModel):
    answer_id: str = Field(min_length=1)


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
