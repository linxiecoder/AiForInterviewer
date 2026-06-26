from __future__ import annotations

import pytest

from app.application.training.use_cases import TrainingUseCases
from app.domain.shared.clock import utc_now
from app.domain.shared.ids import ResourceIdPrefix, stable_resource_id
from app.infrastructure.db.models.report import InterviewReport, ReportSection
from app.infrastructure.db.session import DbSettings
from app.infrastructure.security.auth import AuthRuntimeSettings, build_auth_runtime
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.main import ApiSettings, create_app
from tests.api.asgi_client import call_json, call_json_response

USER_A_ID = stable_resource_id(ResourceIdPrefix.USER, "user_a@example.com")
USER_B_ID = stable_resource_id(ResourceIdPrefix.USER, "user_b@example.com")
USER_A_PASSWORD = "password-a"
USER_B_PASSWORD = "password-b"


def test_get_polish_summary_report_returns_owner_scoped_detail() -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)
    _seed_report(
        app,
        owner_id=owner_id,
        report_id="report_polish_summary_a",
        session_id="sess_polish_a",
        section_key="summary",
        section_summary="Clear structure and concrete examples.",
    )

    status_code, body = call_json(
        app,
        "/api/v1/reports/report_polish_summary_a",
        headers={"cookie": owner_cookie},
    )

    assert status_code == 200
    assert body["resource_type"] == "report_detail"
    data = body["data"]
    assert data["report_id"] == "report_polish_summary_a"
    assert data["report_type"] == "polish_summary"
    assert data["session_ref"] == "sess_polish_a"
    assert data["report_status"] == "available"
    assert data["copy_content_available"] is False
    assert data["source_availability"]["status"] == "source_available"
    assert data["sections"] == [
        {
            "section_key": "summary",
            "section_summary": "Clear structure and concrete examples.",
            "score_ref": None,
        }
    ]
    assert "download_url" not in data
    assert "filename" not in data
    assert "export_artifact" not in data


def test_reports_retrieval_v1_exposes_no_write_or_copy_routes() -> None:
    app = _app_with_two_users()
    report_routes = {
        (method, getattr(route, "path", ""))
        for route in app.routes
        for method in (getattr(route, "methods", None) or set()) - {"HEAD", "OPTIONS"}
        if getattr(route, "path", "").startswith("/api/v1/reports")
    }

    assert ("GET", "/api/v1/reports/{report_id}") in report_routes
    assert not {
        (method, path)
        for method, path in report_routes
        if method in {"POST", "PUT", "PATCH", "DELETE"}
    }
    assert not {(method, path) for method, path in report_routes if "copy" in path}


def test_get_report_denies_cross_owner_access_without_leaking_existence() -> None:
    app = _app_with_two_users()
    owner_a_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_b_cookie = _login_cookie(app, "user_b", USER_B_PASSWORD)
    owner_a_id = _current_owner_id(app, owner_a_cookie)
    _seed_report(
        app,
        owner_id=owner_a_id,
        report_id="report_owner_a_only",
        session_id="sess_owner_a_only",
    )

    status_code, body = call_json(
        app,
        "/api/v1/reports/report_owner_a_only",
        headers={"cookie": owner_b_cookie},
    )

    assert status_code == 404
    assert body["error"]["code"] == "not_found_or_inaccessible"


def test_get_report_returns_404_for_missing_report() -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/reports/report_missing",
        headers={"cookie": owner_cookie},
    )

    assert status_code == 404
    assert body["error"]["code"] == "not_found_or_inaccessible"


def test_get_report_rejects_invalid_id_and_unsupported_report_type() -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)
    _seed_report(
        app,
        owner_id=owner_id,
        report_id="report_pressure_full",
        session_id="sess_pressure_like",
        report_type="pressure_full",
    )

    invalid_id_status, invalid_id_body = call_json(
        app,
        "/api/v1/reports/not-a-report-id",
        headers={"cookie": owner_cookie},
    )
    unsupported_type_status, unsupported_type_body = call_json(
        app,
        "/api/v1/reports/report_pressure_full",
        headers={"cookie": owner_cookie},
    )

    assert invalid_id_status == 422
    assert invalid_id_body["error"]["code"] == "validation_failed"
    assert unsupported_type_status == 422
    assert unsupported_type_body["error"]["code"] == "validation_failed"


