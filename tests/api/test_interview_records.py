"""Tests for the ST13_20 R0 interview record persistence boundary."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest

from tools.testing.temp_artifacts import ManagedTempArtifacts

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.boundary import ERROR_CODE_KEY, ERROR_KEY, HTTP_ERROR_CODE_PREFIX  # noqa: E402
from app.interview_record_contract import (  # noqa: E402
    API_DATABASE_PATH_ENV,
    DEFAULT_HISTORY_STATUS,
    DEFAULT_RECORD_SOURCE,
    DEFAULT_RECORD_VERSION,
    FIELD_CREATED_AT,
    FIELD_ID,
    FIELD_OWNER_ID,
    FIELD_PAYLOAD,
    FIELD_SOURCE,
    FIELD_UPDATED_AT,
    FIELD_VERSION,
    INTERVIEW_RECORDS_ROUTE_PREFIX,
    PAYLOAD_EXPORT,
    PAYLOAD_INTERVIEW,
    PAYLOAD_REVIEW,
    RECORD_EXPORT_TRACE_ROUTE,
    RECORD_ID_ROUTE,
    RECORD_REVIEW_ROUTE,
    RESPONSE_EXPORT_TRACE_AVAILABLE,
    RESPONSE_ITEMS,
    RESPONSE_REVIEW_AVAILABLE,
    RESPONSE_STATUS,
)
from app.main import create_app  # noqa: E402
import app.persistence as persistence  # noqa: E402
from app.boundary import get_settings  # noqa: E402


API_PREFIX = "/api/v1"
MISSING_RECORD_ID = "missing-record"


@pytest.fixture()
def api_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    """Build a FastAPI app backed by a managed temporary SQLite database."""
    artifacts = ManagedTempArtifacts(test_id="tests.api.test_interview_records")
    database_dir = artifacts.make_temp_dir("database")
    monkeypatch.setenv(API_DATABASE_PATH_ENV, str(database_dir / "records.sqlite3"))
    try:
        yield create_app(get_settings(), initialize_schema=True)
    finally:
        artifacts.cleanup()


def test_owner_filter_keeps_history_scoped_to_requested_owner(api_app: Any) -> None:
    """History listing must not leak records across owner_id boundaries."""

    async def run_case() -> None:
        async with _client(api_app) as client:
            first = await _create_record(client, owner_id="owner-a")
            await _create_record(client, owner_id="owner-b")

            response = await client.get(_records_url(), params={FIELD_OWNER_ID: "owner-a"})
            assert response.status_code == 200
            items = response.json()[RESPONSE_ITEMS]

            assert [item[FIELD_ID] for item in items] == [first[FIELD_ID]]
            assert {item[FIELD_OWNER_ID] for item in items} == {"owner-a"}

    asyncio.run(run_case())


def test_empty_payload_uses_defaults_and_traceability_metadata(api_app: Any) -> None:
    """Save with omitted payload should return defaults and readable metadata."""

    async def run_case() -> None:
        async with _client(api_app) as client:
            created = await _create_record(client, owner_id="owner-empty", include_payload=False)

            assert created[FIELD_PAYLOAD] == {}
            assert created[FIELD_SOURCE] == DEFAULT_RECORD_SOURCE
            assert created[FIELD_VERSION] == DEFAULT_RECORD_VERSION
            assert created[FIELD_CREATED_AT]
            assert created[FIELD_UPDATED_AT]

            review_response = await client.get(
                _records_url(RECORD_REVIEW_ROUTE.format(record_id=created[FIELD_ID]))
            )
            assert review_response.status_code == 200
            assert review_response.json()[PAYLOAD_REVIEW] == {}

            trace_response = await client.get(
                _records_url(RECORD_EXPORT_TRACE_ROUTE.format(record_id=created[FIELD_ID]))
            )
            assert trace_response.status_code == 200
            trace = trace_response.json()
            assert trace[PAYLOAD_EXPORT] == {}
            assert _traceability_keys().issubset(trace)

    asyncio.run(run_case())


def test_restore_by_id_and_missing_id_error_envelope(api_app: Any) -> None:
    """Restore returns a saved record and 404 responses use the minimal envelope."""

    async def run_case() -> None:
        async with _client(api_app) as client:
            created = await _create_record(client, owner_id="owner-restore")

            response = await client.get(
                _records_url(RECORD_ID_ROUTE.format(record_id=created[FIELD_ID]))
            )
            assert response.status_code == 200
            restored = response.json()
            assert restored[FIELD_ID] == created[FIELD_ID]
            assert restored[FIELD_PAYLOAD][PAYLOAD_REVIEW]["summary"] == "Clear answer"

            missing_response = await client.get(_records_url(MISSING_RECORD_ID))
            assert_error_code(missing_response, 404)

    asyncio.run(run_case())


def test_history_list_returns_minimal_fields_in_newest_first_order(
    api_app: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """History returns summaries only, ordered by created_at descending."""
    timestamps = iter(("2026-04-30T00:00:00Z", "2026-04-30T00:00:01Z"))
    monkeypatch.setattr(persistence, "_utc_now", lambda: next(timestamps))

    async def run_case() -> None:
        async with _client(api_app) as client:
            older = await _create_record(client, owner_id="owner-history")
            newer = await _create_record(
                client,
                owner_id="owner-history",
                payload=_record_payload(status="reviewed"),
            )

            response = await client.get(_records_url(), params={FIELD_OWNER_ID: "owner-history"})
            assert response.status_code == 200
            items = response.json()[RESPONSE_ITEMS]

            assert [item[FIELD_ID] for item in items] == [newer[FIELD_ID], older[FIELD_ID]]
            assert FIELD_PAYLOAD not in items[0]
            assert items[0][RESPONSE_STATUS] == "reviewed"
            assert items[1][RESPONSE_STATUS] == DEFAULT_HISTORY_STATUS
            assert {
                FIELD_ID,
                FIELD_OWNER_ID,
                FIELD_SOURCE,
                FIELD_VERSION,
                RESPONSE_STATUS,
                FIELD_CREATED_AT,
                FIELD_UPDATED_AT,
                RESPONSE_REVIEW_AVAILABLE,
                RESPONSE_EXPORT_TRACE_AVAILABLE,
            } == set(items[0])

    asyncio.run(run_case())


def test_review_and_export_trace_missing_id_error_envelopes(api_app: Any) -> None:
    """Review and export trace read paths share the missing-record envelope."""

    async def run_case() -> None:
        async with _client(api_app) as client:
            review_response = await client.get(
                _records_url(RECORD_REVIEW_ROUTE.format(record_id=MISSING_RECORD_ID))
            )
            assert_error_code(review_response, 404)

            trace_response = await client.get(
                _records_url(RECORD_EXPORT_TRACE_ROUTE.format(record_id=MISSING_RECORD_ID))
            )
            assert_error_code(trace_response, 404)

    asyncio.run(run_case())


def test_validation_error_uses_minimal_error_envelope(api_app: Any) -> None:
    """Invalid create requests should keep the project error-envelope shape."""

    async def run_case() -> None:
        async with _client(api_app) as client:
            response = await client.post(
                _records_url(),
                json={FIELD_PAYLOAD: _record_payload()},
            )

            assert_error_code(response, 422)

    asyncio.run(run_case())


def test_interview_record_persistence_round_trip(api_app: Any) -> None:
    """Save, restore, list history, read review, and read export trace metadata."""

    async def run_case() -> None:
        async with _client(api_app) as client:
            created = await _create_record(
                client,
                owner_id="user-r0",
                source="r0-smoke",
                payload=_record_payload(export_version="r0-v1"),
            )
            record_id = created[FIELD_ID]
            assert created[FIELD_SOURCE] == "r0-smoke"
            assert created[FIELD_VERSION] == 1
            assert created[FIELD_CREATED_AT]
            assert created[FIELD_UPDATED_AT]

            restore_response = await client.get(
                _records_url(RECORD_ID_ROUTE.format(record_id=record_id))
            )
            assert restore_response.status_code == 200
            restored = restore_response.json()
            assert restored[FIELD_ID] == record_id
            assert restored[FIELD_PAYLOAD][PAYLOAD_REVIEW]["score"] == 82

            history_response = await client.get(_records_url())
            assert history_response.status_code == 200
            history = history_response.json()[RESPONSE_ITEMS]
            assert [item[FIELD_ID] for item in history] == [record_id]
            assert history[0][FIELD_SOURCE] == "r0-smoke"

            review_response = await client.get(
                _records_url(RECORD_REVIEW_ROUTE.format(record_id=record_id))
            )
            assert review_response.status_code == 200
            assert review_response.json()[PAYLOAD_REVIEW]["summary"] == "Clear answer"

            trace_response = await client.get(
                _records_url(RECORD_EXPORT_TRACE_ROUTE.format(record_id=record_id))
            )
            assert trace_response.status_code == 200
            trace = trace_response.json()
            assert trace[FIELD_SOURCE] == "r0-smoke"
            assert trace[FIELD_VERSION] == 1
            assert trace[PAYLOAD_EXPORT]["content_version"] == "r0-v1"
            assert _traceability_keys().issubset(trace)

    asyncio.run(run_case())


def _client(api_app: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app),
        base_url="http://testserver",
    )


def _records_url(suffix: str = "") -> str:
    return f"{API_PREFIX}{INTERVIEW_RECORDS_ROUTE_PREFIX}{suffix}"


async def _create_record(
    client: httpx.AsyncClient,
    *,
    owner_id: str,
    source: str = DEFAULT_RECORD_SOURCE,
    payload: dict[str, Any] | None = None,
    include_payload: bool = True,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        FIELD_OWNER_ID: owner_id,
        FIELD_SOURCE: source,
        FIELD_VERSION: DEFAULT_RECORD_VERSION,
    }
    if include_payload:
        body[FIELD_PAYLOAD] = payload if payload is not None else _record_payload()

    response = await client.post(_records_url(), json=body)
    assert response.status_code == 201
    return response.json()


def _record_payload(
    *,
    status: str | None = None,
    export_version: str = "r0-v1",
) -> dict[str, Any]:
    interview = {
        "question": "How would you design persistence?",
        "answer": "Use a minimal durable adapter.",
    }
    if status is not None:
        interview[RESPONSE_STATUS] = status
    return {
        "job": {"title": "Backend Engineer"},
        "resume": {"summary": "Python and API experience"},
        PAYLOAD_INTERVIEW: interview,
        PAYLOAD_REVIEW: {"summary": "Clear answer", "score": 82},
        PAYLOAD_EXPORT: {"format": "markdown", "content_version": export_version},
    }


def _traceability_keys() -> set[str]:
    return {
        FIELD_ID,
        FIELD_CREATED_AT,
        FIELD_UPDATED_AT,
        FIELD_SOURCE,
        FIELD_VERSION,
    }


def assert_error_code(response: httpx.Response, status_code: int) -> None:
    assert response.status_code == status_code
    assert response.json()[ERROR_KEY][ERROR_CODE_KEY] == (
        f"{HTTP_ERROR_CODE_PREFIX}_{status_code}"
    )
