"""Tiny ASGI caller for sandbox-stable FastAPI endpoint tests."""

from __future__ import annotations

import asyncio
from json import dumps, loads
from typing import Any


def call_json(
    app: Any,
    path: str,
    method: str = "GET",
    *,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    status, body, _headers = call_json_response(
        app,
        path,
        method,
        json_body=json_body,
        headers=headers,
    )
    return status, body


def call_json_response(
    app: Any,
    path: str,
    method: str = "GET",
    *,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any], dict[str, list[str]]]:
    return asyncio.run(_call_json(app, path, method, json_body=json_body, headers=headers))


async def _call_json(
    app: Any,
    path: str,
    method: str,
    *,
    json_body: dict[str, Any] | None,
    headers: dict[str, str] | None,
) -> tuple[int, dict[str, Any], dict[str, list[str]]]:
    messages: list[dict[str, Any]] = []
    request_sent = False
    request_body = b""
    request_headers = [(key.lower().encode("ascii"), value.encode("latin-1")) for key, value in (headers or {}).items()]
    if json_body is not None:
        request_body = dumps(json_body).encode("utf-8")
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
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return status, loads(body.decode("utf-8")), response_headers
