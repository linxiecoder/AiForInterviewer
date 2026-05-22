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


class PolishRepository(Protocol):
    def add_session(self, session: PolishSession) -> None: ...

    def update_progress_tree(self, session: PolishSession) -> None: ...

    def list_sessions(self, owner_id: str) -> tuple[PolishSession, ...]: ...

    def get_session(self, owner_id: str, session_id: str) -> PolishSession | None: ...

    def list_questions_for_session(self, owner_id: str, session_id: str) -> tuple[PolishQuestion, ...]: ...

    def add_question(self, question: PolishQuestion) -> None: ...

    def get_question(self, owner_id: str, question_id: str) -> PolishQuestion | None: ...

    def add_answer(self, answer: PolishAnswer) -> None: ...

    def get_answer(self, owner_id: str, answer_id: str) -> PolishAnswer | None: ...

    def list_answers_for_session(self, owner_id: str, session_id: str) -> tuple[PolishAnswer, ...]: ...

    def count_answers_for_question(self, owner_id: str, question_id: str) -> int: ...

    def add_feedback(self, feedback: PolishFeedback) -> None: ...

    def list_feedbacks_for_session(self, owner_id: str, session_id: str) -> tuple[PolishFeedback, ...]: ...

    def add_task(self, task: PolishTaskStatus, *, owner_id: str, actor_id: str, target_ref_id: str) -> None: ...

    def get_ref(self, session_id: str) -> ResourceRef | None: ...


class PolishCandidateRepository(Protocol):
    def upsert_from_feedback_payload(self, owner_id: str, feedback_payload: dict) -> tuple[dict, ...]: ...

    def list_candidates(
        self,
        *,
        owner_id: str,
        status: str | None = None,
        candidate_type: str | None = None,
        session_id: str | None = None,
        source_type: str | None = None,
        confidence_level: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[dict, ...]: ...

    def get_candidate(self, *, owner_id: str, candidate_id: str) -> dict | None: ...
