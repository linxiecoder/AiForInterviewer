"""Polish commands."""

from dataclasses import dataclass
from typing import Any

from app.application.polish.next_question_authorization import (
    NextQuestionExecutionGrant,
    NextQuestionExecutionGrantSnapshot,
)
from app.domain.shared.refs import VersionRef


@dataclass(frozen=True)
class CreatePolishSessionCommand:
    owner_id: str
    actor_id: str
    resume_job_binding_id: str
    topic_id: str | None = None
    subtopic_id: str | None = None
    custom_topic_text: str | None = None
    polish_theme: str | None = None


@dataclass(frozen=True)
class GenerateInitialPolishProgressTreeCommand:
    owner_id: str
    actor_id: str
    session_id: str


@dataclass(frozen=True)
class CreatePolishQuestionTaskCommand:
    owner_id: str
    actor_id: str
    session_id: str
    progress_node_ref: str | None = None
    generation_mode: str | None = None
    selected_primary_category_ref: str | None = None
    selected_secondary_category_ref: str | None = None
    selected_progress_node_ref: str | None = None
    selected_category_path: tuple[str, ...] = ()
    parent_question_id: str | None = None
    parent_answer_id: str | None = None
    parent_feedback_id: str | None = None
    exclude_question_refs: tuple[str, ...] = ()
    completed_focus_refs: tuple[str, ...] = ()
    execution_source: str = "direct_question_endpoint"
    authorized_feedback_id: str | None = None
    authorized_answer_id: str | None = None
    authorized_parent_question_id: str | None = None
    next_question_execution_grant: NextQuestionExecutionGrant | None = None
    next_question_execution_grant_snapshot: NextQuestionExecutionGrantSnapshot | dict[str, Any] | None = None


@dataclass(frozen=True)
class CompletePolishQuestionCommand:
    owner_id: str
    actor_id: str
    session_id: str
    question_id: str


@dataclass(frozen=True)
class EndPolishSessionCommand:
    owner_id: str
    actor_id: str
    session_id: str


@dataclass(frozen=True)
class GeneratePolishSessionReportCommand:
    owner_id: str
    actor_id: str
    session_id: str


@dataclass(frozen=True)
class SoftDeletePolishSessionCommand:
    owner_id: str
    actor_id: str
    session_id: str


@dataclass(frozen=True)
class CreatePolishAnswerCommand:
    owner_id: str
    actor_id: str
    session_id: str
    question_id: str
    answer_text: str
    base_question_version_ref: VersionRef | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True)
class CreatePolishFeedbackTaskCommand:
    owner_id: str
    actor_id: str
    session_id: str
    answer_id: str
    internal_scoring_context: dict[str, Any] | None = None


@dataclass(frozen=True)
class RefreshPolishProgressTreeStateCommand:
    owner_id: str
    actor_id: str
    session_id: str
