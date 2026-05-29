from __future__ import annotations

from sqlalchemy import text

from app.application.bindings.commands import RegisterResumeVersionCommand
from app.application.bindings.use_cases import BindingUseCases
from app.domain.resumes.entities import Resume
from app.domain.shared.clock import utc_now
from app.domain.shared.ids import ResourceIdPrefix, stable_resource_id
from app.domain.shared.refs import OwnerRef, VersionRef
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.infrastructure.db.session import get_session_factory
from app.infrastructure.security.auth import AuthRuntimeSettings, build_auth_runtime
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.main import create_app
from tests.api.asgi_client import call_json, call_json_response

USER_A_ID = stable_resource_id(ResourceIdPrefix.USER, "user_a@example.com")
USER_B_ID = stable_resource_id(ResourceIdPrefix.USER, "user_b@example.com")
USER_A_PASSWORD = "password-a"
USER_B_PASSWORD = "password-b"


def test_list_resumes_returns_owner_scoped_and_required_fields() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_id = _current_owner_id(app, owner_cookie)

    _seed_resume(owner_id=owner_id, resume_id="resume_a", version_id="resume_a_v1", title="简历 A")
    _seed_resume(owner_id=owner_id, resume_id="resume_a_secondary", version_id="resume_a_v2", title="简历 A2")

    status_code, body = call_json(
        app,
        "/api/v1/resumes",
        "GET",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["resource_type"] == "resume_list"

    resume_list = body["data"]
    assert len(resume_list) == 2
    assert all(item["current_version_ref"]["resource_type"] == "resume" for item in resume_list)
    assert set(item["resume_id"] for item in resume_list) == {"resume_a", "resume_a_secondary"}

    resume = resume_list[0]
    assert isinstance(resume["current_version_ref"], dict)
    assert resume["current_version_ref"]["resource_id"]
    assert "resume_id" in resume
    assert "status" in resume
    assert "created_at" in resume
    assert "updated_at" in resume
    assert "title" in resume


def test_list_resumes_returns_empty_when_no_resume() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/resumes",
        "GET",
        headers={"cookie": owner_cookie},
    )
    assert status_code == 200
    assert body["resource_type"] == "resume_list"
    assert body["data"] == []


def test_create_resume_returns_created_summary_and_owner_scoped_list() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_a_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_b_cookie = _login_cookie(app, "user_b", USER_B_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/resumes",
        "POST",
        json_body={
            "title": "前端工程师简历",
            "markdown_text": "# 前端工程师\n\n- React\n- TypeScript",
        },
        headers={"cookie": owner_a_cookie},
    )

    assert status_code == 201
    assert body["resource_type"] == "resume_detail"
    created = body["data"]
    assert created["resume_id"].startswith("res_")
    assert created["title"] == "前端工程师简历"
    assert created["status"] == "active"
    assert created["current_version_ref"]["resource_type"] == "resume"
    assert created["current_version_ref"]["resource_id"] == created["resume_id"]
    assert created["current_version_ref"]["version_id"].startswith("res_")

    owner_a_status_code, owner_a_body = call_json(
        app,
        "/api/v1/resumes",
        "GET",
        headers={"cookie": owner_a_cookie},
    )
    assert owner_a_status_code == 200
    assert [item["resume_id"] for item in owner_a_body["data"]] == [created["resume_id"]]

    owner_b_status_code, owner_b_body = call_json(
        app,
        "/api/v1/resumes",
        "GET",
        headers={"cookie": owner_b_cookie},
    )
    assert owner_b_status_code == 200
    assert owner_b_body["data"] == []


def test_create_resume_rejects_blank_content() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/resumes",
        "POST",
        json_body={"title": "空白简历", "markdown_text": "   "},
        headers={"cookie": owner_cookie},
    )

    assert status_code == 422
    assert body["error"]["code"] == "validation_failed"


