"""Regression tests for the Polish application service module split."""

from __future__ import annotations

import importlib
import inspect
from dataclasses import fields, replace
from datetime import UTC, datetime
from types import SimpleNamespace


SERVICE_MODULES = (
    ("session_application_service", "PolishSessionApplicationService"),
    ("question_application_service", "PolishQuestionApplicationService"),
    ("answer_application_service", "PolishAnswerApplicationService"),
    ("feedback_application_service", "PolishFeedbackApplicationService"),
    ("progress_application_service", "PolishProgressApplicationService"),
    ("report_application_service", "PolishReportApplicationService"),
)
FORBIDDEN_FOCUSED_SERVICE_IMPORT_SNIPPETS = (
    "app.application.polish.question_generation_prompts",
    "app.application.polish.feedback_prompt_assets",
    "app.application.polish.question_grounding",
    "app.application.polish.feedback_rules",
    "app.application.agents",
    "app.application.ai_runtime",
    "app.infrastructure",
    "app.api.v1",
    "fastapi",
    "sqlalchemy",
    "langgraph",
    "openai",
)
FEEDBACK_GENERATION_HELPERS_OWNED_BY_SERVICE = (
    "_feedback_generation_lock",
    "_existing_generated_feedback_task",
    "_has_generated_feedback_payload",
    "_build_feedback_generation_context",
    "_generated_feedback_payload_for_storage",
    "_failed_feedback_payload_for_storage",
    "_feedback_candidate_refs_from_payload",
    "_canonical_project_asset_items",
    "_feedback_question_sources",
    "_feedback_same_question_answers",
    "_feedback_recent_turns",
    "_feedback_job_snapshot",
    "_feedback_resume_snapshot",
    "_feedback_context_excerpt",
    "_feedback_progress_node_snapshot",
    "_feedback_progress_node_ref",
    "_iter_progress_nodes",
    "_clean_feedback_list",
    "_build_same_question_effect",
)


def test_polish_application_services_live_in_focused_modules() -> None:
    for module_name, class_name in SERVICE_MODULES:
        module = importlib.import_module(f"app.application.polish.{module_name}")
        service_cls = getattr(module, class_name)

        assert service_cls.__module__ == f"app.application.polish.{module_name}"


def test_focused_service_modules_do_not_import_use_cases_facade() -> None:
    for module_name, _class_name in SERVICE_MODULES:
        module = importlib.import_module(f"app.application.polish.{module_name}")
        source = inspect.getsource(module)

        assert "PolishUseCases" not in source
        assert "app.application.polish.use_cases" not in source
        assert ".use_cases" not in source


def test_use_cases_does_not_define_feedback_generation_helpers() -> None:
    use_cases = importlib.import_module("app.application.polish.use_cases")
    source = inspect.getsource(use_cases)

    for helper_name in FEEDBACK_GENERATION_HELPERS_OWNED_BY_SERVICE:
        assert f"def {helper_name}" not in source


def test_feedback_generation_storage_path_does_not_call_legacy_payload_cleaner() -> None:
    feedback_service = importlib.import_module("app.application.polish.feedback_application_service")
    source = inspect.getsource(feedback_service._generated_feedback_payload_for_storage)

    assert "_remove_legacy_feedback_payload_fields" not in source


def test_generated_feedback_storage_payload_keeps_next_actions_allowlisted() -> None:
    feedback_service = importlib.import_module("app.application.polish.feedback_application_service")
    feedback_rules = importlib.import_module("app.application.polish.feedback_rules")
    allowed_actions = feedback_rules.ALLOWED_FEEDBACK_RECOMMENDED_ACTIONS

    stored = feedback_service._generated_feedback_payload_for_storage(
        {
            "next_recommended_actions": ["continue_same_question"],
            "feedback_metadata": {"provider_status": "unit_test"},
        },
        session_id="session-1",
        question_id="question-1",
        answer_id="answer-1",
        feedback_id="feedback-1",
    )

    assert set(stored["next_recommended_actions"]) <= allowed_actions


def test_focused_service_modules_do_not_import_prompt_provider_db_api_or_runtime_paths() -> None:
    for module_name, _class_name in SERVICE_MODULES:
        module = importlib.import_module(f"app.application.polish.{module_name}")
        source = inspect.getsource(module)

        for forbidden_snippet in FORBIDDEN_FOCUSED_SERVICE_IMPORT_SNIPPETS:
            assert forbidden_snippet not in source


def test_use_cases_reexports_split_service_classes_for_existing_imports() -> None:
    use_cases = importlib.import_module("app.application.polish.use_cases")

    for module_name, class_name in SERVICE_MODULES:
        module = importlib.import_module(f"app.application.polish.{module_name}")

        assert getattr(use_cases, class_name) is getattr(module, class_name)


