"""Regression tests for the Polish application service module split."""

from __future__ import annotations

import importlib
import inspect


SERVICE_MODULES = (
    ("session_application_service", "PolishSessionApplicationService"),
    ("question_application_service", "PolishQuestionApplicationService"),
    ("answer_application_service", "PolishAnswerApplicationService"),
    ("feedback_application_service", "PolishFeedbackApplicationService"),
    ("progress_application_service", "PolishProgressApplicationService"),
    ("report_application_service", "PolishReportApplicationService"),
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
