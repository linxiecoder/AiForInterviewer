from __future__ import annotations

from datetime import UTC, datetime

from app.application.common.result import ApplicationResult
from app.application.polish.commands import CreatePolishFeedbackTaskCommand
from app.application.polish.entities import PolishAnswer, PolishFeedback, PolishTaskStatus
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.refs import TraceRef


def test_fetch_candidate_use_case_reads_candidate_from_repository_only() -> None:
    from app.usecases.polish import FetchPolishCandidateQuery, PolishFetchCandidateUseCase

    class RepositorySpy:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, str]] = []

        def get_candidate(self, *, owner_id: str, candidate_id: str):
            self.calls.append(("get_candidate", owner_id, candidate_id))
            return {
                "candidate_id": candidate_id,
                "owner_id": owner_id,
                "candidate_type": "weakness_candidate",
                "status": "candidate",
            }

    repository = RepositorySpy()
    result = PolishFetchCandidateUseCase(repository).execute(
        FetchPolishCandidateQuery(owner_id="owner-1", candidate_id="cand-1")
    )

    assert result.is_success
    assert result.value is not None
    assert result.value["candidate_id"] == "cand-1"
    assert repository.calls == [("get_candidate", "owner-1", "cand-1")]


def test_fetch_candidate_use_case_returns_not_found_for_missing_candidate() -> None:
    from app.usecases.polish import FetchPolishCandidateQuery, PolishFetchCandidateUseCase

    class RepositoryStub:
        def get_candidate(self, *, owner_id: str, candidate_id: str):
            return None

    result = PolishFetchCandidateUseCase(RepositoryStub()).execute(
        FetchPolishCandidateQuery(owner_id="owner-1", candidate_id="missing-candidate")
    )

    assert not result.is_success
    assert result.error is not None
    assert result.error.code == "not_found_or_inaccessible"
    assert result.error.message == "Polish candidate not found"


def test_apply_feedback_use_case_validates_answer_and_passes_internal_scoring_context() -> None:
    from app.usecases.polish import PolishApplyFeedbackUseCase

    answer = PolishAnswer(
        answer_id="answer-1",
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        question_id="question-1",
        answer_round=1,
        answer_text="我会用幂等 key 保护提交。",
        status="saved",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    expected_task = PolishTaskStatus(
        ai_task_id="task-1",
        task_type="polish_feedback_generation",
        status=AiTaskStatus.SUCCEEDED,
        contract_ids=("P-POLISH-005",),
        retryable=False,
        result_ref=TraceRef(trace_ref_id="feedback-1", trace_type="feedback", created_at=datetime.now(UTC)),
        user_visible_status="反馈已生成",
    )

    class RepositorySpy:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, str]] = []

        def get_answer(self, owner_id: str, answer_id: str) -> PolishAnswer | None:
            self.calls.append(("get_answer", owner_id, answer_id))
            return answer

    class FeedbackServiceSpy:
        def __init__(self) -> None:
            self.command: CreatePolishFeedbackTaskCommand | None = None

        def create_feedback_task(self, command: CreatePolishFeedbackTaskCommand):
            self.command = command
            return ApplicationResult(value=expected_task)

    repository = RepositorySpy()
    feedback_service = FeedbackServiceSpy()
    command = CreatePolishFeedbackTaskCommand(
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        answer_id="answer-1",
    )
    object.__setattr__(command, "internal_scoring_context", {"rubric_version": "m3-local"})

    result = PolishApplyFeedbackUseCase(repository, feedback_service).execute(command)

    assert result.value == expected_task
    assert repository.calls == [("get_answer", "owner-1", "answer-1")]
    assert feedback_service.command is command
    assert getattr(feedback_service.command, "internal_scoring_context") == {"rubric_version": "m3-local"}


def test_persist_result_use_case_persists_feedback_before_task() -> None:
    from app.usecases.polish import PersistPolishResultCommand, PolishPersistResultUseCase

    now = datetime.now(UTC)
    feedback = PolishFeedback(
        feedback_id="feedback-1",
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        answer_id="answer-1",
        ai_task_id="task-1",
        score_result_id=None,
        feedback_summary='{"feedback_text":"ok"}',
        status="generated",
        created_at=now,
        updated_at=now,
    )
    task = PolishTaskStatus(
        ai_task_id="task-1",
        task_type="polish_feedback_generation",
        status=AiTaskStatus.SUCCEEDED,
        contract_ids=("P-POLISH-005",),
        retryable=False,
        result_ref=TraceRef(trace_ref_id="feedback-1", trace_type="feedback", created_at=now),
        user_visible_status="反馈已生成",
    )

    class RepositorySpy:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        def add_feedback(self, saved_feedback: PolishFeedback) -> None:
            self.calls.append(("add_feedback", saved_feedback))

        def add_task(self, saved_task: PolishTaskStatus, *, owner_id: str, actor_id: str, target_ref_id: str) -> None:
            self.calls.append(("add_task", (saved_task, owner_id, actor_id, target_ref_id)))

    repository = RepositorySpy()
    result = PolishPersistResultUseCase(repository).execute(
        PersistPolishResultCommand(
            feedback=feedback,
            task=task,
            owner_id="owner-1",
            actor_id="actor-1",
            target_ref_id="answer-1",
        )
    )

    assert result.value == task
    assert repository.calls == [
        ("add_feedback", feedback),
        ("add_task", (task, "owner-1", "actor-1", "answer-1")),
    ]
