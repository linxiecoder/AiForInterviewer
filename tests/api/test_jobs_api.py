from __future__ import annotations

from app.application.bindings.commands import RegisterResumeVersionCommand
from app.application.bindings.use_cases import BindingUseCases
from app.domain.shared.ids import ResourceIdPrefix, stable_resource_id
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.security.auth import AuthRuntimeSettings, build_auth_runtime
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.main import create_app
from tests.api.asgi_client import call_json, call_json_response


USER_A_ID = stable_resource_id(ResourceIdPrefix.USER, "user_a@example.com")
USER_B_ID = stable_resource_id(ResourceIdPrefix.USER, "user_b@example.com")
USER_A_PASSWORD = "password-a"
USER_B_PASSWORD = "password-b"


def test_create_job_success_and_returns_current_version() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Platform Engineer",
            "company": "ACME",
            "department": "Engineering",
            "responsibilities": ["Build APIs", "Maintain code"],
            "requirements": ["Python", "SQL"],
            "other_notes": "Focus on correctness",
            "application_status": "draft",
        },
        headers={"cookie": owner_cookie},
    )

    assert status_code == 200
    assert body["resource_type"] == "job_detail"
    assert body["data"]["binding_summary"]["status"] == "not_bound"
    assert body["data"]["latest_match_summary"]["status"] == "match_not_generated"

    job_id = body["data"]["job_id"]
    current_version_id = body["data"]["current_version_ref"]["version_id"]

    status_code, body = call_json(app, f"/api/v1/jobs/{job_id}", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert body["data"]["current_version_ref"]["version_id"] == current_version_id
    assert body["data"]["department"] == "Engineering"
    assert body["data"]["responsibilities"] == ["Build APIs", "Maintain code"]
    assert body["data"]["requirements"] == ["Python", "SQL"]
    assert body["data"]["other_notes"] == "Focus on correctness"

    status_code, body = call_json(app, "/api/v1/jobs", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert body["data"][0]["department"] == "Engineering"


def test_jobs_are_scoped_to_current_owner() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_a_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_b_cookie = _login_cookie(app, "user_b", USER_B_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Job A",
            "responsibilities": ["R1"],
            "requirements": ["Q1"],
        },
        headers={"cookie": owner_a_cookie},
    )
    assert status_code == 200
    job_a = body["data"]["job_id"]

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Job B",
            "responsibilities": ["R2"],
            "requirements": ["Q2"],
        },
        headers={"cookie": owner_b_cookie},
    )
    assert status_code == 200
    job_b = body["data"]["job_id"]

    status_code, body = call_json(app, "/api/v1/jobs", headers={"cookie": owner_a_cookie})
    assert status_code == 200
    assert len(body["data"]) == 1
    assert body["data"][0]["job_id"] == job_a

    status_code, body = call_json(app, "/api/v1/jobs", headers={"cookie": owner_b_cookie})
    assert status_code == 200
    assert {item["job_id"] for item in body["data"]} == {job_b}