def test_create_question_task_execution_grant_contract_fields_are_additive() -> None:
    from app.application.polish.commands import CreatePolishQuestionTaskCommand

    command_fields = {field.name for field in fields(CreatePolishQuestionTaskCommand)}

    assert "next_question_execution_grant" in command_fields
    assert "next_question_execution_grant_snapshot" in command_fields
    legacy_command = CreatePolishQuestionTaskCommand(
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
    )
    assert legacy_command.next_question_execution_grant is None
    assert legacy_command.next_question_execution_grant_snapshot is None
    assert legacy_command.authorized_feedback_id is None
    assert legacy_command.authorized_answer_id is None
    assert legacy_command.authorized_parent_question_id is None


def test_next_question_execution_grant_lifecycle_states_are_represented() -> None:
    from app.application.polish.next_question_authorization import (
        build_next_question_execution_grant,
        consume_next_question_execution_grant,
        validate_next_question_intent,
    )

    issued_at = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    grant = build_next_question_execution_grant(
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-1",
        allowed_progress_node_refs=("node-1",),
        freshness_marker="feedback-1:v1",
        issued_at=issued_at,
        ttl_seconds=60,
    )

    assert grant.lifecycle_state(now=issued_at) == "active"
    assert grant.lifecycle_state(now=issued_at.replace(minute=2)) == "expired"
    assert (
        validate_next_question_intent(
            grant,
            session_id="session-1",
            feedback_id="feedback-1",
            answer_id="answer-1",
            parent_question_id="question-1",
            selected_progress_node_ref="node-2",
            freshness_marker="feedback-1:v1",
            now=issued_at,
        ).reason
        == "target_progress_node_mismatch"
    )
    consumed = consume_next_question_execution_grant(grant, now=issued_at)
    assert consumed.is_valid
    assert consumed.grant is not None
    assert consumed.grant.lifecycle_state(now=issued_at) == "consumed"


def test_answer_submission_boundary_rejects_blank_answer_with_existing_semantics() -> None:
    from app.application.polish.answer_application_service import AnswerSubmissionBoundaryBuilder
    from app.application.polish.commands import CreatePolishAnswerCommand

    command = CreatePolishAnswerCommand(
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        question_id="question-1",
        answer_text="   ",
    )

    result = AnswerSubmissionBoundaryBuilder().prepare(command)

    assert not result.is_success
    assert result.error is not None
    assert result.error.code == "validation_failed"
    assert result.error.message == "Answer text cannot be empty"
    assert result.error.details == {
        "field": "answer_text",
        "min_length": 2,
        "max_length": 8000,
    }


def test_answer_submission_boundary_trims_answer_and_preserves_idempotency_normalization() -> None:
    from app.application.polish.answer_application_service import AnswerSubmissionBoundaryBuilder
    from app.application.polish.commands import CreatePolishAnswerCommand

    command = CreatePolishAnswerCommand(
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        question_id="question-1",
        answer_text="  我会说明接口幂等和失败补偿。  ",
    )
    object.__setattr__(command, "idempotency_key", "  retry-key-1  ")

    result = AnswerSubmissionBoundaryBuilder().prepare(command)

    assert result.is_success
    assert result.value is not None
    assert result.value.answer_text == "我会说明接口幂等和失败补偿。"
    assert result.value.idempotency_key == "retry-key-1"


def test_answer_submission_boundary_rejects_too_long_idempotency_key_with_existing_semantics() -> None:
    from app.application.polish.answer_application_service import AnswerSubmissionBoundaryBuilder
    from app.application.polish.commands import CreatePolishAnswerCommand

    command = CreatePolishAnswerCommand(
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        question_id="question-1",
        answer_text="我会说明接口幂等和失败补偿。",
    )
    object.__setattr__(command, "idempotency_key", "k" * 129)

    result = AnswerSubmissionBoundaryBuilder().prepare(command)

    assert not result.is_success
    assert result.error is not None
    assert result.error.code == "validation_failed"
    assert result.error.message == "Idempotency key is too long"
    assert result.error.details == {
        "field": "idempotency_key",
        "max_length": 128,
        "actual_length": 129,
    }


def test_answer_submission_boundary_constructs_polish_answer_fields() -> None:
    from app.application.polish.answer_application_service import AnswerSubmissionBoundaryBuilder
    from app.application.polish.commands import CreatePolishAnswerCommand

    timestamp = datetime(2026, 6, 10, 1, 2, 3, tzinfo=UTC)
    command = CreatePolishAnswerCommand(
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        question_id="question-1",
        answer_text="  我会说明接口幂等和失败补偿。  ",
    )

    answer = AnswerSubmissionBoundaryBuilder().build_answer(
        command=command,
        answer_id="answer-1",
        answer_round=3,
        answer_text="我会说明接口幂等和失败补偿。",
        timestamp=timestamp,
    )

    assert answer.answer_id == "answer-1"
    assert answer.owner_id == "owner-1"
    assert answer.actor_id == "actor-1"
    assert answer.session_id == "session-1"
    assert answer.question_id == "question-1"
    assert answer.answer_round == 3
    assert answer.answer_text == "我会说明接口幂等和失败补偿。"
    assert answer.status == "saved"
    assert answer.created_at == timestamp
    assert answer.updated_at == timestamp


