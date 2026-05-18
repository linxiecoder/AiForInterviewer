from __future__ import annotations

from http.cookies import SimpleCookie
from json import dumps
from typing import Any
import pytest

from app.infrastructure.security.auth import AuthRuntimeSettings, build_auth_runtime
from app.main import create_app
from tests.api.asgi_client import call_json, call_json_response


TEST_PASSWORD = "test-password"
ENV_PASSWORD = "env-test-password"


def test_login_success_with_env_configured_dev_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_AUTH_DEV_USER_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_DEV_USER_IDENTIFIER", "developer")
    monkeypatch.setenv("API_AUTH_DEV_USER_EMAIL", "developer@example.com")
    monkeypatch.setenv("API_AUTH_DEV_USER_USERNAME", "developer")
    monkeypatch.setenv("API_AUTH_DEV_USER_DISPLAY_NAME", "F5 Dev User")
    monkeypatch.setenv("API_AUTH_DEV_USER_PASSWORD", ENV_PASSWORD)
    app = create_app()

    status_code, body, headers = call_json_response(
        app,
        "/api/v1/auth/login",
        "POST",
        json_body={"identifier": "developer", "password": ENV_PASSWORD},
    )

    set_cookie = _single_set_cookie(headers)
    assert status_code == 200
    assert body["resource_type"] == "current_user"
    assert body["data"]["email"] == "developer@example.com"
    assert "aifi_session=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Path=/api/v1" in set_cookie
    assert "Secure" not in set_cookie
    _assert_no_sensitive_auth_fields(body)


def test_login_fails_when_env_password_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_AUTH_DEV_USER_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_DEV_USER_IDENTIFIER", "developer")
    monkeypatch.setenv("API_AUTH_DEV_USER_EMAIL", "developer@example.com")
    monkeypatch.setenv("API_AUTH_DEV_USER_USERNAME", "developer")
    monkeypatch.setenv("API_AUTH_DEV_USER_DISPLAY_NAME", "F5 Dev User")
    monkeypatch.delenv("API_AUTH_DEV_USER_PASSWORD", raising=False)
    app = create_app()

    status_code, body = call_json(
        app,
        "/api/v1/auth/login",
        "POST",
        json_body={"identifier": "developer", "password": "any-password"},
    )

    assert status_code == 401
    assert body["error"]["code"] == "unauthenticated"
    assert body["error"]["user_action"] == "login"


def test_prod_like_env_defaults_to_no_dev_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_ENV", "production")
    monkeypatch.setenv("API_AUTH_ENV", "production")
    monkeypatch.delenv("API_AUTH_DEV_USER_ENABLED", raising=False)
    monkeypatch.setenv("API_AUTH_DEV_USER_PASSWORD", "should-not-be-used")
    app = create_app()

    status_code, body = call_json(
        app,
        "/api/v1/auth/login",
        "POST",
        json_body={"identifier": "developer", "password": "should-not-be-used"},
    )

    assert status_code == 401
    assert body["error"]["code"] == "unauthenticated"
    assert body["error"]["user_action"] == "login"


def test_login_success_sets_httponly_cookie() -> None:
    app = _auth_app()

    status_code, body, headers = call_json_response(
        app,
        "/api/v1/auth/login",
        "POST",
        json_body={"identifier": "developer@example.com", "password": TEST_PASSWORD},
    )

    set_cookie = _single_set_cookie(headers)
    assert status_code == 200
    assert body["resource_type"] == "current_user"
    assert body["data"]["email"] == "developer@example.com"
    assert "aifi_session=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Path=/api/v1" in set_cookie
    assert "Secure" not in set_cookie
    _assert_no_sensitive_auth_fields(body)


def test_wrong_password_returns_401_error_envelope() -> None:
    app = _auth_app()

    status_code, body = call_json(
        app,
        "/api/v1/auth/login",
        "POST",
        json_body={"identifier": "developer@example.com", "password": "wrong"},
    )

    assert status_code == 401
    assert body["error"]["code"] == "unauthenticated"
    assert body["error"]["user_action"] == "login"
    _assert_no_sensitive_auth_fields(body)


def test_me_without_cookie_returns_401() -> None:
    app = _auth_app()

    status_code, body = call_json(app, "/api/v1/auth/me")

    assert status_code == 401
    assert body["error"]["code"] == "unauthenticated"


def test_me_with_cookie_returns_user_summary() -> None:
    app = _auth_app()
    session_cookie = _login_cookie(app)

    status_code, body = call_json(app, "/api/v1/auth/me", headers={"cookie": session_cookie})

    assert status_code == 200
    assert body["data"]["user_id"].startswith("usr_")
    assert body["data"]["owner_id"] == body["data"]["user_id"]
    assert body["data"]["roles"] == ["user"]
    _assert_no_sensitive_auth_fields(body)


def test_logout_clears_cookie() -> None:
    app = _auth_app()
    session_cookie = _login_cookie(app)

    status_code, body, headers = call_json_response(
        app,
        "/api/v1/auth/logout",
        "POST",
        headers={"cookie": session_cookie},
    )

    set_cookie = _single_set_cookie(headers)
    assert status_code == 200
    assert body["data"] == {"logged_out": True}
    assert "aifi_session=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "Path=/api/v1" in set_cookie
    assert "SameSite=lax" in set_cookie

    status_code_after_logout, body_after_logout = call_json(
        app,
        "/api/v1/auth/me",
        headers={"cookie": session_cookie},
    )
    assert status_code_after_logout == 401
    assert body_after_logout["error"]["code"] == "unauthenticated"


def test_auth_session_endpoint_is_not_implemented() -> None:
    app = _auth_app()

    status_code, _body = call_json(app, "/api/v1/auth/session")

    assert status_code == 404


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
    set_cookie = _single_set_cookie(headers)
    cookie = SimpleCookie()
    cookie.load(set_cookie)
    return f"aifi_session={cookie['aifi_session'].value}"


def _single_set_cookie(headers: dict[str, list[str]]) -> str:
    values = headers.get("set-cookie", [])
    assert len(values) == 1
    return values[0]


def _assert_no_sensitive_auth_fields(body: dict[str, Any]) -> None:
    serialized = dumps(body, ensure_ascii=False)
    forbidden = {
        "session_id",
        "session_digest",
        "session_token",
        "password_hash",
        "salt",
        TEST_PASSWORD,
    }
    for item in forbidden:
        assert item not in serialized
