"""R0 最小端到端验收 smoke：start -> answer -> review -> export。"""

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

from app.boundary import ENVIRONMENT_ENV, get_settings  # noqa: E402
from app.interview_flow.contract import (  # noqa: E402
    FIELD_CONTENT,
    FIELD_CURRENT_TURN,
    FIELD_JOB,
    FIELD_METADATA,
    FIELD_MODE,
    FIELD_NEXT_TURN,
    FIELD_QUESTION,
    FIELD_RECORD_ID,
    FIELD_RESUME,
    FIELD_SESSION_ID,
    FIELD_TURN_ID,
    FIELD_TURNS,
    INTERVIEWS_ROUTE_PREFIX,
)
from app.interview_record_contract import (  # noqa: E402
    API_DATABASE_PATH_ENV,
    FIELD_OWNER_ID,
    FIELD_PAYLOAD,
    INTERVIEW_RECORDS_ROUTE_PREFIX,
    PAYLOAD_EXPORT,
    PAYLOAD_REVIEW,
    RECORD_ID_ROUTE,
    RESPONSE_ITEMS,
)
from app.llm.constants import LLM_PROVIDER_DETERMINISTIC, LLM_PROVIDER_ENV  # noqa: E402
from app.main import create_app  # noqa: E402


API_PREFIX = "/api/v1"
PAYLOAD_SCORE = "score"


@pytest.fixture()
def api_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    """创建隔离数据库，并显式使用 deterministic provider 完成 R0 smoke。"""
    artifacts = ManagedTempArtifacts(test_id="tests.api.test_r0_e2e")
    database_dir = artifacts.make_temp_dir("database")
    monkeypatch.setenv(API_DATABASE_PATH_ENV, str(database_dir / "r0-e2e.sqlite3"))
    monkeypatch.setenv(ENVIRONMENT_ENV, "test")
    monkeypatch.setenv(LLM_PROVIDER_ENV, LLM_PROVIDER_DETERMINISTIC)
    try:
        yield create_app(get_settings(), initialize_schema=True)
    finally:
        artifacts.cleanup()


def test_r0_start_answer_review_export_happy_path(api_app: Any) -> None:
    """R0 主链路、复盘、导出和持久化应能在同一 session 内闭环。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            started = await _start_interview(client)
            answered = await _submit_answer(client, started)
            review = await _generate_review(client, answered)
            export = await _generate_export(client, answered)

            assert started[FIELD_CURRENT_TURN][FIELD_QUESTION]
            assert answered[FIELD_NEXT_TURN][FIELD_QUESTION]
            assert 0 <= review[PAYLOAD_SCORE]["value"] <= 100
            assert review[PAYLOAD_REVIEW]["summary"]
            assert review[PAYLOAD_REVIEW]["weakness"]
            assert review[PAYLOAD_REVIEW]["improvements"]

            export_payload = export[PAYLOAD_EXPORT]
            assert export_payload["format"] == "markdown"
            assert export_payload["metadata"]["session_id"] == answered[FIELD_SESSION_ID]
            assert "R0 answer keeps provider and persistence boundaries explicit." in export_payload[
                "content"
            ]
            assert "score" in export_payload["content"]
            assert "Review Summary" in export_payload["content"]

            restored = await _restore_session(client, session_id=answered[FIELD_SESSION_ID])
            assert restored[FIELD_SESSION_ID] == answered[FIELD_SESSION_ID]
            assert len(restored[FIELD_TURNS]) == 2

            history = await _history(client)
            assert [item[FIELD_SESSION_ID] for item in history[RESPONSE_ITEMS]] == [
                answered[FIELD_SESSION_ID]
            ]

            persisted = await _get_record(client, record_id=export[FIELD_RECORD_ID])
            record_payload = persisted[FIELD_PAYLOAD]
            assert record_payload[PAYLOAD_SCORE]["content_version"] == "r0-score-v1"
            assert record_payload[PAYLOAD_REVIEW]["content_version"] == "r0-review-v1"
            assert record_payload[PAYLOAD_EXPORT]["content_version"] == "r0-export-v1"

    asyncio.run(run_case())


def _client(api_app: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app),
        base_url="http://testserver",
    )


def _interviews_url(suffix: str = "") -> str:
    return f"{API_PREFIX}{INTERVIEWS_ROUTE_PREFIX}{suffix}"


def _records_url(suffix: str = "") -> str:
    return f"{API_PREFIX}{INTERVIEW_RECORDS_ROUTE_PREFIX}{suffix}"


async def _start_interview(client: httpx.AsyncClient) -> dict[str, Any]:
    response = await client.post(
        _interviews_url(),
        json={
            FIELD_OWNER_ID: "owner-r0-e2e",
            FIELD_JOB: {"title": "Backend Engineer"},
            FIELD_RESUME: {"summary": "Python API and persistence experience"},
            FIELD_MODE: "r0_mock",
            FIELD_METADATA: {"source": "r0-e2e"},
        },
    )
    assert response.status_code == 201
    return response.json()


async def _submit_answer(
    client: httpx.AsyncClient,
    started: dict[str, Any],
) -> dict[str, Any]:
    response = await client.post(
        _interviews_url(f"/{started[FIELD_SESSION_ID]}/answers"),
        json={
            FIELD_OWNER_ID: "owner-r0-e2e",
            FIELD_TURN_ID: started[FIELD_CURRENT_TURN][FIELD_TURN_ID],
            FIELD_CONTENT: "R0 answer keeps provider and persistence boundaries explicit.",
        },
    )
    assert response.status_code == 200
    return response.json()


async def _generate_review(client: httpx.AsyncClient, session: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(
        _interviews_url(f"/{session[FIELD_SESSION_ID]}/review"),
        json={FIELD_OWNER_ID: "owner-r0-e2e"},
    )
    assert response.status_code == 200
    return response.json()


async def _generate_export(client: httpx.AsyncClient, session: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(
        _interviews_url(f"/{session[FIELD_SESSION_ID]}/export"),
        json={FIELD_OWNER_ID: "owner-r0-e2e"},
    )
    assert response.status_code == 200
    return response.json()


async def _restore_session(client: httpx.AsyncClient, *, session_id: str) -> dict[str, Any]:
    response = await client.get(
        _interviews_url(f"/{session_id}"),
        params={FIELD_OWNER_ID: "owner-r0-e2e"},
    )
    assert response.status_code == 200
    return response.json()


async def _history(client: httpx.AsyncClient) -> dict[str, Any]:
    response = await client.get(_interviews_url(), params={FIELD_OWNER_ID: "owner-r0-e2e"})
    assert response.status_code == 200
    return response.json()


async def _get_record(client: httpx.AsyncClient, *, record_id: str) -> dict[str, Any]:
    response = await client.get(_records_url(RECORD_ID_ROUTE.format(record_id=record_id)))
    assert response.status_code == 200
    return response.json()