def test_job_detail_includes_binding_summary_and_version_snapshot() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Senior Engineer",
            "responsibilities": ["Design systems"],
            "requirements": ["Go"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]
    job_version = body["data"]["current_version_ref"]["version_id"]

    _register_resume_version(owner_id, "res_demo", "res_ver_001")
    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": "res_demo", "job_id": job_id},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200

    status_code, body = call_json(app, f"/api/v1/jobs/{job_id}", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert body["data"]["binding_summary"]["status"] == "bound"
    assert body["data"]["binding_summary"]["resume_id"] == "res_demo"
    assert body["data"]["binding_summary"]["resume_version_ref"]["version_id"] == "res_ver_001"
    assert body["data"]["current_version_ref"]["version_id"] == job_version


def test_job_update_success_advances_version_and_record_version() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Embedded Engineer",
            "responsibilities": ["Implement"],
            "requirements": ["C++"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]
    current_version = body["data"]["current_version_ref"]["version_id"]

    patch = {
        "base_version_ref": {
            "resource_type": "job",
            "resource_id": job_id,
            "version_id": current_version,
        },
        "title": "Embedded Engineer II",
        "responsibilities": ["Implement", "Test"],
    }
    status_code, body = call_json(
        app,
        f"/api/v1/jobs/{job_id}",
        "PATCH",
        json_body=patch,
        headers={"cookie": owner_cookie},
    )

    assert status_code == 200
    assert body["data"]["title"] == "Embedded Engineer II"
    assert body["data"]["responsibilities"] == ["Implement", "Test"]
    assert body["data"]["record_version"] == 2
    assert body["data"]["current_version_ref"]["version_id"] != current_version


def test_job_update_stale_base_version_returns_conflict() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "QA Engineer",
            "responsibilities": ["Quality"],
            "requirements": ["Testing"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]
    current_version = body["data"]["current_version_ref"]["version_id"]

    status_code, _body = call_json(
        app,
        f"/api/v1/jobs/{job_id}",
        "PATCH",
        json_body={
            "base_version_ref": {
                "resource_type": "job",
                "resource_id": job_id,
                "version_id": current_version,
            },
            "status": "archived",
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200

    status_code, body = call_json(
        app,
        f"/api/v1/jobs/{job_id}",
        "PATCH",
        json_body={
            "base_version_ref": {
                "resource_type": "job",
                "resource_id": job_id,
                "version_id": current_version,
            },
            "status": "active",
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 409
    assert body["error"]["code"] == "stale_version_conflict"


def test_job_can_be_archived_with_patch_status() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "DevOps Engineer",
            "responsibilities": ["Release"],
            "requirements": ["Linux"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]
    current_version = body["data"]["current_version_ref"]["version_id"]

    status_code, body = call_json(
        app,
        f"/api/v1/jobs/{job_id}",
        "PATCH",
        json_body={
            "base_version_ref": {
                "resource_type": "job",
                "resource_id": job_id,
                "version_id": current_version,
            },
            "status": "archived",
        },
        headers={"cookie": owner_cookie},
    )

    assert status_code == 200
    assert body["data"]["status"] == "archived"
    assert body["data"]["archived_at"] is not None


def test_job_owner_scope_for_get_and_update() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_a_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_b_cookie = _login_cookie(app, "user_b", USER_B_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Staff Engineer",
            "responsibilities": ["Review"],
            "requirements": ["Architecture"],
        },
        headers={"cookie": owner_a_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]
    current_version = body["data"]["current_version_ref"]["version_id"]

    status_code, body = call_json(app, f"/api/v1/jobs/{job_id}", headers={"cookie": owner_b_cookie})
    assert status_code == 404
    assert body["error"]["code"] in {"not_found_or_inaccessible", "permission_denied"}

    status_code, body = call_json(
        app,
        f"/api/v1/jobs/{job_id}",
        "PATCH",
        json_body={
            "base_version_ref": {
                "resource_type": "job",
                "resource_id": job_id,
                "version_id": current_version,
            },
            "title": "Should Fail",
        },
        headers={"cookie": owner_b_cookie},
    )
    assert status_code in {404, 403}
    assert body["error"]["code"] in {"not_found_or_inaccessible", "permission_denied", "owner_mismatch"}


def test_job_update_validation_failed_without_base_version_or_record_version() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Data Analyst",
            "responsibilities": ["Collect"],
            "requirements": ["SQL"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]

    status_code, body = call_json(
        app,
        f"/api/v1/jobs/{job_id}",
        "PATCH",
        json_body={},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 422
    assert body["error"]["code"] == "validation_failed"


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
    return create_app(auth_runtime=runtime)


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


def _register_resume_version(owner_id: str, resume_id: str, resume_version_id: str) -> None:
    command = RegisterResumeVersionCommand(
        owner_id=owner_id,
        resume_id=resume_id,
        resume_version_id=resume_version_id,
    )
    binding_use_case = BindingUseCases(
        binding_repository=SqlAlchemyBindingRepository(),
        job_repository=SqlAlchemyJobRepository(),
    )
    binding_use_case.register_resume(command)


def _reset_repositories() -> None:
    SqlAlchemyJobRepository.clear_state()
    SqlAlchemyBindingRepository.clear_state()
