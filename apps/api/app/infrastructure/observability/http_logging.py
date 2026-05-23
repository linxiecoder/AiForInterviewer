"""HTTP access logging middleware."""

from __future__ import annotations

import json
from time import perf_counter
from typing import Any
from urllib.parse import parse_qs

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.domain.shared.ids import generate_request_id, generate_trace_id
from app.infrastructure.observability.logging import (
    LogUtil,
    RequestTraceContext,
    get_request_trace_context,
    reset_request_trace_context,
    set_request_trace_context,
)


ACCESS_LOGGER_NAME = "app.http.access"
DEFAULT_BODY_LIMIT_BYTES = 4096
REDACTED_VALUE = "***"
SENSITIVE_FIELD_MARKERS = (
    "password",
    "token",
    "secret",
    "authorization",
    "cookie",
    "session",
    "api_key",
)

class HttpAccessLogMiddleware:
    """Log one structured access record for each HTTP request."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        logger_name: str = ACCESS_LOGGER_NAME,
        max_body_bytes: int = DEFAULT_BODY_LIMIT_BYTES,
    ) -> None:
        self.app = app
        self.logger_name = logger_name
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_headers = _headers_from_scope(scope)
        response_headers: list[tuple[bytes, bytes]] = []
        request_id = _header_value(request_headers, "x-request-id") or generate_request_id()
        trace_id = _header_value(request_headers, "x-trace-id") or generate_trace_id()
        context_token = set_request_trace_context(request_id=request_id, trace_id=trace_id)

        request_body = _BodyCapture(self.max_body_bytes)
        response_body = _BodyCapture(self.max_body_bytes)
        status_code = 500
        start = perf_counter()
        exception_name: str | None = None

        async def receive_wrapper() -> Message:
            message = await receive()
            if message["type"] == "http.request":
                request_body.add(message.get("body", b""))
            return message

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code, response_headers
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                response_headers = _with_trace_headers(
                    list(message.get("headers", [])),
                    request_id=request_id,
                    trace_id=trace_id,
                )
                message = {**message, "headers": response_headers}
            elif message["type"] == "http.response.body":
                response_body.add(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        except BaseException as exc:
            exception_name = type(exc).__name__
            raise
        finally:
            duration_ms = round((perf_counter() - start) * 1000, 3)
            LogUtil.http_access(
                request_id=request_id,
                trace_id=trace_id,
                method=scope.get("method"),
                path=scope.get("path"),
                query=_query_params(scope),
                request_body=_summarize_body(
                    request_body,
                    content_type=_header_value(request_headers, "content-type"),
                ),
                response_body=_summarize_body(
                    response_body,
                    content_type=_header_value(_decode_headers(response_headers), "content-type"),
                ),
                status_code=status_code,
                duration_ms=duration_ms,
                client=_client(scope),
                exception_name=exception_name,
            )
            reset_request_trace_context(context_token)


class _BodyCapture:
    def __init__(self, limit_bytes: int) -> None:
        self.limit_bytes = max(0, limit_bytes)
        self.chunks: list[bytes] = []
        self.total_size = 0
        self.truncated = False

    def add(self, chunk: bytes) -> None:
        if not chunk:
            return
        self.total_size += len(chunk)
        current_size = sum(len(existing) for existing in self.chunks)
        remaining = self.limit_bytes - current_size
        if remaining <= 0:
            self.truncated = True
            return
        self.chunks.append(chunk[:remaining])
        if len(chunk) > remaining:
            self.truncated = True

    def raw(self) -> bytes:
        return b"".join(self.chunks)


def _summarize_body(body: _BodyCapture, *, content_type: str | None) -> Any:
    if body.total_size == 0:
        return None
    raw = body.raw()
    if _is_json_content_type(content_type) and not body.truncated:
        try:
            return _sanitize(json.loads(raw.decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    return {
        "content_type": content_type,
        "size_bytes": body.total_size,
        "truncated": body.truncated,
        "body": raw.decode("utf-8", errors="replace"),
    }


def _sanitize(value: Any, *, key: str | None = None) -> Any:
    if key is not None and _is_sensitive_key(key):
        return REDACTED_VALUE
    if isinstance(value, dict):
        return {str(item_key): _sanitize(item_value, key=str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def _query_params(scope: Scope) -> dict[str, Any]:
    raw = scope.get("query_string", b"")
    if not raw:
        return {}
    parsed = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
    collapsed = {
        key: values[0] if len(values) == 1 else values
        for key, values in parsed.items()
    }
    return _sanitize(collapsed)


def _client(scope: Scope) -> dict[str, Any] | None:
    client = scope.get("client")
    if client is None:
        return None
    host, port = client
    return {"host": host, "port": port}


def _headers_from_scope(scope: Scope) -> list[tuple[str, str]]:
    return _decode_headers(list(scope.get("headers", [])))


def _decode_headers(headers: list[tuple[bytes, bytes]]) -> list[tuple[str, str]]:
    return [
        (key.decode("latin-1").lower(), value.decode("latin-1"))
        for key, value in headers
    ]


def _header_value(headers: list[tuple[str, str]], name: str) -> str | None:
    target = name.lower()
    for key, value in headers:
        if key == target:
            stripped = value.strip()
            return stripped or None
    return None


def _with_trace_headers(
    headers: list[tuple[bytes, bytes]],
    *,
    request_id: str,
    trace_id: str,
) -> list[tuple[bytes, bytes]]:
    without_existing = [
        (key, value)
        for key, value in headers
        if key.lower() not in {b"x-request-id", b"x-trace-id"}
    ]
    return [
        *without_existing,
        (b"x-request-id", request_id.encode("latin-1")),
        (b"x-trace-id", trace_id.encode("latin-1")),
    ]


def _is_json_content_type(content_type: str | None) -> bool:
    return bool(content_type and "application/json" in content_type.lower())


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(marker in normalized for marker in SENSITIVE_FIELD_MARKERS)
