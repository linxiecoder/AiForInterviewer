"""Unified backend logging utilities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextvars import ContextVar, Token
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo


APP_LOGGER_NAME = "app"
HTTP_ACCESS_LOGGER_NAME = "app.http.access"
LLM_TRANSPORT_LOGGER_NAME = "app.llm.transport"
SECURITY_AUTH_LOGGER_NAME = "app.security.auth"
AGENT_RUNTIME_LOGGER_NAME = "app.agent.runtime"
BEIJING_TIMEZONE = ZoneInfo("Asia/Shanghai")
REDACTED_VALUE = "***"
SENSITIVE_FIELD_MARKERS = (
    "password",
    "token",
    "secret",
    "authorization",
    "cookie",
    "session",
    "api_key",
    "raw_prompt",
    "raw_completion",
    "provider_payload",
    "prompt",
    "completion",
)


@dataclass(frozen=True)
class RequestTraceContext:
    request_id: str
    trace_id: str


_REQUEST_TRACE_CONTEXT: ContextVar[RequestTraceContext | None] = ContextVar(
    "request_trace_context",
    default=None,
)


def get_request_trace_context() -> RequestTraceContext | None:
    return _REQUEST_TRACE_CONTEXT.get()


def set_request_trace_context(request_id: str, trace_id: str) -> Token[RequestTraceContext | None]:
    return _REQUEST_TRACE_CONTEXT.set(RequestTraceContext(request_id=request_id, trace_id=trace_id))


def reset_request_trace_context(token: Token[RequestTraceContext | None]) -> None:
    _REQUEST_TRACE_CONTEXT.reset(token)


@dataclass(frozen=True)
class BackendLogSettings:
    """Backend logging settings.

    File output is intentionally disabled by default. `file_path` is accepted
    now so callers do not need a new logging API when file output is enabled
    later.
    """

    level: str = "INFO"
    console_enabled: bool = True
    file_path: str | None = None
    file_enabled: bool = False


class LogUtil:
    """Single entrypoint for backend log records."""

    _settings = BackendLogSettings()

    @classmethod
    def configure(cls, settings: BackendLogSettings | None = None) -> None:
        cls._settings = settings or BackendLogSettings()
        for logger_name in (
            APP_LOGGER_NAME,
            HTTP_ACCESS_LOGGER_NAME,
            LLM_TRANSPORT_LOGGER_NAME,
            SECURITY_AUTH_LOGGER_NAME,
            AGENT_RUNTIME_LOGGER_NAME,
        ):
            cls._configured_logger(logger_name)

    @classmethod
    def http_access(
        cls,
        *,
        request_id: str,
        trace_id: str,
        method: str | None,
        path: str | None,
        query: Mapping[str, Any],
        request_body: Any,
        response_body: Any,
        status_code: int,
        duration_ms: float,
        client: Mapping[str, Any] | None,
        exception_name: str | None = None,
    ) -> None:
        fields: dict[str, Any] = {
            "request_id": request_id,
            "trace_id": trace_id,
            "method": method,
            "path": path,
            "query": dict(query),
            "request_body": request_body,
            "status_code": status_code,
            "response_body": response_body,
            "duration_ms": duration_ms,
            "client": dict(client) if client is not None else None,
        }
        if exception_name is not None:
            fields["exception"] = exception_name
        cls._emit(HTTP_ACCESS_LOGGER_NAME, logging.INFO, "http_access", fields)

    @classmethod
    def llm_transport_request_start(
        cls,
        *,
        task_type: str,
        model: str,
        provider_base_host: str,
        contract_ids: Sequence[str],
        input_ref_count: int,
        timeout_seconds: float,
    ) -> None:
        cls._emit(
            LLM_TRANSPORT_LOGGER_NAME,
            logging.INFO,
            "llm_transport_request_start",
            {
                "task_type": task_type,
                "model": model,
                "provider_base_host": provider_base_host,
                "contract_ids": list(contract_ids),
                "input_ref_count": input_ref_count,
                "timeout_seconds": timeout_seconds,
            },
        )

    @classmethod
    def llm_transport_request_success(
        cls,
        *,
        task_type: str,
        model: str,
        provider_model: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        cls._emit(
            LLM_TRANSPORT_LOGGER_NAME,
            logging.INFO,
            "llm_transport_request_success",
            {
                "task_type": task_type,
                "model": model,
                "provider_model": provider_model,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

    @classmethod
    def llm_transport_request_failed(
        cls,
        *,
        task_type: str,
        model: str,
        error_type: str,
        duration_ms: float,
        status_code: int | None = None,
    ) -> None:
        fields: dict[str, Any] = {
            "task_type": task_type,
            "model": model,
            "error_type": error_type,
            "duration_ms": duration_ms,
        }
        if status_code is not None:
            fields["status_code"] = status_code
        cls._emit(LLM_TRANSPORT_LOGGER_NAME, logging.INFO, "llm_transport_request_failed", fields)

    @classmethod
    def agent_runtime_step(
        cls,
        *,
        task_type: str,
        phase: str,
        status: str,
        graph_name: str | None = None,
        run_id: str | None = None,
        ai_task_id: str | None = None,
        tool_name: str | None = None,
        attempt: int | None = None,
        max_attempts: int | None = None,
        max_agent_steps: int | None = None,
        timeout_seconds: float | None = None,
        retry_delay_seconds: float | None = None,
        duration_ms: float | None = None,
        input_ref: str | None = None,
        output_ref: str | None = None,
        error_type: str | None = None,
    ) -> None:
        fields: dict[str, Any] = {
            "task_type": task_type,
            "phase": phase,
            "status": status,
        }
        optional_fields: dict[str, Any | None] = {
            "graph_name": graph_name,
            "run_id": run_id,
            "ai_task_id": ai_task_id,
            "tool_name": tool_name,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "max_agent_steps": max_agent_steps,
            "timeout_seconds": timeout_seconds,
            "retry_delay_seconds": retry_delay_seconds,
            "duration_ms": duration_ms,
            "input_ref": input_ref,
            "output_ref": output_ref,
            "error_type": error_type,
        }
        fields.update({key: value for key, value in optional_fields.items() if value is not None})
        cls._emit(AGENT_RUNTIME_LOGGER_NAME, logging.INFO, "agent_runtime_step", fields)

    @classmethod
    def llm_provider_resolved(cls, *, provider: str) -> None:
        cls._emit(APP_LOGGER_NAME, logging.INFO, "llm_provider_resolved", {"provider": provider})

    @classmethod
    def llm_transport_built(cls, *, kind: str, provider: str) -> None:
        cls._emit(
            APP_LOGGER_NAME,
            logging.INFO,
            "llm_transport_built",
            {"kind": kind, "provider": provider},
        )

    @classmethod
    def api_runtime_ready(cls, *, message: str) -> None:
        cls._emit(APP_LOGGER_NAME, logging.INFO, "api_runtime_ready", {"message": message})

    @classmethod
    def api_cors_wildcard_dropped(cls) -> None:
        cls._emit(
            APP_LOGGER_NAME,
            logging.WARNING,
            "api_cors_wildcard_dropped",
            {"message": "API_CORS_ALLOW_ORIGINS contains wildcard; dropping it because credentials mode is enabled."},
        )

    @classmethod
    def auth_dev_seed_disabled_missing_password(cls) -> None:
        cls._emit(
            SECURITY_AUTH_LOGGER_NAME,
            logging.WARNING,
            "auth_dev_seed_disabled_missing_password",
            {"message": "API_AUTH_DEV_USER_ENABLED=true but API_AUTH_DEV_USER_PASSWORD is missing; dev seed user is disabled."},
        )

    @classmethod
    def polish_session_create_started(
        cls,
        *,
        resume_job_binding_id: str,
        topic_id: str | None,
        subtopic_id: str | None,
        has_custom_topic_text: bool,
        polish_theme: str | None,
    ) -> None:
        cls._emit(
            APP_LOGGER_NAME,
            logging.INFO,
            "polish_session_create_started",
            {
                "resume_job_binding_id": resume_job_binding_id,
                "topic_id": topic_id,
                "subtopic_id": subtopic_id,
                "has_custom_topic_text": has_custom_topic_text,
                "polish_theme": polish_theme,
            },
        )

    @classmethod
    def polish_session_create_failed(
        cls,
        *,
        duration_ms: float,
        error_code: str,
        error_message: str,
        session_id: str | None = None,
    ) -> None:
        fields: dict[str, Any] = {
            "duration_ms": duration_ms,
            "error_code": error_code,
            "error_message": error_message,
        }
        if session_id is not None:
            fields["session_id"] = session_id
        cls._emit(APP_LOGGER_NAME, logging.INFO, "polish_session_create_failed", fields)

    @classmethod
    def polish_session_create_completed(
        cls,
        *,
        duration_ms: float,
        session_id: str,
        progress_tree_status: str,
        progress_percent: int,
    ) -> None:
        cls._emit(
            APP_LOGGER_NAME,
            logging.INFO,
            "polish_session_create_completed",
            {
                "duration_ms": duration_ms,
                "session_id": session_id,
                "progress_tree_status": progress_tree_status,
                "progress_percent": progress_percent,
            },
        )

    @classmethod
    def _emit(
        cls,
        logger_name: str,
        level: int,
        event: str,
        fields: Mapping[str, Any],
    ) -> None:
        logger = cls._configured_logger(logger_name)
        record = cls._record(event=event, level=logging.getLevelName(level), fields=fields)
        logger.log(level, json.dumps(record, ensure_ascii=False, sort_keys=True))

    @classmethod
    def _record(cls, *, event: str, level: str, fields: Mapping[str, Any]) -> dict[str, Any]:
        record: dict[str, Any] = {
            "event": event,
            "occurred_at": datetime.now(BEIJING_TIMEZONE).isoformat(timespec="milliseconds"),
            "level": level,
        }
        trace_context = cls._current_request_trace_context()
        if trace_context is not None:
            record.setdefault("request_id", trace_context.request_id)
            record.setdefault("trace_id", trace_context.trace_id)
        for key, value in fields.items():
            record[str(key)] = cls._sanitize(value, key=str(key))
        return record

    @classmethod
    def _configured_logger(cls, logger_name: str) -> logging.Logger:
        app_logger = logging.getLogger(APP_LOGGER_NAME)
        app_logger.setLevel(_level_value(cls._settings.level))
        if cls._settings.console_enabled:
            _ensure_console_handler(app_logger)
        _configure_file_handler(app_logger, cls._settings)

        logger = logging.getLogger(logger_name)
        logger.setLevel(_level_value(cls._settings.level))
        return logger

    @staticmethod
    def _sanitize(value: Any, *, key: str | None = None) -> Any:
        if key is not None and _is_sensitive_key(key):
            return REDACTED_VALUE
        if isinstance(value, Mapping):
            return {str(item_key): LogUtil._sanitize(item_value, key=str(item_key)) for item_key, item_value in value.items()}
        if isinstance(value, list):
            return [LogUtil._sanitize(item) for item in value]
        if isinstance(value, tuple):
            return [LogUtil._sanitize(item) for item in value]
        return value

    @staticmethod
    def _current_request_trace_context() -> RequestTraceContext | None:
        return get_request_trace_context()


def _ensure_console_handler(logger: logging.Logger) -> None:
    if any(getattr(handler, "_aifi_backend_console_handler", False) for handler in logger.handlers):
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler._aifi_backend_console_handler = True  # type: ignore[attr-defined]
    logger.addHandler(handler)


def _configure_file_handler(logger: logging.Logger, settings: BackendLogSettings) -> None:
    existing_file_handlers = [
        handler
        for handler in logger.handlers
        if getattr(handler, "_aifi_backend_file_handler", False)
    ]
    if not settings.file_enabled or not settings.file_path:
        for handler in existing_file_handlers:
            logger.removeHandler(handler)
            handler.close()
        return
    target = str(Path(settings.file_path))
    if any(getattr(handler, "baseFilename", None) == target for handler in existing_file_handlers):
        return
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(target, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler._aifi_backend_file_handler = True  # type: ignore[attr-defined]
    logger.addHandler(handler)


def _level_value(level: str) -> int:
    normalized = level.strip().upper()
    value = getattr(logging, normalized, None)
    return value if isinstance(value, int) else logging.INFO


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(marker in normalized for marker in SENSITIVE_FIELD_MARKERS)
