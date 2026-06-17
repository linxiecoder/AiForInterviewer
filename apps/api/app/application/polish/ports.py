"""Polish ports."""

from typing import Protocol

from app.application.polish.entities import (
    PolishAnswer,
    PolishFeedback,
    PolishQuestion,
    PolishSession,
    PolishTaskStatus,
)
from app.domain.shared.refs import ResourceRef


class PolishSessionVersionConflictError(RuntimeError):
    def __init__(self, *, base_record_version: int, current_record_version: int) -> None:
        super().__init__("stale_version_conflict")
        self.base_record_version = base_record_version
        self.current_record_version = current_record_version


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
