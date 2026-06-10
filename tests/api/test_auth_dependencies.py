from fastapi import Depends

from app.api.deps import optional_actor, owner_scope_for_actor, require_authenticated_actor
from app.infrastructure.security.auth import AuthRuntimeSettings, build_auth_runtime
from app.main import create_app
from tests.api.asgi_client import call_json, call_json_response


TEST_PASSWORD = "dependency-test-password"


def test_auth_dependency_can_produce_current_actor() -> None:
    app = _auth_app()

    @app.get("/probe/current-actor")
    async def probe(actor=Depends(require_authenticated_actor)):
        return {
            "actor_id": actor.actor_id,
            "owner_id": actor.owner_id,
            "scope_owner_id": owner_scope_for_actor(actor).owner_id,
        }

    session_cookie = _login_cookie(app)
    status_code, body = call_json(app, "/probe/current-actor", headers={"cookie": session_cookie})

    assert status_code == 200
    assert body["actor_id"].startswith("usr_")
    assert body["owner_id"] == body["actor_id"]
    assert body["scope_owner_id"] == body["actor_id"]


def test_optional_actor_returns_none_without_cookie() -> None:
    app = _auth_app()

    @app.get("/probe/optional-actor")
    async def probe(actor=Depends(optional_actor)):
        return {"has_actor": actor is not None}

    status_code, body = call_json(app, "/probe/optional-actor")

    assert status_code == 200
    assert body == {"has_actor": False}


def test_optional_actor_returns_none_with_invalid_cookie() -> None:
    app = _auth_app()

    @app.get("/probe/optional-actor-invalid-cookie")
    async def probe(actor=Depends(optional_actor)):
        return {"has_actor": actor is not None}

    status_code, body = call_json(
        app,
        "/probe/optional-actor-invalid-cookie",
        headers={"cookie": "aifi_session=invalid-token"},
    )

    assert status_code == 200
    assert body == {"has_actor": False}


def test_required_actor_without_cookie_returns_error_envelope() -> None:
    app = _auth_app()

    @app.get("/probe/required-actor")
    async def probe(_actor=Depends(require_authenticated_actor)):
        return {"ok": True}

    status_code, body = call_json(app, "/probe/required-actor")

    assert status_code == 401
    assert body["error"]["code"] == "unauthenticated"


def test_required_actor_with_invalid_cookie_returns_error_envelope() -> None:
    app = _auth_app()

    @app.get("/probe/required-actor-invalid-cookie")
    async def probe(_actor=Depends(require_authenticated_actor)):
        return {"ok": True}

    status_code, body, headers = call_json_response(
        app,
        "/probe/required-actor-invalid-cookie",
        headers={"cookie": "aifi_session=invalid-token"},
    )

    assert status_code == 401
    assert body["error"]["code"] == "unauthenticated"
    assert body["error"]["user_action"] == "login"
    assert headers.get("set-cookie", []) == []


def _auth_app():
    runtime = build_auth_runtime(
        AuthRuntimeSettings(dev_user_password=TEST_PASSWORD),
        cookie_path="/api/v1",
    )
    return create_app(auth_runtime=runtime)


def _login_cookie(app) -> str:
    status_code, body, headers = call_json_response(
        app,
        "/api/v1/auth/login",
        "POST",
        json_body={"identifier": "developer", "password": TEST_PASSWORD},
    )
    assert status_code == 200, body
    set_cookie = headers["set-cookie"][0]
    token = set_cookie.split("aifi_session=", 1)[1].split(";", 1)[0]
    return f"aifi_session={token}"
