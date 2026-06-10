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

USER_B_ID = stable_resource_id(ResourceIdPrefix.USER, "user_b@example.com")
USER_A_PASSWORD = "password-a"
USER_B_PASSWORD = "password-b"
RESUME_ID = "resume_42"


def test_binding_creation_uses_current_resume_and_job_versions() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Frontend Engineer",
            "responsibilities": ["Build UI"],
            "requirements": ["React"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]
    job_version_id = body["data"]["current_version_ref"]["version_id"]

    _register_resume_version(owner_id, RESUME_ID, "resume_ver_001")

    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_ID, "job_id": job_id},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["resource_type"] == "job_resume_binding"
    assert body["data"]["binding_status"] == "active"
    assert body["data"]["resume_ref"]["version_id"] == "resume_ver_001"
    assert body["data"]["job_ref"]["version_id"] == job_version_id
    assert body["data"]["record_version"] == 1


def test_binding_create_duplicate_active_binding_is_idempotent() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "QA Engineer",
            "responsibilities": ["Review"],
            "requirements": ["Testing"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]
    _register_resume_version(owner_id, RESUME_ID, "resume_ver_002")

    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_ID, "job_id": job_id},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    first_binding_id = body["data"]["resume_job_binding_id"]

    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_ID, "job_id": job_id},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["data"]["resume_job_binding_id"] == first_binding_id
    assert body["data"]["binding_status"] == "active"


def test_binding_create_conflict_when_active_binding_differs_by_version() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Ops Engineer",
            "responsibilities": ["Deploy"],
            "requirements": ["Kubernetes"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]

    _register_resume_version(owner_id, RESUME_ID, "resume_ver_010")
    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_ID, "job_id": job_id, "resume_version_id": "resume_ver_010"},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200

    _register_resume_version(owner_id, RESUME_ID, "resume_ver_011")
    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_ID, "job_id": job_id},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 409
    assert body["error"]["code"] in {"idempotency_conflict", "stale_version_conflict"}


def test_binding_delete_unbinds_without_deleting_history() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Mobile Engineer",
            "responsibilities": ["Ship"],
            "requirements": ["Swift"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]
    _register_resume_version(owner_id, RESUME_ID, "resume_ver_100")

    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_ID, "job_id": job_id},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    binding_id = body["data"]["resume_job_binding_id"]

    status_code, body = call_json(
        app,
        f"/api/v1/resume-job-bindings/{binding_id}",
        "DELETE",
        json_body={},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["data"]["binding_status"] == "unbound"
    assert body["data"]["unbound_at"] is not None
    assert body["data"]["unbound_by"] == {"owner_id": owner_id}

    # The endpoint has no binding-list filter; inspect repository directly to ensure history stays.
    repository = SqlAlchemyBindingRepository()
    history = repository.list_by_owner(owner_id)
    assert len(history) == 1
    assert history[0].binding_id == binding_id
    assert history[0].status == "unbound"


def test_binding_delete_stale_base_version_returns_conflict_and_preserves_active_binding() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Backend Engineer",
            "responsibilities": ["Build services"],
            "requirements": ["Python"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]
    _register_resume_version(owner_id, RESUME_ID, "resume_ver_150")

    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_ID, "job_id": job_id},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    binding_id = body["data"]["resume_job_binding_id"]
    record_version = body["data"]["record_version"]

    status_code, body = call_json(
        app,
        f"/api/v1/resume-job-bindings/{binding_id}",
        "DELETE",
        json_body={
            "base_version_ref": {
                "resource_type": "resume_job_binding",
                "resource_id": binding_id,
                "version_id": str(record_version - 1),
            },
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 409
    assert body["error"]["code"] == "stale_version_conflict"

    repository = SqlAlchemyBindingRepository()
    history = repository.list_by_owner(owner_id)
    assert len(history) == 1
    assert history[0].binding_id == binding_id
    assert history[0].status == "active"
    assert history[0].record_version == record_version

    status_code, body = call_json(
        app,
        f"/api/v1/resume-job-bindings/{binding_id}",
        "DELETE",
        json_body={"record_version": record_version},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["data"]["binding_status"] == "unbound"
    assert body["data"]["record_version"] == record_version + 1


def test_binding_owner_scope_for_cross_owner_create_and_delete() -> None:
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
        json_body={
            "title": "Security Engineer",
            "responsibilities": ["Review access"],
            "requirements": ["IAM"],
        },
        headers={"cookie": owner_a_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]

    _register_resume_version(owner_b_id, "resume_b_private", "resume_b_ver_001")
    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={
            "resume_id": "resume_b_private",
            "job_id": job_id,
            "resume_version_id": "resume_b_ver_001",
        },
        headers={"cookie": owner_a_cookie},
    )
    assert status_code == 422
    assert body["error"]["code"] == "validation_failed"

    _register_resume_version(owner_a_id, RESUME_ID, "resume_ver_300")
    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_ID, "job_id": job_id},
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
    assert status_code == 404
    assert body["error"]["code"] == "not_found_or_inaccessible"

    repository = SqlAlchemyBindingRepository()
    history = repository.list_by_owner(owner_a_id)
    assert len(history) == 1
    assert history[0].binding_id == binding_id
    assert history[0].status == "active"


def test_binding_validation_error_without_required_fields() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"job_id": "job_001"},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 422
    assert "detail" in body
    detail = body["detail"]
    assert isinstance(detail, list)
    assert any(
        entry["type"] == "missing" and "resume_id" in entry["loc"] for entry in detail
    )


def test_job_binding_summary_reflects_binding_state() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    status_code, body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Platform Lead",
            "responsibilities": ["Operate"],
            "requirements": ["Distributed systems"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = body["data"]["job_id"]

    status_code, body = call_json(app, "/api/v1/jobs", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert body["data"][0]["binding_summary"]["status"] == "not_bound"

    _register_resume_version(owner_id, RESUME_ID, "resume_ver_200")
    status_code, body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={"resume_id": RESUME_ID, "job_id": job_id},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    binding_id = body["data"]["resume_job_binding_id"]

    status_code, body = call_json(app, "/api/v1/jobs", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert body["data"][0]["binding_summary"]["status"] == "bound"
    assert body["data"][0]["binding_summary"]["resume_id"] == RESUME_ID

    status_code, body = call_json(
        app,
        f"/api/v1/jobs/{job_id}",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["data"]["binding_summary"]["status"] == "bound"
    assert body["data"]["binding_summary"]["resume_job_binding_id"] == binding_id

    status_code, body = call_json(
        app,
        f"/api/v1/resume-job-bindings/{binding_id}",
        "DELETE",
        json_body={},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200

    status_code, body = call_json(app, "/api/v1/jobs", headers={"cookie": owner_cookie})
    assert status_code == 200
    assert body["data"][0]["binding_summary"]["status"] == "not_bound"


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
    return create_app(auth_runtime=runtime, initialize_schema=True)


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