def test_get_report_does_not_call_training_use_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _app_with_two_users()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)
    _seed_report(
        app,
        owner_id=owner_id,
        report_id="report_no_training_call",
        session_id="sess_no_training_call",
    )

    def fail_training_call(*_args, **_kwargs):  # pragma: no cover - assertion guard
        raise AssertionError("Report retrieval must not call Training use cases.")

    monkeypatch.setattr(TrainingUseCases, "list_training_suggestions", fail_training_call)
    monkeypatch.setattr(TrainingUseCases, "dismiss_training_suggestion", fail_training_call)
    monkeypatch.setattr(TrainingUseCases, "start_training_task", fail_training_call)
    monkeypatch.setattr(TrainingUseCases, "complete_training_task", fail_training_call)

    status_code, body = call_json(
        app,
        "/api/v1/reports/report_no_training_call",
        headers={"cookie": owner_cookie},
    )

    assert status_code == 200
    assert body["data"]["report_id"] == "report_no_training_call"


def _seed_report(
    app,
    *,
    owner_id: str,
    report_id: str,
    session_id: str,
    report_type: str = "polish_summary",
    section_key: str | None = None,
    section_summary: str | None = None,
) -> None:
    session_factory = app.state.db_session_factory
    now = utc_now()
    with session_factory() as session:
        session.add(
            InterviewReport(
                id=report_id,
                owner_id=owner_id,
                actor_id=owner_id,
                record_version=1,
                status="available",
                trace_ref_ids=["trace_report_seed"],
                evidence_ref_ids=["evidence_report_seed"],
                created_at=now,
                updated_at=now,
                session_id=session_id,
                ai_task_id=None,
                score_result_id=None,
                report_type=report_type,
                generated_at=now,
            )
        )
        if section_key is not None:
            session.add(
                ReportSection(
                    id=f"{report_id}_{section_key}",
                    owner_id=owner_id,
                    actor_id=owner_id,
                    record_version=1,
                    status="available",
                    trace_ref_ids=None,
                    evidence_ref_ids=["evidence_section_seed"],
                    created_at=now,
                    updated_at=now,
                    report_id=report_id,
                    section_key=section_key,
                    score_result_id=None,
                    section_summary=section_summary,
                )
            )
        session.commit()


def _app_with_two_users():
    runtime = build_auth_runtime(
        AuthRuntimeSettings(
            dev_user_password=USER_A_PASSWORD,
            dev_user_identifier="user_a@example.com",
            dev_user_email="user_a@example.com",
            dev_username="user_a",
            dev_display_name="User A",
            seed_dev_user=True,
        ),
        cookie_path="/api/v1",
    )
    runtime.user_store.add_user(
        user_id=USER_B_ID,
        email="user_b@example.com",
        username="user_b",
        display_name="User B",
        password_hash=Pbkdf2PasswordHasher().hash_password(USER_B_PASSWORD),
    )
    return create_app(
        settings=ApiSettings(),
        auth_runtime=runtime,
        db_settings=DbSettings(database_url="sqlite+pysqlite:///:memory:"),
        initialize_schema=True,
    )


def _login_cookie(app, identifier: str, password: str) -> str:
    status_code, _body, headers = call_json_response(
        app,
        "/api/v1/auth/login",
        "POST",
        json_body={"identifier": identifier, "password": password},
    )
    assert status_code == 200
    values = headers["set-cookie"]
    assert len(values) == 1
    cookie_value = values[0]
    prefix = "aifi_session="
    assert prefix in cookie_value
    token = cookie_value.split(prefix, 1)[1].split(";", 1)[0]
    return f"aifi_session={token}"


def _current_owner_id(app, cookie: str) -> str:
    status_code, body = call_json(app, "/api/v1/auth/me", headers={"cookie": cookie})
    assert status_code == 200
    return body["data"]["owner_id"]