def test_polish_use_cases_create_answer_preserves_order_and_idempotency_behavior() -> None:
    from app.application.polish.commands import CreatePolishAnswerCommand
    from app.application.polish.entities import PolishAnswer, PolishQuestion, PolishSession
    from app.application.polish.use_cases import PolishUseCases

    now = datetime.now(UTC)
    session = PolishSession(
        session_id="session-m22-answer-order",
        owner_id="owner-1",
        actor_id="actor-1",
        binding_id="binding-1",
        resume_id="resume-1",
        resume_version_id="resume-version-1",
        job_id="job-1",
        job_version_id="job-version-1",
        status="running",
        topic_id="topic-1",
        subtopic_id=None,
        custom_topic_text_summary=None,
        created_at=now,
        updated_at=now,
    )
    question = PolishQuestion(
        question_id="question-m22-answer-order",
        owner_id="owner-1",
        actor_id="actor-1",
        session_id=session.session_id,
        ai_task_id="task-question-1",
        question_text="请说明你如何处理幂等提交。",
        status="generated",
        created_at=now,
        updated_at=now,
    )

    class RepositorySpy:
        def __init__(self) -> None:
            self.calls: list[str] = []
            self.answers_by_id: dict[str, PolishAnswer] = {}
            self.added_answers: list[PolishAnswer] = []
            self.answer_count_before_submission = 2

        def get_session(self, owner_id: str, session_id: str) -> PolishSession | None:
            self.calls.append("get_session")
            if owner_id == session.owner_id and session_id == session.session_id:
                return session
            return None

        def get_question(self, owner_id: str, question_id: str) -> PolishQuestion | None:
            self.calls.append("get_question")
            if owner_id == question.owner_id and question_id == question.question_id:
                return question
            return None

        def get_answer(self, owner_id: str, answer_id: str) -> PolishAnswer | None:
            self.calls.append("get_answer")
            answer = self.answers_by_id.get(answer_id)
            if answer is not None and answer.owner_id == owner_id:
                return answer
            return None

        def count_answers_for_question(self, owner_id: str, question_id: str) -> int:
            self.calls.append("count_answers_for_question")
            assert owner_id == question.owner_id
            assert question_id == question.question_id
            return self.answer_count_before_submission

        def add_answer(self, answer: PolishAnswer) -> None:
            self.calls.append("add_answer")
            self.answers_by_id[answer.answer_id] = answer
            self.added_answers.append(answer)

    class DummyRepository:
        pass

    repository = RepositorySpy()
    use_cases = PolishUseCases(
        polish_repository=repository,
        binding_repository=DummyRepository(),
        resume_repository=DummyRepository(),
        job_repository=DummyRepository(),
    )

    command = CreatePolishAnswerCommand(
        owner_id="owner-1",
        actor_id="actor-1",
        session_id=session.session_id,
        question_id=question.question_id,
        answer_text="  我会使用幂等 key 复用已经保存的回答。  ",
    )
    object.__setattr__(command, "idempotency_key", "  m22-answer-order-key  ")

    first_result = use_cases.create_answer(command)

    assert first_result.is_success
    assert first_result.value is repository.added_answers[0]
    first_answer = first_result.value
    assert first_answer is not None
    assert first_answer.answer_round == repository.answer_count_before_submission + 1
    assert first_answer.answer_text == "我会使用幂等 key 复用已经保存的回答。"
    assert first_answer.status == "saved"
    assert len(repository.added_answers) == 1
    assert repository.calls.index("get_session") < repository.calls.index("get_question")
    assert repository.calls.index("get_question") < repository.calls.index("count_answers_for_question")
    assert repository.calls.index("count_answers_for_question") < repository.calls.index("add_answer")

    second_result = use_cases.create_answer(command)

    assert second_result.is_success
    assert second_result.value is first_answer
    assert len(repository.added_answers) == 1
    assert repository.calls.count("count_answers_for_question") == 1
    assert repository.calls.count("add_answer") == 1

    conflicting_command = CreatePolishAnswerCommand(
        owner_id="owner-1",
        actor_id="actor-1",
        session_id=session.session_id,
        question_id=question.question_id,
        answer_text="我换了一个不同回答。",
    )
    object.__setattr__(conflicting_command, "idempotency_key", "m22-answer-order-key")

    conflict_result = use_cases.create_answer(conflicting_command)

    assert not conflict_result.is_success
    assert conflict_result.error is not None
    assert conflict_result.error.code == "validation_failed"
    assert conflict_result.error.message == "Idempotency key conflicts with a different answer payload"
    assert conflict_result.error.details == {
        "field": "idempotency_key",
        "reason": "idempotency_conflict",
    }
    assert len(repository.added_answers) == 1
    assert repository.calls.count("count_answers_for_question") == 1
    assert repository.calls.count("add_answer") == 1
    assert repository.answers_by_id == {first_answer.answer_id: first_answer}


