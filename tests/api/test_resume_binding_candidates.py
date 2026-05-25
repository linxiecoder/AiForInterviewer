from __future__ import annotations

from app.domain.resumes.entities import Resume
from app.domain.shared.clock import utc_now
from app.domain.shared.ids import ResourceIdPrefix, stable_resource_id
from app.domain.shared.refs import OwnerRef, VersionRef
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.infrastructure.security.auth import AuthRuntimeSettings, build_auth_runtime
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.main import create_app
from tests.api.asgi_client import call_json, call_json_response

USER_A_ID = stable_resource_id(ResourceIdPrefix.USER, "user_a@example.com")
USER_B_ID = stable_resource_id(ResourceIdPrefix.USER, "user_b@example.com")
USER_A_PASSWORD = "password-a"
USER_B_PASSWORD = "password-b"


def test_resume_candidates_support_binding_and_refresh_job_summary() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    status_code, create_job_body = call_json(
        app,
        "/api/v1/jobs",
        "POST",
        json_body={
            "title": "Candidate Binding Round",
            "responsibilities": ["Read CV"],
            "requirements": ["Strong communication"],
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_id = create_job_body["data"]["job_id"]

    _seed_resume(owner_id=owner_id, resume_id="resume_candidate", version_id="resume_candidate_v1", title="候选简历")

    status_code, list_body = call_json(
        app,
        "/api/v1/resumes",
        "GET",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    resume_items = list_body["data"]
    assert resume_items
    assert resume_items[0]["resume_id"] == "resume_candidate"

    status_code, create_binding_body = call_json(
        app,
        "/api/v1/resume-job-bindings",
        "POST",
        json_body={
            "resume_id": "resume_candidate",
            "job_id": job_id,
            "resume_version_id": "resume_candidate_v1",
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert create_binding_body["data"]["binding_status"] == "active"
    binding_id = create_binding_body["data"]["resume_job_binding_id"]

    status_code, job_detail_after_bind_body = call_json(
        app,
        f"/api/v1/jobs/{job_id}",
        "GET",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    job_binding_summary = job_detail_after_bind_body["data"]["binding_summary"]
    assert job_binding_summary["status"] == "bound"
    assert job_binding_summary["resume_id"] == "resume_candidate"
    assert job_binding_summary["resume_version_ref"] == {
        "resource_type": "resume",
        "resource_id": "resume_candidate",
        "version_id": "resume_candidate_v1",
    }

    status_code, list_body_after_bind = call_json(
        app,
        "/api/v1/jobs",
        "GET",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert list_body_after_bind["data"][0]["binding_summary"]["status"] == "bound"
    assert list_body_after_bind["data"][0]["binding_summary"]["resume_id"] == "resume_candidate"

    status_code, unbind_body = call_json(
        app,
        f"/api/v1/resume-job-bindings/{binding_id}",
        "DELETE",
        json_body={},
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert unbind_body["data"]["binding_status"] == "unbound"

    status_code, job_detail_after_unbind_body = call_json(
        app,
        f"/api/v1/jobs/{job_id}",
        "GET",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert job_detail_after_unbind_body["data"]["binding_summary"]["status"] == "not_bound"

    status_code, list_body_after_unbind = call_json(
        app,
        "/api/v1/jobs",
        "GET",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert list_body_after_unbind["data"][0]["binding_summary"]["status"] == "not_bound"


def _seed_resume(*, owner_id: str, resume_id: str, version_id: str, title: str = "简历") -> None:
    repo = SqlAlchemyResumeRepository()
    repo.add(
        Resume(
            resume_id=resume_id,
            owner_ref=OwnerRef(owner_id=owner_id),
            current_version_ref=VersionRef(
                resource_type="resume",
                resource_id=resume_id,
                version_id=version_id,
            ),
            status="active",
            title=title,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
    )
    binding_repo = SqlAlchemyBindingRepository()
    binding_repo.register_resume(
        owner_id=owner_id,
        resume_id=resume_id,
        resume_version_id=version_id,
    )


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


def _reset_repositories() -> None:
    SqlAlchemyJobRepository.clear_state()
    SqlAlchemyBindingRepository.clear_state()
    SqlAlchemyResumeRepository.clear_state()
