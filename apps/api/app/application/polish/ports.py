"""Polish ports and cross-layer persistence contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from app.domain.shared.enums import AiTaskStatus, ScoreType
from app.domain.shared.refs import ResourceRef
from app.domain.shared.refs import TraceRef


class PolishSessionVersionConflictError(RuntimeError):
    def __init__(self, *, base_record_version: int, current_record_version: int) -> None:
        super().__init__("stale_version_conflict")
        self.base_record_version = base_record_version
        self.current_record_version = current_record_version


@dataclass(frozen=True)
class AuthorityDecisionResult:
    allowed: bool
    decision_ref: str
    execution_target: str | None = None
    control_reason_codes: tuple[str, ...] = ()
    policy_reason_codes: tuple[str, ...] = ()
    rejection_reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


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
class PolishSessionReportSummary:
    report_id: str
    report_status: str
    report_generated_at: datetime | None = None


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
    record_version: int = 1
    polish_theme: str | None = None
    progress_tree_status: str = "insufficient_context"
    progress_percent: int = 0
    progress_tree_plan: dict[str, Any] = field(default_factory=dict)
    progress_tree_state: dict[str, Any] = field(default_factory=dict)
    report_summary: PolishSessionReportSummary | None = None


@dataclass(frozen=True)
class PolishQuestionSource:
    index: int
    source_type: str
    title: str
    excerpt: str
    ref_id: str | None
    availability: str


@dataclass(frozen=True)
class PolishQuestionDraft:
    question_text: str
    question_sources: tuple[PolishQuestionSource, ...] = ()
    progress_node_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    context_digest: str | None = None
    question_pattern: str | None = None
    quality_score: int | None = None
    confidence_level: str | None = None
    low_confidence_flags: tuple[str, ...] = ()
    expected_answer_dimensions: tuple[str, ...] = ()
    question_metadata: dict[str, Any] = field(default_factory=dict)
    evidence_signal_refs: tuple[str, ...] = ()
    builder_version: str | None = None
    validator_version: str | None = None


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
    question_sources: tuple[PolishQuestionSource, ...] = ()
    progress_node_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    context_digest: str | None = None
    question_metadata: dict[str, Any] = field(default_factory=dict)


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
    idempotency_key: str | None = None
    request_body_hash: str | None = None


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
class PolishSessionAnswerDetail:
    answer_id: str
    answer_round: int
    answer_text: str
    answer_created_at: datetime
    feedback_text: str | None
    feedback_id: str | None
    score_result_id: str | None
    feedback_created_at: datetime | None
    feedback_payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class PolishSessionTurn:
    question_id: str
    question_text: str
    question_created_at: datetime
    question_sources: tuple[PolishQuestionSource, ...] = ()
    progress_node_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    context_digest: str | None = None
    question_metadata: dict[str, Any] = field(default_factory=dict)
    answers: tuple[PolishSessionAnswerDetail, ...] = ()


@dataclass(frozen=True)
class PolishSessionDetail:
    session: PolishSession
    job_title: str | None
    job_company: str | None
    resume_title: str | None
    binding_label: str | None
    turns: tuple[PolishSessionTurn, ...]
    progress_tree_status: str = "insufficient_context"
    progress_percent: int = 0
    progress_context: dict[str, Any] = field(default_factory=dict)
    progress_tree_plan: dict[str, Any] = field(default_factory=dict)
    progress_tree_state: dict[str, Any] = field(default_factory=dict)


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
    validation_errors: tuple[str, ...] = field(default_factory=tuple)
    safe_summary: dict[str, Any] | None = None


class PolishRepository(Protocol):
    def add_session(self, session: PolishSession) -> None: ...

    def update_progress_tree(self, session: PolishSession) -> None: ...

    def save_session_status(self, session: PolishSession) -> None: ...

    def create_session_report(
        self,
        *,
        owner_id: str,
        actor_id: str,
        session_id: str,
        report_id: str,
    ) -> PolishSession: ...

    def list_sessions(self, owner_id: str) -> tuple[PolishSession, ...]: ...

    def get_session(self, owner_id: str, session_id: str) -> PolishSession | None: ...

    def list_questions_for_session(self, owner_id: str, session_id: str) -> tuple[PolishQuestion, ...]: ...

    def add_question(self, question: PolishQuestion) -> None: ...

    def add_question_once(
        self,
        *,
        owner_id: str,
        session_id: str,
        graph_persistence_idempotency_key: str,
        question: PolishQuestion,
    ) -> tuple[PolishQuestion, bool]: ...

    def get_question(self, owner_id: str, question_id: str) -> PolishQuestion | None: ...

    def add_answer(self, answer: PolishAnswer) -> None: ...

    def add_answer_once(
        self,
        *,
        answer: PolishAnswer,
        idempotency_key: str | None,
        request_body_hash: str | None,
    ) -> PolishAnswer: ...

    def get_answer(self, owner_id: str, answer_id: str) -> PolishAnswer | None: ...

    def list_answers_for_session(self, owner_id: str, session_id: str) -> tuple[PolishAnswer, ...]: ...

    def count_answers_for_question(self, owner_id: str, question_id: str) -> int: ...

    def add_feedback(self, feedback: PolishFeedback) -> None: ...

    def get_latest_feedback_for_answer(
        self,
        *,
        owner_id: str,
        answer_id: str,
        status: str | None = None,
    ) -> PolishFeedback | None: ...

    def list_feedbacks_for_session(self, owner_id: str, session_id: str) -> tuple[PolishFeedback, ...]: ...

    def add_task(self, task: PolishTaskStatus, *, owner_id: str, actor_id: str, target_ref_id: str) -> None: ...

    def get_ref(self, session_id: str) -> ResourceRef | None: ...