def test_session_application_service_bootstrap_owns_skeleton_result_without_delegate_call() -> None:
    from app.application.polish.session_application_service import PolishSessionApplicationService

    class BootstrapShouldNotBeCalled:
        def bootstrap(self):  # pragma: no cover - assertion guard
            raise AssertionError("bootstrap should be owned by the focused session service")

    result = PolishSessionApplicationService(BootstrapShouldNotBeCalled()).bootstrap()

    assert result.value == "polish_skeleton"


def test_session_application_service_list_topics_owns_binding_visibility_without_delegate_call() -> None:
    from app.application.polish.queries import ListPolishTopicsQuery
    from app.application.polish.session_application_service import PolishSessionApplicationService

    class ListTopicsShouldNotBeCalled:
        def list_topics(self, query):  # pragma: no cover - assertion guard
            raise AssertionError("list_topics should be owned by the focused session service")

    class BindingRepositoryStub:
        def __init__(self) -> None:
            self.requested_binding_ids: list[str] = []

        def get(self, binding_id: str):
            self.requested_binding_ids.append(binding_id)
            return SimpleNamespace(owner_id="owner-1")

    binding_repository = BindingRepositoryStub()
    service = PolishSessionApplicationService(
        ListTopicsShouldNotBeCalled(),
        binding_repository=binding_repository,
    )

    result = service.list_topics(ListPolishTopicsQuery(owner_id="owner-1", resume_job_binding_id="binding-1"))

    assert result.is_success
    assert result.value
    assert binding_repository.requested_binding_ids == ["binding-1"]


