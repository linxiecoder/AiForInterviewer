import json
import logging
import re

from app.infrastructure.security.auth import AuthRuntimeSettings, build_auth_runtime
from app.main import create_app
from tests.api.asgi_client import call_json_response


LOCAL_TEST_PASSWORD = "local-password"


def test_access_log_uses_beijing_time_and_shared_trace_headers(caplog) -> None:
    app = create_app()

    with caplog.at_level(logging.INFO, logger="app.http.access"):
        status_code, body, headers = call_json_response(
            app,
            "/api/v1/health?api_key=secret-value",
            headers={"X-Request-ID": "req-from-client", "X-Trace-ID": "trace-from-client"},
        )

    assert status_code == 200
    assert body == {"status": "ok"}
    assert headers["x-request-id"] == ["req-from-client"]
    assert headers["x-trace-id"] == ["trace-from-client"]

    record = _single_access_log(caplog)
    assert record["event"] == "http_access"
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}\+08:00", record["occurred_at"])
    assert record["request_id"] == "req-from-client"
    assert record["trace_id"] == "trace-from-client"
    assert record["method"] == "GET"
    assert record["path"] == "/api/v1/health"
    assert record["query"] == {"api_key": "***"}
    assert record["status_code"] == 200
    assert record["response_body"] == {"status": "ok"}
    assert isinstance(record["duration_ms"], float)
    assert record["client"] == {"host": "testclient", "port": 50000}


def test_access_log_redacts_request_body_and_matches_success_envelope(caplog) -> None:
    app = create_app(auth_runtime=_auth_runtime())

    with caplog.at_level(logging.INFO, logger="app.http.access"):
        status_code, body, headers = call_json_response(
            app,
            "/api/v1/auth/login",
            "POST",
            json_body={"identifier": "developer", "password": LOCAL_TEST_PASSWORD},
        )

    assert status_code == 200
    record = _single_access_log(caplog)
    assert headers["x-request-id"] == [body["request_id"]]
    assert headers["x-trace-id"] == [body["trace_id"]]
    assert record["request_id"] == body["request_id"]
    assert record["trace_id"] == body["trace_id"]
    assert record["request_body"] == {"identifier": "developer", "password": "***"}
    assert record["response_body"]["request_id"] == body["request_id"]
    assert record["response_body"]["trace_id"] == body["trace_id"]


def test_access_log_matches_error_envelope(caplog) -> None:
    app = create_app(auth_runtime=_auth_runtime())

    with caplog.at_level(logging.INFO, logger="app.http.access"):
        status_code, body, headers = call_json_response(
            app,
            "/api/v1/auth/login",
            "POST",
            json_body={"identifier": "developer", "password": "wrong-password"},
        )

    assert status_code == 401
    record = _single_access_log(caplog)
    assert headers["x-request-id"] == [body["request_id"]]
    assert headers["x-trace-id"] == [body["trace_id"]]
    assert record["request_id"] == body["request_id"]
    assert record["trace_id"] == body["trace_id"]
    assert record["request_body"]["password"] == "***"
    assert record["response_body"]["error"]["code"] == "unauthenticated"


def _auth_runtime():
    return build_auth_runtime(
        AuthRuntimeSettings(
            seed_dev_user=True,
            dev_user_identifier="developer",
            dev_user_email="developer@example.com",
            dev_username="developer",
            dev_display_name="Developer",
            dev_user_password=LOCAL_TEST_PASSWORD,
        )
    )


def _single_access_log(caplog) -> dict:
    messages = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "app.http.access"
    ]
    assert len(messages) == 1
    return messages[0]
