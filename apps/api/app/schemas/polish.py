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


class PolishSessionResponse(BaseModel):
    session_id: str
    mode: str = "polish"
    session_status: str
    resume_job_binding_id: str
    resume_id: str
    resume_version_id: str
    job_id: str
    job_version_id: str
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
