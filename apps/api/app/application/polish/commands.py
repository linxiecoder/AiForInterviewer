"""Polish commands."""

from dataclasses import dataclass

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
class CreatePolishQuestionTaskCommand:
    owner_id: str
    actor_id: str
    session_id: str
    progress_node_ref: str | None = None


@dataclass(frozen=True)
class CreatePolishAnswerCommand:
    owner_id: str
    actor_id: str
    session_id: str
    question_id: str
    answer_text: str
    base_question_version_ref: VersionRef | None = None


@dataclass(frozen=True)
class CreatePolishFeedbackTaskCommand:
    owner_id: str
    actor_id: str
    session_id: str
    answer_id: str


@dataclass(frozen=True)
class RefreshPolishProgressTreeStateCommand:
    owner_id: str
    actor_id: str
    session_id: str
