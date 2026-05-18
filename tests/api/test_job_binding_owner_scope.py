from __future__ import annotations

from app.application.bindings.commands import RegisterResumeVersionCommand
from app.application.bindings.use_cases import BindingUseCases
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.security.auth import AuthRuntimeSettings, build_auth_runtime
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.main import create_app
from app.domain.shared.ids import ResourceIdPrefix, stable_resource_id
from tests.api.asgi_client import call_json, call_json_response

USER_A_ID = stable_resource_id(ResourceIdPrefix.USER, "user_a@example.com")
USER_B_ID = stable_resource_id(ResourceIdPrefix.USER, "user_b@example.com")
USER_A_PASSWORD = "password-a"
USER_B_PASSWORD = "password-b"
RESUME_A_ID = "resume_a"
RESUME_B_ID = "resume_b"


def test_owner_scope_prevents_user_b_access_to_user_a_jobs() -> None:
    app = _app_with_two_users()
    _reset_repositories()

    owner_a_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_b_cookie = _login_cookie(app, "user_b", USER_B_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={"title": "Owner A Job", "responsibilities": ["Analyze"], "requirements": ["Python"]},
        headers={"cookie": owner_a_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]

    status_code, body = call_json(app, "/api/v1/jobs", headers={"cookie": owner_a_cookie})
    assert status_code == 200
    assert any(item["job_id"] == job_id for item in body["data"])

    status_code, body = call_json(app, "/api/v1/jobs", headers={"cookie": owner_b_cookie})
    assert status_code == 200
    assert all(item["job_id"] != job_id for item in body["data"])


def test_owner_scope_prevents_user_b_binding_user_a_job() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_a_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_a_id = _current_owner_id(app, owner_a_cookie)
    owner_b_cookie = _login_cookie(app, "user_b", USER_B_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={"title": "Owner A Job", "responsibilities": ["Plan"], "requirements": ["Security"]},
        headers={"cookie": owner_a_cookie},
    )
    assert status_code == 200
    job_a_id = body["data"]["job_id"]

    _register_resume_version(owner_a_id, RESUME_A_ID, "resume_a_v1")
    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_A_ID, "job_id": job_a_id, "resume_version_id": "resume_a_v1"},
        headers={"cookie": owner_b_cookie},
    )
    assert status_code in {404, 403, 422}


def test_owner_scope_prevents_user_b_binding_user_a_resume_to_user_b_job() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_a_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_b_cookie = _login_cookie(app, "user_b", USER_B_PASSWORD)
    owner_a_id = _current_owner_id(app, owner_a_cookie)
    owner_b_id = _current_owner_id(app, owner_b_cookie)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={"title": "Owner A Job", "responsibilities": ["Plan"], "requirements": ["Security"]},
        headers={"cookie": owner_a_cookie},
    )
    assert status_code == 200
    job_a_id = body["data"]["job_id"]
    _register_resume_version(owner_a_id, RESUME_A_ID, "resume_a_v1")

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={"title": "Owner B Job", "responsibilities": ["Build"], "requirements": ["Go"]},
        headers={"cookie": owner_b_cookie},
    )
    assert status_code == 200
    job_b_id = body["data"]["job_id"]
    _register_resume_version(owner_b_id, RESUME_B_ID, "resume_b_v1")

    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_A_ID, "job_id": job_b_id, "resume_version_id": "resume_a_v1"},
        headers={"cookie": owner_b_cookie},
    )
    assert status_code == 422
    assert body["error"]["code"] in {"validation_failed", "not_found_or_inaccessible"}


def test_owner_scope_prevents_user_b_unbinding_user_a_binding() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_a_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_a_id = _current_owner_id(app, owner_a_cookie)
    owner_b_cookie = _login_cookie(app, "user_b", USER_B_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={"title": "Owner A Job", "responsibilities": ["Plan"], "requirements": ["Security"]},
        headers={"cookie": owner_a_cookie},
    )
    assert status_code == 200
    job_a_id = body["data"]["job_id"]
    _register_resume_version(owner_a_id, RESUME_A_ID, "resume_a_v1")

    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_A_ID, "job_id": job_a_id, "resume_version_id": "resume_a_v1"},
        headers={"cookie": owner_a_cookie},
    )
    assert status_code == 200
    binding_id = body["data"]["resume_job_binding_id"]

    status_code, body = call_json(
        app,
        f"/api/v1/resume-job-bindings/{binding_id}",
        "DELETE",
        json_body={},
        headers={"cookie": owner_b_cookie},
    )
    assert status_code in {404, 403}
    assert body["error"]["code"] in {"not_found_or_inaccessible", "permission_denied"}


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
