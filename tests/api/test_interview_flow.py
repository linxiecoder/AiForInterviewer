"""ST13_12 R0 模拟面试主链路测试。"""

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

from app.boundary import (  # noqa: E402
    ENVIRONMENT_ENV,
    ERROR_CODE_KEY,
    ERROR_KEY,
    HTTP_ERROR_CODE_PREFIX,
    get_settings,
)
from app.interview_flow.contract import (  # noqa: E402
    FIELD_ANSWER,
    FIELD_CONTENT,
    FIELD_CURRENT_TURN,
    FIELD_JOB,
    FIELD_METADATA,
    FIELD_MODE,
    FIELD_NEXT_TURN,
    FIELD_PROVIDER,
    FIELD_QUESTION,
    FIELD_RECORD_ID,
    FIELD_RESUME,
    FIELD_SESSION_ID,
    FIELD_STATUS,
    FIELD_TURN_ID,
    FIELD_TURN_INDEX,
    FIELD_TURNS,
    INTERVIEWS_ROUTE_PREFIX,
    SESSION_STATUS_IN_PROGRESS,
)
from app.interview_record_contract import API_DATABASE_PATH_ENV, FIELD_OWNER_ID, RESPONSE_ITEMS  # noqa: E402
from app.llm.constants import (  # noqa: E402
    ERROR_LLM_PROVIDER_FAILED,
    LLM_PROVIDER_DETERMINISTIC,
    LLM_PROVIDER_ENV,
)
from app.llm.errors import LLMProviderError  # noqa: E402
from app.llm.models import LLMGenerateRequest  # noqa: E402
from app.main import create_app  # noqa: E402


API_PREFIX = "/api/v1"


@pytest.fixture()
def api_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    """为每个 case 创建隔离数据库，并显式使用 deterministic provider。"""
    artifacts = ManagedTempArtifacts(test_id="tests.api.test_interview_flow")
    database_dir = artifacts.make_temp_dir("database")
    monkeypatch.setenv(API_DATABASE_PATH_ENV, str(database_dir / "interview-flow.sqlite3"))
    monkeypatch.setenv(ENVIRONMENT_ENV, "test")
    monkeypatch.setenv(LLM_PROVIDER_ENV, LLM_PROVIDER_DETERMINISTIC)
    try:
        yield create_app(get_settings(), initialize_schema=True)
    finally:
        artifacts.cleanup()


def test_start_interview_uses_provider_and_persists_session(api_app: Any) -> None:
    """启动面试应通过 provider 生成首题，并保存可恢复的 session。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            created = await _start_interview(client, owner_id="owner-start")

            assert created[FIELD_OWNER_ID] == "owner-start"
            assert created[FIELD_STATUS] == SESSION_STATUS_IN_PROGRESS
            assert created[FIELD_RECORD_ID]
            assert created[FIELD_SESSION_ID]
            assert created[FIELD_CURRENT_TURN][FIELD_TURN_INDEX] == 0
            assert created[FIELD_CURRENT_TURN][FIELD_PROVIDER] == LLM_PROVIDER_DETERMINISTIC
            assert "deterministic question" in created[FIELD_CURRENT_TURN][FIELD_QUESTION]

            restored = await _restore_session(
                client,
                owner_id="owner-start",
                session_id=created[FIELD_SESSION_ID],
            )
            assert restored[FIELD_SESSION_ID] == created[FIELD_SESSION_ID]
            assert restored[FIELD_RECORD_ID] == created[FIELD_RECORD_ID]
            assert restored[FIELD_TURNS][0][FIELD_TURN_ID] == created[FIELD_CURRENT_TURN][FIELD_TURN_ID]

    asyncio.run(run_case())


def test_submit_answer_persists_answer_and_returns_follow_up(api_app: Any) -> None:
    """提交回答后应保存 answer，并生成最小 follow-up turn。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            created = await _start_interview(client, owner_id="owner-answer")

            submitted = await _submit_answer(
                client,
                owner_id="owner-answer",
                session_id=created[FIELD_SESSION_ID],
                turn_id=created[FIELD_CURRENT_TURN][FIELD_TURN_ID],
                content="I would keep the interface small and testable.",
            )

            assert submitted[FIELD_SESSION_ID] == created[FIELD_SESSION_ID]
            assert submitted[FIELD_TURNS][0][FIELD_ANSWER][FIELD_CONTENT] == (
                "I would keep the interface small and testable."
            )
            assert submitted[FIELD_NEXT_TURN][FIELD_TURN_INDEX] == 1
            assert submitted[FIELD_NEXT_TURN][FIELD_PROVIDER] == LLM_PROVIDER_DETERMINISTIC
            assert "deterministic follow_up" in submitted[FIELD_NEXT_TURN][FIELD_QUESTION]

            restored = await _restore_session(
                client,
                owner_id="owner-answer",
                session_id=created[FIELD_SESSION_ID],
            )
            assert len(restored[FIELD_TURNS]) == 2
            assert restored[FIELD_TURNS][0][FIELD_ANSWER][FIELD_CONTENT] == (
                "I would keep the interface small and testable."
            )

    asyncio.run(run_case())


