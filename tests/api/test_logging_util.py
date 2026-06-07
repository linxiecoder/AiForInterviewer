import json
import logging

from app.infrastructure.observability.logging import (
    BackendLogSettings,
    LogUtil,
    reset_request_trace_context,
    set_request_trace_context,
)


_FEEDBACK_FORBIDDEN_LOG_KEYS = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "completion",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "provider_response",
    "raw_provider_response",
    "full_resume",
    "full_jd",
    "full_answer",
    "full_asset_body",
    "api_key",
    "token",
    "secret",
    "cookie",
)


def _app_payloads(caplog) -> list[dict]:
    return [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "app"
    ]


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


def test_logutil_feedback_generation_started_outputs_json_with_trace_context(caplog) -> None:
    LogUtil.configure(BackendLogSettings(console_enabled=True, file_enabled=False))
    token = set_request_trace_context(request_id="req_feedback_started", trace_id="trace_feedback_started")

    try:
        with caplog.at_level(logging.INFO, logger="app"):
            LogUtil.feedback_generation_started(
                session_id="session_1",
                question_id="question_1",
                answer_id="answer_1",
            )
    finally:
        reset_request_trace_context(token)

    payload = _app_payloads(caplog)[0]
    assert payload["event"] == "feedback_generation_started"
    assert payload["request_id"] == "req_feedback_started"
    assert payload["trace_id"] == "trace_feedback_started"
    assert payload["session_id"] == "session_1"
    assert payload["question_id"] == "question_1"
    assert payload["answer_id"] == "answer_1"
    assert payload["llm_called"] is False
    assert payload["provider_status"] == "not_called"
    assert payload["validation_stage"] is None
    assert payload["candidate_valid"] is None
    assert payload["prompt_char_count"] is None
    assert payload["evidence_item_count"] is None
    assert payload["duration_ms"] == 0


def test_logutil_feedback_generation_failed_outputs_validation_provider_and_error(caplog) -> None:
    LogUtil.configure(BackendLogSettings(console_enabled=True, file_enabled=False))

    with caplog.at_level(logging.INFO, logger="app"):
        LogUtil.feedback_generation_failed(
            session_id="session_1",
            question_id="question_1",
            answer_id="answer_1",
            llm_called=True,
            provider_status="failed",
            error_code="llm_transport_generation_failed",
            validation_stage="candidate",
            candidate_valid=False,
            prompt_char_count=4312,
            evidence_item_count=4,
            duration_ms=12.5,
        )

    payload = _app_payloads(caplog)[0]
    assert payload["event"] == "feedback_generation_failed"
    assert payload["session_id"] == "session_1"
    assert payload["question_id"] == "question_1"
    assert payload["answer_id"] == "answer_1"
    assert payload["llm_called"] is True
    assert payload["provider_status"] == "failed"
    assert payload["error_code"] == "llm_transport_generation_failed"
    assert payload["validation_stage"] == "candidate"
    assert payload["candidate_valid"] is False
    assert payload["prompt_char_count"] == 4312
    assert payload["evidence_item_count"] == 4
    assert payload["duration_ms"] == 12.5


def test_logutil_feedback_generation_succeeded_outputs_validation_and_provider(caplog) -> None:
    LogUtil.configure(BackendLogSettings(console_enabled=True, file_enabled=False))

    with caplog.at_level(logging.INFO, logger="app"):
        LogUtil.feedback_generation_succeeded(
            session_id="session_1",
            question_id="question_1",
            answer_id="answer_1",
            llm_called=True,
            provider_status="called",
            validation_stage="final",
            candidate_valid=True,
            prompt_char_count=5987,
            evidence_item_count=5,
            duration_ms=42.75,
        )

    payload = _app_payloads(caplog)[0]
    assert payload["event"] == "feedback_generation_succeeded"
    assert payload["session_id"] == "session_1"
    assert payload["question_id"] == "question_1"
    assert payload["answer_id"] == "answer_1"
    assert payload["llm_called"] is True
    assert payload["provider_status"] == "called"
    assert payload["error_code"] is None
    assert payload["validation_stage"] == "final"
    assert payload["candidate_valid"] is True
    assert payload["prompt_char_count"] == 5987
    assert payload["evidence_item_count"] == 5
    assert payload["duration_ms"] == 42.75


def test_logutil_feedback_generation_events_do_not_emit_forbidden_keys(caplog) -> None:
    LogUtil.configure(BackendLogSettings(console_enabled=True, file_enabled=False))

    with caplog.at_level(logging.INFO, logger="app"):
        LogUtil.feedback_generation_failed(
            session_id="session_1",
            question_id="question_1",
            answer_id="answer_1",
            llm_called=True,
            provider_status="failed",
            error_code="llm_transport_generation_failed",
            validation_stage="candidate",
            candidate_valid=False,
            prompt_char_count=4312,
            evidence_item_count=4,
            duration_ms=12.5,
        )

    payload = _app_payloads(caplog)[0]
    serialized = json.dumps(payload, ensure_ascii=False)
    for forbidden_key in _FEEDBACK_FORBIDDEN_LOG_KEYS:
        assert forbidden_key not in payload
        assert forbidden_key not in serialized
