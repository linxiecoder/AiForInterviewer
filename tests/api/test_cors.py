from app.main import create_app
from app.infrastructure.security.auth import AuthRuntimeSettings, build_auth_runtime
import pytest
import json
import asyncio
from typing import Any
from tests.api.asgi_client import call_json_response


ALLOWED_LOCAL_ORIGIN = "http://127.0.0.1:5174"
DISALLOWED_ORIGIN = "http://127.0.0.1:9000"
LOCAL_TEST_PASSWORD = "cors-password"


def _auth_app() -> object:
    runtime = build_auth_runtime(
        AuthRuntimeSettings(
            dev_user_password=LOCAL_TEST_PASSWORD,
            dev_user_identifier="developer",
            dev_user_email="developer@example.com",
            dev_username="developer",
            dev_display_name="F5 Dev User",
            seed_dev_user=True,
        ),
        cookie_path="/api/v1",
    )
    return create_app(auth_runtime=runtime)


def _header_values(headers: dict[str, list[str]], key: str) -> list[str]:
    return headers.get(key.lower(), [])


def _preflight_headers(origin: str, method: str = "POST") -> dict[str, str]:
    return {
        "Origin": origin,
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": "content-type,authorization",
    }


def _assert_allow_credentials(headers: dict[str, list[str]]) -> None:
    assert _header_values(headers, "access-control-allow-credentials") == ["true"]


def test_cors_preflight_returns_allow_origin_for_local_allowlist() -> None:
    app = _auth_app()

    status_code, _body, headers = call_raw_response(
        app,
        "/api/v1/auth/login",
        "OPTIONS",
        headers=_preflight_headers(ALLOWED_LOCAL_ORIGIN),
    )

    assert status_code in {200, 204}
    assert _header_values(headers, "access-control-allow-origin") == [ALLOWED_LOCAL_ORIGIN]
    _assert_allow_credentials(headers)
    assert "GET" in _allowed_methods(headers)
    assert "POST" in _allowed_methods(headers)
    assert "OPTIONS" in _allowed_methods(headers)


def test_cors_preflight_includes_expected_headers() -> None:
    app = _auth_app()

    status_code, _body, headers = call_raw_response(
        app,
        "/api/v1/auth/login",
        "OPTIONS",
        headers=_preflight_headers(ALLOWED_LOCAL_ORIGIN),
    )

    assert status_code in {200, 204}
    allowed_headers = _header_values(headers, "access-control-allow-headers")
    header_csv = allowed_headers[0] if allowed_headers else ""
    normalized_headers = {h.strip().lower() for h in header_csv.split(",") if h.strip()}
    assert {"content-type", "accept", "authorization"}.issubset(normalized_headers)


def test_disallowed_origin_is_not_granted_cors() -> None:
    app = _auth_app()

    status_code, _body, headers = call_json_response(
        app,
        "/api/v1/auth/login",
        "POST",
        json_body={"identifier": "developer", "password": LOCAL_TEST_PASSWORD},
        headers={
            "Origin": DISALLOWED_ORIGIN,
            "Content-Type": "application/json",
        },
    )

    assert status_code == 200
    assert _header_values(headers, "access-control-allow-origin") == []


def test_prod_like_env_without_cors_var_keeps_cors_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_ENV", "production")
    monkeypatch.setenv("API_AUTH_ENV", "production")
    monkeypatch.delenv("API_CORS_ALLOW_ORIGINS", raising=False)
    app = create_app()

    status_code, _body, headers = call_raw_response(
        app,
        "/api/v1/auth/login",
        "OPTIONS",
        headers=_preflight_headers(ALLOWED_LOCAL_ORIGIN),
    )

    assert status_code in {200, 400, 405}
    assert _header_values(headers, "access-control-allow-origin") == []


def test_auth_route_uses_envelope_and_cookie_with_allowed_origin() -> None:
    app = _auth_app()

    status_code, body, headers = call_json_response(
        app,
        "/api/v1/auth/login",
        "POST",
        json_body={"identifier": "developer", "password": LOCAL_TEST_PASSWORD},
        headers={
            "Origin": ALLOWED_LOCAL_ORIGIN,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    set_cookie = _header_values(headers, "set-cookie")[0]
    assert status_code == 200
    assert body["resource_type"] == "current_user"
    assert body["data"]["email"] == "developer@example.com"
    assert "aifi_session=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Path=/api/v1" in set_cookie
    _assert_allow_credentials(headers)
    assert _header_values(headers, "access-control-allow-origin") == [ALLOWED_LOCAL_ORIGIN]
    assert "session_token" not in str(body)


def _allowed_methods(headers: dict[str, list[str]]) -> set[str]:
    method_values = _header_values(headers, "access-control-allow-methods")
    methods_csv = ";".join(method_values)
    return {method.strip().upper() for method in methods_csv.replace(";", ",").split(",") if method.strip()}


def call_raw_response(
    app: Any,
    path: str,
    method: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
) -> tuple[int, str, dict[str, list[str]]]:
    return asyncio.run(
        _raw_asgi_call(
            app,
            path,
            method,
            headers=headers or {},
            json_body=json_body,
        )
    )


async def _raw_asgi_call(
    app: Any,
    path: str,
    method: str,
    *,
    headers: dict[str, str],
    json_body: dict[str, Any] | None,
) -> tuple[int, str, dict[str, list[str]]]:
    messages: list[dict[str, Any]] = []
    request_body = b""
    request_sent = False
    request_headers = [
        (key.lower().encode("ascii"), value.encode("latin-1"))
        for key, value in headers.items()
    ]
    if json_body is not None:
        request_body = json.dumps(json_body).encode("utf-8")
        request_headers.append((b"content-type", b"application/json"))
        request_headers.append((b"content-length", str(len(request_body)).encode("ascii")))

    async def receive() -> dict[str, Any]:
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}
        request_sent = True
        return {"type": "http.request", "body": request_body, "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": request_headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        },
        receive,
        send,
    )

    response_start = next(message for message in messages if message["type"] == "http.response.start")
    status = response_start["status"]
    response_headers: dict[str, list[str]] = {}
    for key, value in response_start.get("headers", []):
        response_headers.setdefault(key.decode("latin-1").lower(), []).append(value.decode("latin-1"))
    body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
    return status, body.decode("utf-8"), response_headers