def test_report_application_service_generate_report_owns_repository_orchestration_without_delegate_call() -> None:
    from app.application.polish.commands import GeneratePolishSessionReportCommand
    from app.application.polish.entities import PolishSession, PolishSessionDetail, PolishSessionReportSummary
    from app.application.polish.report_application_service import PolishReportApplicationService

    now = datetime.now(UTC)
    session = PolishSession(
        session_id="session-1",
        owner_id="owner-1",
        actor_id="actor-1",
        binding_id="binding-1",
        resume_id="resume-1",
        resume_version_id="resume-version-1",
        job_id="job-1",
        job_version_id="job-version-1",
        status="running",
        topic_id=None,
        subtopic_id=None,
        custom_topic_text_summary=None,
        created_at=now,
        updated_at=now,
    )

    class GenerateReportShouldNotBeCalled:
        def generate_session_report(self, command):  # pragma: no cover - assertion guard
            raise AssertionError("generate_session_report should be owned by the focused report service")

    class PolishRepositoryStub:
        def __init__(self, existing_session: PolishSession) -> None:
            self.existing_session = existing_session
            self.created_report_args: dict[str, str] | None = None

        def get_session(self, owner_id: str, session_id: str) -> PolishSession | None:
            if owner_id == self.existing_session.owner_id and session_id == self.existing_session.session_id:
                return self.existing_session
            return None

        def create_session_report(
            self,
            *,
            owner_id: str,
            actor_id: str,
            session_id: str,
            report_id: str,
        ) -> PolishSession:
            self.created_report_args = {
                "owner_id": owner_id,
                "actor_id": actor_id,
                "session_id": session_id,
                "report_id": report_id,
            }
            return replace(
                self.existing_session,
                report_summary=PolishSessionReportSummary(
                    report_id=report_id,
                    report_status="generated",
                    report_generated_at=now,
                ),
            )

    built_details: list[PolishSession] = []

    def build_session_detail(*, owner_id: str, session: PolishSession) -> PolishSessionDetail:
        built_details.append(session)
        return PolishSessionDetail(
            session=session,
            job_title=None,
            job_company=None,
            resume_title=None,
            binding_label=None,
            turns=(),
        )

    repository = PolishRepositoryStub(session)
    service = PolishReportApplicationService(
        GenerateReportShouldNotBeCalled(),
        polish_repository=repository,
        build_session_detail=build_session_detail,
    )

    result = service.generate_session_report(
        GeneratePolishSessionReportCommand(
            owner_id="owner-1",
            actor_id="actor-1",
            session_id="session-1",
        )
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.session.report_summary is not None
    assert result.value.session.report_summary.report_id.startswith("report_")
    assert repository.created_report_args == {
        "owner_id": "owner-1",
        "actor_id": "actor-1",
        "session_id": "session-1",
        "report_id": result.value.session.report_summary.report_id,
    }
    assert built_details == [result.value.session]


def test_polish_use_cases_create_feedback_task_is_shallow_delegate() -> None:
    from app.application.polish.commands import CreatePolishFeedbackTaskCommand
    from app.application.polish.entities import PolishTaskStatus
    from app.application.polish.use_cases import PolishUseCases
    from app.application.common.result import ApplicationResult
    from app.domain.shared.enums import AiTaskStatus
    from app.domain.shared.refs import TraceRef
    from app.domain.shared.clock import utc_now

    class DummyBindingRepository:
        def get_answer(self, owner_id: str, answer_id: str):
            return SimpleNamespace(owner_id=owner_id, answer_id=answer_id, session_id="session-1")

    class DummyResumeRepository:
        pass

    class DummyJobRepository:
        pass

    delegated = {}

    expected_task = PolishTaskStatus(
        ai_task_id="task_feedback_001",
        task_type="polish_feedback_generation",
        status=AiTaskStatus.SUCCEEDED,
        contract_ids=("P-POLISH-005",),
        retryable=False,
        result_ref=TraceRef(trace_ref_id="feedback_task_001", trace_type="feedback", created_at=utc_now()),
        user_visible_status="反馈已生成",
    )

    def fake_create_feedback_task(self, command: CreatePolishFeedbackTaskCommand) -> ApplicationResult[PolishTaskStatus]:
        delegated["command"] = command
        return ApplicationResult(value=expected_task)

    from app.application.polish.feedback_application_service import (
        PolishFeedbackApplicationService,
    )

    original = PolishFeedbackApplicationService.create_feedback_task
    PolishFeedbackApplicationService.create_feedback_task = fake_create_feedback_task
    try:
        use_cases = PolishUseCases(
            polish_repository=DummyBindingRepository(),
            binding_repository=DummyBindingRepository(),
            resume_repository=DummyResumeRepository(),
            job_repository=DummyJobRepository(),
        )

        command = CreatePolishFeedbackTaskCommand(
            owner_id="owner-1",
            actor_id="actor-1",
            session_id="session-1",
            answer_id="answer-1",
        )
        result = use_cases.create_feedback_task(command)

        assert result.value == expected_task
        assert delegated["command"] == command
    finally:
        PolishFeedbackApplicationService.create_feedback_task = original


def test_polish_feedback_application_service_create_feedback_task_owns_main_flow() -> None:
    from app.application.polish.commands import CreatePolishFeedbackTaskCommand
    from app.application.polish.entities import (
        PolishAnswer,
        PolishFeedback,
        PolishQuestion,
        PolishSession,
        PolishSessionAnswerDetail,
        PolishSessionDetail,
        PolishSessionTurn,
        PolishTaskStatus,
    )
    from app.application.polish.feedback_application_service import PolishFeedbackApplicationService
    from app.application.common.result import ApplicationResult
    from app.domain.shared.clock import utc_now
    from app.domain.shared.enums import AiTaskStatus
    from app.domain.shared.refs import TraceRef

    now = utc_now()
    session = PolishSession(
        session_id="session-1",
        owner_id="owner-1",
        actor_id="actor-1",
        binding_id="binding-1",
        resume_id="resume-1",
        resume_version_id="resume-version-1",
        job_id="job-1",
        job_version_id="job-version-1",
        status="running",
        topic_id="topic-1",
        subtopic_id=None,
        custom_topic_text_summary=None,
        created_at=now,
        updated_at=now,
    )
    answer = PolishAnswer(
        answer_id="answer-1",
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        question_id="question-1",
        answer_round=1,
        answer_text="我会说明异步和幂等。",
        status="saved",
        created_at=now,
        updated_at=now,
    )
    question = PolishQuestion(
        question_id="question-1",
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        ai_task_id="task-question-1",
        question_text="请给我一份回答建议。",
        status="generated",
        created_at=now,
        updated_at=now,
    )

    class RepositoryStub:
        def __init__(self) -> None:
            self.get_session_args: list[tuple[str, str]] = []
            self.get_answer_args: list[tuple[str, str]] = []
            self.get_question_args: list[tuple[str, str]] = []
            self.get_latest_feedback_calls: list[tuple[str, str, str]] = []
            self.add_feedback_calls: list[PolishFeedback] = []
            self.add_task_calls: list[tuple[PolishTaskStatus, str, str, str]] = []

        def get_session(self, owner_id: str, session_id: str) -> PolishSession | None:
            self.get_session_args.append((owner_id, session_id))
            return session

        def get_answer(self, owner_id: str, answer_id: str) -> PolishAnswer | None:
            self.get_answer_args.append((owner_id, answer_id))
            return answer

        def get_question(self, owner_id: str, question_id: str) -> PolishQuestion | None:
            self.get_question_args.append((owner_id, question_id))
            return question

        def get_latest_feedback_for_answer(self, *, owner_id: str, answer_id: str, status: str) -> None:
            self.get_latest_feedback_calls.append((owner_id, answer_id, status))
            return None

        def add_feedback(self, feedback: PolishFeedback) -> None:
            self.add_feedback_calls.append(feedback)

        def add_task(
            self,
            task: PolishTaskStatus,
            *,
            owner_id: str,
            actor_id: str,
            target_ref_id: str,
        ) -> None:
            self.add_task_calls.append((task, owner_id, actor_id, target_ref_id))

    class GenerationResult:
        succeeded = True
        payload = {
            "status": "generated",
            "schema_id": "polish_feedback_generated_v1",
            "schema_version": "1.0",
            "contract_ids": ["P-POLISH-005"],
            "feedback_text": "反馈文本",
            "answer_summary": "回答总结",
            "score_result": {
                "score_type": "polish_answer",
                "score_value": 80,
                "dimension_scores": [
                    {"dimension": "correctness", "score": 84, "rationale": "方向正确。"},
                    {"dimension": "depth", "score": 78, "rationale": "细节略少。"},
                    {"dimension": "tradeoff_reasoning", "score": 76, "rationale": "取舍略少。"},
                    {"dimension": "structure", "score": 82, "rationale": "结构清楚。"},
                    {"dimension": "engineering_awareness", "score": 80, "rationale": "工程意识中等。"},
                ],
            },
            "loss_points": [],
            "reference_answer": None,
            "trace_refs": ("trace_feedback",),
        }
        validation_errors = ()
        metadata = {"provider_status": "unit_test"}
        trace_refs = ()

    class GenerationServiceStub:
        def __init__(self) -> None:
            self.calls = 0

        def generate_feedback_v1(self, *_: object, **__: object) -> GenerationResult:
            self.calls += 1
            return GenerationResult()

    class OperationsStub:
        def __init__(self, repository: RepositoryStub, generation_service: GenerationServiceStub) -> None:
            self._polish_repository = repository
            self._feedback_generation_service = generation_service

        def _build_session_detail(self, *, owner_id: str, session: PolishSession, include_turns: bool = True) -> PolishSessionDetail:
            return PolishSessionDetail(
                session=session,
                job_title="Job",
                job_company="Company",
                resume_title="Resume",
                binding_label="Job / Resume",
                turns=(
                    PolishSessionTurn(
                        question_id="question-1",
                        question_text="请给我一份回答建议。",
                        question_created_at=now,
                        answers=(
                            PolishSessionAnswerDetail(
                                answer_id="answer-1",
                                answer_round=1,
                                answer_text="我会说明异步和幂等。",
                                answer_created_at=now,
                                feedback_text=None,
                                feedback_id=None,
                                score_result_id=None,
                                feedback_created_at=None,
                                feedback_payload=None,
                            ),
                        ),
                    ),
                ),
            )

    repository = RepositoryStub()
    generation_service = GenerationServiceStub()
    service = PolishFeedbackApplicationService(OperationsStub(repository, generation_service))

    result = service.create_feedback_task(
        CreatePolishFeedbackTaskCommand(
            owner_id="owner-1",
            actor_id="actor-1",
            session_id="session-1",
            answer_id="answer-1",
        )
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert generation_service.calls == 1
    assert repository.get_session_args == [("owner-1", "session-1")]
    assert repository.get_answer_args == [("owner-1", "answer-1")]
    assert repository.get_question_args == [("owner-1", "question-1")]
    assert repository.get_latest_feedback_calls == [("owner-1", "answer-1", "generated")]
    assert len(repository.add_feedback_calls) == 1
    assert len(repository.add_task_calls) == 1
    assert repository.add_task_calls[0][1] == "owner-1"
    assert repository.add_task_calls[0][3] == "answer-1"


def test_polish_feedback_application_service_persists_feedback_and_task_with_candidate_refs_only() -> None:
    import json

    from sqlalchemy import func, select

    from app.application.polish.commands import CreatePolishFeedbackTaskCommand
    from app.application.polish.entities import (
        PolishAnswer,
        PolishQuestion,
        PolishSession,
        PolishSessionAnswerDetail,
        PolishSessionDetail,
        PolishSessionTurn,
    )
    from app.application.polish.feedback_application_service import PolishFeedbackApplicationService
    from app.application.polish.feedback_generation_service import (
        FeedbackGenerationContext,
        FeedbackGenerationResult,
    )
    from app.domain.shared.clock import utc_now
    from app.domain.shared.enums import AiTaskStatus
    from app.infrastructure.db.models.ai_task import AiTask
    from app.infrastructure.db.models.asset import Asset, AssetVersion
    from app.infrastructure.db.models.feedback import Feedback as FeedbackModel
    from app.infrastructure.db.models.polish_candidate import PolishCandidateRecord
    from app.infrastructure.db.models.training import TrainingRecommendation, TrainingTask
    from app.infrastructure.db.models.weakness import Weakness
    from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
    from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema

    session_factory = build_session_factory(DbSettings(database_url="sqlite+pysqlite:///:memory:"))
    initialize_schema(session_factory=session_factory)
    repository = SqlAlchemyPolishRepository(session_factory)
    now = utc_now()
    session = PolishSession(
        session_id="session-m23-feedback-boundary",
        owner_id="owner-1",
        actor_id="actor-1",
        binding_id="binding-1",
        resume_id="resume-1",
        resume_version_id="resume-version-1",
        job_id="job-1",
        job_version_id="job-version-1",
        status="running",
        topic_id="topic-1",
        subtopic_id=None,
        custom_topic_text_summary=None,
        created_at=now,
        updated_at=now,
    )
    question = PolishQuestion(
        question_id="question-m23-feedback-boundary",
        owner_id="owner-1",
        actor_id="actor-1",
        session_id=session.session_id,
        ai_task_id="task-question-m23",
        question_text="请说明你如何处理支付链路失败恢复。",
        status="generated",
        created_at=now,
        updated_at=now,
        progress_node_ref="progress-node-reliability",
        evidence_refs=("evidence_resume_payment",),
    )
    answer = PolishAnswer(
        answer_id="answer-m23-feedback-boundary",
        owner_id="owner-1",
        actor_id="actor-1",
        session_id=session.session_id,
        question_id=question.question_id,
        answer_round=1,
        answer_text="我会用 MQ 解耦、幂等键和补偿任务处理失败恢复。",
        status="saved",
        created_at=now,
        updated_at=now,
    )
    repository.add_session(session)
    repository.add_question(question)
    repository.add_answer(answer)

    generation_payload = {
        "schema_id": "polish_feedback_generated_v1",
        "schema_version": "1.0",
        "status": "generated",
        "contract_ids": ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005"],
        "feedback_text": "回答覆盖了 MQ 解耦和幂等，但缺少失败恢复指标。",
        "answer_summary": "候选人说明了补偿和幂等策略。",
        "score_result": {"score_type": "polish_answer", "score_value": 82, "score_level": "good"},
        "loss_points": [
            {
                "loss_point_id": "lp_failure_recovery_metric",
                "severity": "minor",
                "deduction": 8,
                "reason": "缺少恢复耗时和堆积量指标。",
                "evidence_refs": ["evidence_resume_payment"],
            }
        ],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "ref_failure_recovery_metric",
                    "title": "失败恢复指标",
                    "content": "补充失败率、恢复耗时和消息堆积量的监控边界。",
                    "addresses_loss_point_ids": ["lp_failure_recovery_metric"],
                }
            ]
        },
        "asset_consistency_check": {
            "status": "consistent",
            "checked_asset_refs": ["asset_payment_reliability"],
            "conflicts": [],
            "unsupported_claims": [],
            "user_clarification_required": False,
        },
        "answer_coverage": {
            "expected_points": ["幂等", "补偿", "观测"],
            "covered_points": ["幂等", "补偿"],
            "missing_points": ["观测"],
            "weak_points": ["失败恢复指标"],
            "contradicted_points": [],
        },
        "answer_change_analysis": {
            "has_prior_attempts": False,
            "previous_answer_refs": [],
            "retained_points": [],
            "newly_added_points": [],
            "regressed_points": [],
            "repeated_loss_points": [],
            "fixed_loss_points": [],
            "score_delta": None,
            "trend": "unchanged",
        },
        "feedback_cards": [
            {"card_type": "overall", "status": "generated", "payload": {"summary": "核心方案可用"}},
            {
                "card_type": "asset_update_candidates",
                "status": "candidate",
                "payload": [
                    {
                        "candidate_type": "project_asset_update_candidate",
                        "candidate_ref": "asset_update_candidate_ref_m23_payment_metric",
                        "user_confirmation_required": True,
                        "target_asset_ref": {
                            "resource_type": "asset",
                            "resource_id": "asset_payment_reliability",
                        },
                        "summary": "补充支付链路失败恢复指标素材。",
                    }
                ],
            },
        ],
        "next_recommended_actions": ["review_reference_answer"],
        "low_confidence_flags": [],
        "trace_refs": [{"resource_type": "llm_trace", "resource_id": "trace_feedback_m23"}],
        "feedback_metadata": {"provider_status": "unit_test"},
    }

    class GenerationServiceStub:
        def __init__(self) -> None:
            self.contexts: list[FeedbackGenerationContext] = []

        def generate_feedback_v1(self, context: FeedbackGenerationContext) -> FeedbackGenerationResult:
            self.contexts.append(context)
            return FeedbackGenerationResult(
                succeeded=True,
                payload=generation_payload,
                validation_errors=(),
                trace_refs=("trace_generation_m23",),
                metadata={
                    "provider_status": "unit_test",
                    "validation_stage": "final",
                    "candidate_valid": True,
                    "raw_prompt": "DO_NOT_PERSIST",
                    "completion_payload": "DO_NOT_PERSIST",
                    "secret_token": "DO_NOT_PERSIST",
                },
            )

    class OperationsStub:
        def __init__(self, generation_service: GenerationServiceStub) -> None:
            self._polish_repository = repository
            self._feedback_generation_service = generation_service

        def _build_session_detail(
            self,
            *,
            owner_id: str,
            session: PolishSession,
            include_turns: bool = True,
        ) -> PolishSessionDetail:
            assert owner_id == "owner-1"
            assert include_turns is True
            return PolishSessionDetail(
                session=session,
                job_title="Backend Engineer",
                job_company="Example Inc.",
                resume_title="支付平台项目",
                binding_label="Backend Engineer / 支付平台项目",
                turns=(
                    PolishSessionTurn(
                        question_id=question.question_id,
                        question_text=question.question_text,
                        question_created_at=question.created_at,
                        progress_node_ref=question.progress_node_ref,
                        evidence_refs=question.evidence_refs,
                        answers=(
                            PolishSessionAnswerDetail(
                                answer_id=answer.answer_id,
                                answer_round=answer.answer_round,
                                answer_text=answer.answer_text,
                                answer_created_at=answer.created_at,
                                feedback_text=None,
                                feedback_id=None,
                                score_result_id=None,
                                feedback_created_at=None,
                                feedback_payload=None,
                            ),
                        ),
                    ),
                ),
                progress_context={
                    "canonical_project_assets": {
                        "items": [
                            {
                                "asset_id": "asset_payment_reliability",
                                "title": "支付链路可靠性",
                                "summary": "支付链路已有补偿方案素材。",
                            }
                        ]
                    }
                },
            )

    generation_service = GenerationServiceStub()
    service = PolishFeedbackApplicationService(OperationsStub(generation_service))

    result = service.create_feedback_task(
        CreatePolishFeedbackTaskCommand(
            owner_id="owner-1",
            actor_id="actor-1",
            session_id=session.session_id,
            answer_id=answer.answer_id,
        )
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert len(generation_service.contexts) == 1
    provider_context = generation_service.contexts[0]
    assert provider_context.session_id == session.session_id
    assert provider_context.question_id == question.question_id
    assert provider_context.answer_id == answer.answer_id
    assert provider_context.evidence_refs == ("evidence_resume_payment",)

    task_refs = {(ref.resource_type, ref.resource_id) for ref in result.value.candidate_refs}
    feedback_candidate_refs = [
        ref.resource_id for ref in result.value.candidate_refs if ref.resource_type == "feedback_candidate"
    ]
    asset_candidate_refs = [
        ref.resource_id for ref in result.value.candidate_refs if ref.resource_type == "asset_update_candidate"
    ]
    assert len(feedback_candidate_refs) == 1
    assert asset_candidate_refs == ["asset_update_candidate_ref_m23_payment_metric"]
    assert {
        ref.resource_type for ref in result.value.candidate_refs
    } <= {
        "feedback_candidate",
        "asset_update_candidate",
        "answer",
        "question",
        "progress_node",
        "evidence",
        "validation_result",
        "trace",
    }
    assert ("asset", "asset_payment_reliability") not in task_refs
    assert ("weakness", "lp_failure_recovery_metric") not in task_refs

    with session_factory() as db:
        feedback_rows = list(db.scalars(select(FeedbackModel)))
        ai_task_rows = list(db.scalars(select(AiTask)))
        formal_counts = {
            model.__tablename__: db.scalar(select(func.count()).select_from(model))
            for model in (
                PolishCandidateRecord,
                Weakness,
                Asset,
                AssetVersion,
                TrainingRecommendation,
                TrainingTask,
            )
        }

    assert len(feedback_rows) == 1
    assert len(ai_task_rows) == 1
    assert ai_task_rows[0].id == result.value.ai_task_id
    assert ai_task_rows[0].target_ref_id == answer.answer_id
    assert feedback_rows[0].id == result.value.result_ref.trace_ref_id
    assert feedback_rows[0].ai_task_id == result.value.ai_task_id
    assert formal_counts == {
        "polish_candidates": 0,
        "weaknesses": 0,
        "assets": 0,
        "asset_versions": 0,
        "training_recommendations": 0,
        "training_tasks": 0,
    }

    stored_payload = json.loads(feedback_rows[0].feedback_summary)
    stored_metadata = stored_payload["feedback_metadata"]
    assert stored_metadata["candidate_ref"] == feedback_candidate_refs[0]
    assert stored_metadata["asset_update_candidate_refs"] == asset_candidate_refs
    assert stored_metadata["asset_update_formal_write_performed"] is False
    assert stored_metadata["asset_update_user_confirmation_required"] is True
    assert "raw_prompt" not in stored_metadata
    assert "completion_payload" not in stored_metadata
    assert "secret_token" not in stored_metadata

    asset_cards = [
        card for card in stored_payload["feedback_cards"] if card["card_type"] == "asset_update_candidates"
    ]
    assert len(asset_cards) == 1
    asset_candidate = asset_cards[0]["payload"][0]
    assert asset_candidate["candidate_ref"] == "asset_update_candidate_ref_m23_payment_metric"
    assert asset_candidate["user_confirmation_required"] is True
    assert asset_candidate["formal_write_blocked_until"] == "user_confirmation"
    assert stored_payload["loss_points"][0]["loss_point_id"] == "lp_failure_recovery_metric"