def test_history_list_is_owner_scoped(api_app: Any) -> None:
    """历史列表必须按 owner_id 隔离，不能泄漏其他 owner 的 session。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            owner_a = await _start_interview(client, owner_id="owner-a")
            await _start_interview(client, owner_id="owner-b")

            response = await client.get(_interviews_url(), params={FIELD_OWNER_ID: "owner-a"})

            assert response.status_code == 200
            items = response.json()[RESPONSE_ITEMS]
            assert [item[FIELD_SESSION_ID] for item in items] == [owner_a[FIELD_SESSION_ID]]
            assert {item[FIELD_OWNER_ID] for item in items} == {"owner-a"}
            assert items[0][FIELD_MODE] == "r0_mock"

    asyncio.run(run_case())


def test_provider_failure_uses_stable_error_envelope(api_app: Any) -> None:
    """Provider 失败应透传稳定 code，不回退为 deterministic success。"""
    api_app.state.llm_provider = FailingProvider()

    async def run_case() -> None:
        async with _client(api_app) as client:
            response = await client.post(
                _interviews_url(),
                json=_start_body(owner_id="owner-provider-failure"),
            )

            assert response.status_code == 502
            payload = response.json()
            assert payload[ERROR_KEY][ERROR_CODE_KEY] == ERROR_LLM_PROVIDER_FAILED

    asyncio.run(run_case())


def test_validation_error_uses_project_error_envelope(api_app: Any) -> None:
    """请求体验证失败应保持 ST13_21 兼容 error envelope。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            body = _start_body(owner_id="owner-validation")
            body.pop(FIELD_OWNER_ID)

            response = await client.post(_interviews_url(), json=body)

            assert_error_code(response, 422)

    asyncio.run(run_case())


def test_missing_session_returns_404_error_envelope(api_app: Any) -> None:
    """恢复或提交不存在的 session 时应返回稳定 404 envelope。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            restore_response = await client.get(
                _interviews_url("/missing-session"),
                params={FIELD_OWNER_ID: "owner-missing"},
            )
            assert_error_code(restore_response, 404)

            submit_response = await client.post(
                _interviews_url("/missing-session/answers"),
                json={
                    FIELD_OWNER_ID: "owner-missing",
                    FIELD_TURN_ID: "missing-turn",
                    FIELD_CONTENT: "answer",
                },
            )
            assert_error_code(submit_response, 404)

    asyncio.run(run_case())


def _client(api_app: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app),
        base_url="http://testserver",
    )


def _interviews_url(suffix: str = "") -> str:
    return f"{API_PREFIX}{INTERVIEWS_ROUTE_PREFIX}{suffix}"


async def _start_interview(client: httpx.AsyncClient, *, owner_id: str) -> dict[str, Any]:
    response = await client.post(_interviews_url(), json=_start_body(owner_id=owner_id))
    assert response.status_code == 201
    return response.json()


async def _submit_answer(
    client: httpx.AsyncClient,
    *,
    owner_id: str,
    session_id: str,
    turn_id: str,
    content: str,
) -> dict[str, Any]:
    response = await client.post(
        _interviews_url(f"/{session_id}/answers"),
        json={
            FIELD_OWNER_ID: owner_id,
            FIELD_TURN_ID: turn_id,
            FIELD_CONTENT: content,
        },
    )
    assert response.status_code == 200
    return response.json()


async def _restore_session(
    client: httpx.AsyncClient,
    *,
    owner_id: str,
    session_id: str,
) -> dict[str, Any]:
    response = await client.get(
        _interviews_url(f"/{session_id}"),
        params={FIELD_OWNER_ID: owner_id},
    )
    assert response.status_code == 200
    return response.json()


def _start_body(*, owner_id: str) -> dict[str, Any]:
    return {
        FIELD_OWNER_ID: owner_id,
        FIELD_JOB: {"title": "Backend Engineer"},
        FIELD_RESUME: {"summary": "Python API experience"},
        FIELD_MODE: "r0_mock",
        FIELD_METADATA: {"source": "test"},
    }


def assert_error_code(response: httpx.Response, status_code: int) -> None:
    assert response.status_code == status_code
    assert response.json()[ERROR_KEY][ERROR_CODE_KEY] == (
        f"{HTTP_ERROR_CODE_PREFIX}_{status_code}"
    )


class FailingProvider:
    """主链路测试用 provider double，用于验证失败路径不会 fallback。"""

    def generate(self, request: LLMGenerateRequest) -> Any:
        """模拟 provider 边界失败，并保留 request_id。"""
        raise LLMProviderError(
            code=ERROR_LLM_PROVIDER_FAILED,
            message="provider failed",
            request_id=request.request_id,
        )
