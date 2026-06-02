"""Regression tests for the Polish application service module split."""

from __future__ import annotations

import importlib
import inspect
from dataclasses import replace
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
