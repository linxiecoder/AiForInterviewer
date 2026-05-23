import json
import logging

from app.infrastructure.observability.logging import BackendLogSettings, LogUtil


def test_logutil_prints_structured_json_for_llm_transport_start(caplog) -> None:
    LogUtil.configure(BackendLogSettings(console_enabled=True, file_enabled=False))

    with caplog.at_level(logging.INFO, logger="app.llm.transport"):
        LogUtil.llm_transport_request_start(
            task_type="polish_question_generation",
            model="deepseek-v4-pro",
            provider_base_host="api.deepseek.com",
            contract_ids=("P-POLISH-002", "P-SHARED-001"),
            input_ref_count=5,
            timeout_seconds=90.0,
        )

    records = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "app.llm.transport"
    ]
    assert len(records) == 1
    payload = records[0]
    assert payload["event"] == "llm_transport_request_start"
    assert payload["level"] == "INFO"
    assert payload["task_type"] == "polish_question_generation"
    assert payload["model"] == "deepseek-v4-pro"
    assert payload["provider_base_host"] == "api.deepseek.com"
    assert payload["contract_ids"] == ["P-POLISH-002", "P-SHARED-001"]
    assert payload["input_ref_count"] == 5
    assert payload["timeout_seconds"] == 90.0
    assert payload["occurred_at"].endswith("+08:00")


def test_logutil_redacts_sensitive_nested_fields(caplog) -> None:
    LogUtil.configure(BackendLogSettings(console_enabled=True, file_enabled=False))

    with caplog.at_level(logging.INFO, logger="app.http.access"):
        LogUtil.http_access(
            request_id="trace_safe",
            trace_id="trace_safe",
            method="POST",
            path="/api/v1/auth/login",
            query={"api_key": "secret-api-key"},
            request_body={
                "identifier": "developer",
                "password": "plain-password",
                "nested": {"authorization": "Bearer secret-token"},
            },
            response_body={"status": "success", "raw_completion": "model raw output"},
            status_code=200,
            duration_ms=12.345,
            client={"host": "testclient", "port": 50000},
        )

    payload = next(
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "app.http.access"
    )
    assert payload["query"] == {"api_key": "***"}
    assert payload["request_body"]["password"] == "***"
    assert payload["request_body"]["nested"]["authorization"] == "***"
    assert payload["response_body"]["raw_completion"] == "***"
    assert "plain-password" not in json.dumps(payload, ensure_ascii=False)
    assert "secret-token" not in json.dumps(payload, ensure_ascii=False)
    assert "model raw output" not in json.dumps(payload, ensure_ascii=False)


def test_logutil_file_output_is_reserved_but_disabled_by_default(tmp_path, caplog) -> None:
    log_path = tmp_path / "backend.log"
    LogUtil.configure(
        BackendLogSettings(
            console_enabled=True,
            file_enabled=False,
            file_path=str(log_path),
        )
    )

    with caplog.at_level(logging.WARNING, logger="app.security.auth"):
        LogUtil.auth_dev_seed_disabled_missing_password()

    assert not log_path.exists()
    payload = next(
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "app.security.auth"
    )
    assert payload["event"] == "auth_dev_seed_disabled_missing_password"
    assert payload["level"] == "WARNING"
