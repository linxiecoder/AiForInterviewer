"""Application entities for polish core workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.shared.enums import AiTaskStatus, ScoreType
from app.domain.shared.refs import ResourceRef, TraceRef


@dataclass(frozen=True)
class PolishSubtopic:
    subtopic_id: str
    topic_id: str
    title: str
    description: str | None = None
    disabled_reason: str | None = None


@dataclass(frozen=True)
class PolishTopic:
    topic_id: str
    title: str
    description: str | None
    requires_job_binding: bool
    disabled_reason: str | None = None
    subtopics: tuple[PolishSubtopic, ...] = ()


@dataclass(frozen=True)
class PolishSession:
    session_id: str
    owner_id: str
    actor_id: str
    binding_id: str
    resume_id: str
    resume_version_id: str
    job_id: str
    job_version_id: str
    status: str
    topic_id: str | None
    subtopic_id: str | None
    custom_topic_text_summary: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PolishQuestion:
    question_id: str
    owner_id: str
    actor_id: str
    session_id: str
    ai_task_id: str
    question_text: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PolishAnswer:
    answer_id: str
    owner_id: str
    actor_id: str
    session_id: str
    question_id: str
    answer_round: int
    answer_text: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PolishFeedback:
    feedback_id: str
    owner_id: str
    actor_id: str
    session_id: str
    answer_id: str
    ai_task_id: str
    score_result_id: str | None
    feedback_summary: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PolishTaskStatus:
    ai_task_id: str
    task_type: str
    status: AiTaskStatus
    contract_ids: tuple[str, ...]
    retryable: bool
    result_ref: TraceRef
    user_visible_status: str
    score_type: ScoreType | None = None
    candidate_refs: tuple[ResourceRef, ...] = field(default_factory=tuple)
    suggestion_refs: tuple[ResourceRef, ...] = field(default_factory=tuple)