def test_update_resume_creates_new_version_and_returns_detail() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/resumes",
        "POST",
        json_body={
            "title": "旧简历",
            "markdown_text": "# 旧内容",
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 201
    created = body["data"]
    resume_id = created["resume_id"]
    old_version_id = created["current_version_ref"]["version_id"]

    detail_status, detail_body = call_json(
        app,
        f"/api/v1/resumes/{resume_id}",
        "GET",
        headers={"cookie": owner_cookie},
    )
    assert detail_status == 200
    assert detail_body["data"]["markdown_text"] == "# 旧内容"

    update_status, update_body = call_json(
        app,
        f"/api/v1/resumes/{resume_id}",
        "PATCH",
        json_body={
            "title": "更新后的简历",
            "markdown_text": "# 新内容\n\n- TypeScript",
            "base_version_ref": created["current_version_ref"],
        },
        headers={"cookie": owner_cookie},
    )
    assert update_status == 200
    assert update_body["resource_type"] == "resume_detail"
    updated = update_body["data"]
    assert updated["resume_id"] == resume_id
    assert updated["title"] == "更新后的简历"
    assert updated["markdown_text"] == "# 新内容\n\n- TypeScript"
    assert updated["current_version_ref"]["version_id"] != old_version_id

    list_status, list_body = call_json(
        app,
        "/api/v1/resumes",
        "GET",
        headers={"cookie": owner_cookie},
    )
    assert list_status == 200
    assert list_body["data"][0]["title"] == "更新后的简历"
    assert list_body["data"][0]["current_version_ref"]["version_id"] == updated["current_version_ref"]["version_id"]


def test_resume_delete_soft_deletes_without_physical_delete() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)

    status_code, body = call_json(
        app,
        "/api/v1/resumes",
        "POST",
        json_body={
            "title": "待删除简历",
            "markdown_text": "# 待删除\n\n- Python",
        },
        headers={"cookie": owner_cookie},
    )
    assert status_code == 201
    resume_id = body["data"]["resume_id"]
    version_id = body["data"]["current_version_ref"]["version_id"]

    delete_status, delete_body = call_json(
        app,
        f"/api/v1/resumes/{resume_id}",
        "DELETE",
        headers={"cookie": owner_cookie},
    )
    assert delete_status == 200
    assert delete_body["data"]["status"] == "deleted"

    list_status, list_body = call_json(app, "/api/v1/resumes", headers={"cookie": owner_cookie})
    assert list_status == 200
    assert list_body["data"] == []

    detail_status, detail_body = call_json(app, f"/api/v1/resumes/{resume_id}", headers={"cookie": owner_cookie})
    assert detail_status == 404
    assert detail_body["error"]["code"] == "not_found_or_inaccessible"

    assert _record_status("resumes", resume_id) == "deleted"
    assert _record_count("resumes", resume_id) == 1
    assert _record_count("resume_versions", version_id) == 1

    repeat_status, repeat_body = call_json(
        app,
        f"/api/v1/resumes/{resume_id}",
        "DELETE",
        headers={"cookie": owner_cookie},
    )
    assert repeat_status == 404
    assert repeat_body["error"]["code"] == "not_found_or_inaccessible"


def test_user_b_cannot_list_user_a_resumes() -> None:
    app = _app_with_two_users()
    _reset_repositories()
    owner_a_cookie = _login_cookie(app, "user_a@example.com", USER_A_PASSWORD)
    owner_b_cookie = _login_cookie(app, "user_b", USER_B_PASSWORD)
    owner_a_id = _current_owner_id(app, owner_a_cookie)

    _seed_resume(owner_id=owner_a_id, resume_id="resume_a_only", version_id="resume_a_v1", title="跨用户简历")

    owner_b_status_code, owner_b_body = call_json(
        app,
        "/api/v1/resumes",
        "GET",
        headers={"cookie": owner_b_cookie},
    )
    assert owner_b_status_code == 200
    assert owner_b_body["data"] == []

    owner_a_status_code, owner_a_body = call_json(
        app,
        "/api/v1/resumes",
        "GET",
        headers={"cookie": owner_a_cookie},
    )
    assert owner_a_status_code == 200
    assert len(owner_a_body["data"]) == 1
    assert owner_a_body["data"][0]["resume_id"] == "resume_a_only"


def test_list_resumes_unauthenticated() -> None:
    app = _app_with_two_users()
    _reset_repositories()

    status_code, body = call_json(app, "/api/v1/resumes", "GET")
    assert status_code == 401
    assert body["error"]["code"] in {"unauthenticated", "unauthenticated_required"}


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
    repo = SqlAlchemyBindingRepository()
    repo.register_resume(owner_id=owner_id, resume_id=resume_id, resume_version_id=version_id)


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


def _record_count(table_name: str, record_id: str) -> int:
    session_factory = get_session_factory()
    with session_factory() as session:
        return int(
            session.execute(
                text(f"SELECT COUNT(*) FROM {table_name} WHERE id = :record_id"),
                {"record_id": record_id},
            ).scalar_one()
        )


def _record_status(table_name: str, record_id: str) -> str | None:
    session_factory = get_session_factory()
    with session_factory() as session:
        return session.execute(
            text(f"SELECT status FROM {table_name} WHERE id = :record_id"),
            {"record_id": record_id},
        ).scalar_one_or_none()
