"""ST13_13/ST13_15/ST13_19 R0 评分、复盘与 Markdown 导出测试。"""

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
    ERROR_REQUEST_ID_KEY,
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
    FIELD_QUESTION,
    FIELD_RECORD_ID,
    FIELD_RESUME,
    FIELD_SESSION_ID,
    FIELD_SNAPSHOT_INDEX,
    FIELD_TURN_ID,
    FIELD_TURNS,
    INTERVIEWS_ROUTE_PREFIX,
    INTERVIEW_FLOW_RECORD_SOURCE,
    SESSION_STATUS_IN_PROGRESS,
)
from app.interview_record_contract import (  # noqa: E402
    API_DATABASE_PATH_ENV,
    DEFAULT_RECORD_VERSION,
    FIELD_OWNER_ID,
    FIELD_PAYLOAD,
    INTERVIEW_RECORDS_ROUTE_PREFIX,
    PAYLOAD_INTERVIEW,
    PAYLOAD_EXPORT,
    PAYLOAD_REVIEW,
    RECORD_ID_ROUTE,
    RESPONSE_STATUS,
)
from app.llm.constants import (  # noqa: E402
    ERROR_LLM_PROVIDER_FAILED,
    LLM_PROVIDER_DETERMINISTIC,
    LLM_PROVIDER_ENV,
)
from app.llm.errors import LLMProviderError  # noqa: E402
from app.llm.models import LLMGenerateRequest, LLMGenerateResult  # noqa: E402
from app.main import create_app  # noqa: E402


API_PREFIX = "/api/v1"
PAYLOAD_SCORE = "score"
RESPONSE_REVIEW = "review"
RESPONSE_EXPORT = "export"


@pytest.fixture()
def api_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    """为 review/export 测试创建隔离数据库和 deterministic provider。"""
    artifacts = ManagedTempArtifacts(test_id="tests.api.test_review_export")
    database_dir = artifacts.make_temp_dir("database")
    monkeypatch.setenv(API_DATABASE_PATH_ENV, str(database_dir / "review-export.sqlite3"))
    monkeypatch.setenv(ENVIRONMENT_ENV, "test")
    monkeypatch.setenv(LLM_PROVIDER_ENV, LLM_PROVIDER_DETERMINISTIC)
    try:
        yield create_app(get_settings(), initialize_schema=True)
    finally:
        artifacts.cleanup()


def test_generate_review_summary_score_and_persistence(api_app: Any) -> None:
    """Review endpoint 应生成 R1 多维 score、可信 review payload 并持久化。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            session = await _answered_session(client, owner_id="owner-review")

            response = await client.post(
                _interviews_url(f"/{session[FIELD_SESSION_ID]}/review"),
                json={FIELD_OWNER_ID: "owner-review"},
            )

            assert response.status_code == 200
            payload = response.json()
            score = payload[PAYLOAD_SCORE]
            review = payload[RESPONSE_REVIEW]
            assert 0 <= score["value"] <= 100
            assert score["score_total"] == score["value"]
            assert score["status"] == "generated"
            assert score["explanation"]
            assert len(score["dimensions"]) >= 5
            for dimension in score["dimensions"]:
                assert {"id", "label", "score", "reason"}.issubset(dimension)
                assert 0 <= dimension["score"] <= 100
                assert dimension["reason"]
                assert "citation_refs" in dimension
                assert "evidence_gap_refs" in dimension
                assert "low_confidence" in dimension
            assert score["suggestions"]
            assert score["weak_areas"]
            assert score["review_summary"]

            assert review["summary"]
            assert review["review_summary"] == review["summary"]
            assert review["score_total"] == score["score_total"]
            assert review["dimensions"] == score["dimensions"]
            assert review["suggestions"]
            assert review["weak_areas"]
            assert review["improvements"]
            assert review["status"] == "generated"
            assert review["degraded"] is False
            assert review["retryable"] is False

            persisted = await _get_record(client, record_id=payload[FIELD_RECORD_ID])
            assert persisted[FIELD_PAYLOAD][PAYLOAD_SCORE]["score_total"] == score["score_total"]
            assert persisted[FIELD_PAYLOAD][PAYLOAD_REVIEW]["summary"] == review["summary"]

    asyncio.run(run_case())


def test_review_consumes_legacy_r0_score_value_without_crashing(api_app: Any) -> None:
    """旧 R0 score.value 可被 review 消费，并以 review.score_total 兼容表达。"""
    session_id = "session-legacy-score"
    api_app.state.interview_record_store.create_record(
        owner_id="owner-legacy-score",
        source=INTERVIEW_FLOW_RECORD_SOURCE,
        version=DEFAULT_RECORD_VERSION,
        payload={
            PAYLOAD_INTERVIEW: {
                FIELD_SESSION_ID: session_id,
                FIELD_MODE: "legacy_r0",
                RESPONSE_STATUS: SESSION_STATUS_IN_PROGRESS,
                FIELD_METADATA: {},
                FIELD_SNAPSHOT_INDEX: 0,
                FIELD_TURNS: [
                    {
                        FIELD_TURN_ID: "turn-legacy-score",
                        FIELD_QUESTION: "How do you keep old score records stable?",
                        FIELD_ANSWER: {FIELD_CONTENT: "I keep a value fallback."},
                    }
                ],
            },
            PAYLOAD_SCORE: {
                "value": 64,
                "content_version": "r0-score-v1",
            },
        },
    )

    async def run_case() -> None:
        async with _client(api_app) as client:
            response = await client.post(
                _interviews_url(f"/{session_id}/review"),
                json={FIELD_OWNER_ID: "owner-legacy-score"},
            )
            detail = await client.get(
                _interviews_url(f"/{session_id}"),
                params={FIELD_OWNER_ID: "owner-legacy-score"},
            )

            assert response.status_code == 200
            payload = response.json()
            assert payload[PAYLOAD_SCORE]["value"] == 64
            assert payload[PAYLOAD_SCORE]["content_version"] == "r0-score-v1"
            assert payload[RESPONSE_REVIEW]["score_total"] == 64
            assert payload[RESPONSE_REVIEW]["dimensions"] == []
            assert payload[RESPONSE_REVIEW]["status"] == "generated"
            assert detail.status_code == 200
            assert detail.json()[PAYLOAD_SCORE]["value"] == 64

    asyncio.run(run_case())


def test_provider_success_does_not_persist_prompt_raw_response_or_secret(api_app: Any) -> None:
    """provider 成功路径只保存安全摘要，不持久化 prompt/raw response/secret/object path。"""
    forbidden_markers = [
        "FULL_PROMPT_SHOULD_NOT_PERSIST",
        "RAW_LLM_RESPONSE_SHOULD_NOT_PERSIST",
        "FAKE_SECRET_SHOULD_NOT_PERSIST",
        "s3://private-bucket/raw-export.md",
    ]

    async def run_case() -> None:
        async with _client(api_app) as client:
            session = await _answered_session(client, owner_id="owner-sensitive-provider")
            api_app.state.llm_provider = SensitiveProvider()

            response = await client.post(
                _interviews_url(f"/{session[FIELD_SESSION_ID]}/review"),
                json={FIELD_OWNER_ID: "owner-sensitive-provider", "use_provider": True},
            )

            assert response.status_code == 200
            payload = response.json()
            persisted = await _get_record(client, record_id=payload[FIELD_RECORD_ID])
            traces = api_app.state.traceability_store.list_traces(
                owner_id="owner-sensitive-provider",
                session_ref=session[FIELD_SESSION_ID],
            )
            serialized = "\n".join([str(payload), str(persisted), str(traces)])

            assert payload[PAYLOAD_SCORE]["scoring_strategy"] == "provider_assisted"
            assert persisted[FIELD_PAYLOAD][PAYLOAD_REVIEW]["metadata"]["provider_comment_present"] is True
            for marker in forbidden_markers:
                assert marker not in serialized

    asyncio.run(run_case())


def test_markdown_export_content_metadata_and_persistence(api_app: Any) -> None:
    """Markdown export 应包含面试、答案、score、review、metadata 并写回 payload。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            session = await _answered_session(client, owner_id="owner-export")

            response = await client.post(
                _interviews_url(f"/{session[FIELD_SESSION_ID]}/export"),
                json={FIELD_OWNER_ID: "owner-export"},
            )

            assert response.status_code == 200
            payload = response.json()
            export = payload[RESPONSE_EXPORT]
            assert export["format"] == "markdown"
            assert export["content_version"] == "r0-export-v1"
            assert export["metadata"]["generated_at"]
            assert export["metadata"]["session_id"] == session[FIELD_SESSION_ID]

            content = export["content"]
            assert "Interview" in content
            assert "I would keep the API small and persist every snapshot." in content
            assert "score" in content
            assert "Review Summary" in content
            assert "Weakness" in content
            assert "Improvement" in content

            persisted = await _get_record(client, record_id=payload[FIELD_RECORD_ID])
            record_payload = persisted[FIELD_PAYLOAD]
            assert record_payload[PAYLOAD_EXPORT]["content"] == content
            assert record_payload[PAYLOAD_SCORE]["content_version"] == "r0-score-v1"
            assert record_payload[PAYLOAD_REVIEW]["content_version"] == "r0-review-v1"

    asyncio.run(run_case())


def test_review_export_missing_session_and_validation_error(api_app: Any) -> None:
    """缺失 session 与缺失 owner_id 都应返回稳定 error envelope。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            missing_review = await client.post(
                _interviews_url("/missing-session/review"),
                json={FIELD_OWNER_ID: "owner-missing"},
            )
            assert_error_code(missing_review, 404)

            missing_export = await client.get(
                _interviews_url("/missing-session/export"),
                params={FIELD_OWNER_ID: "owner-missing"},
            )
            assert_error_code(missing_export, 404)

            validation_response = await client.post(
                _interviews_url("/missing-session/review"),
                json={},
            )
            assert_error_code(validation_response, 422)

    asyncio.run(run_case())


def test_review_provider_failure_uses_stable_error_envelope(api_app: Any) -> None:
    """Provider 复盘失败不能 fallback，必须返回 ST13_11 稳定 envelope。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            session = await _answered_session(client, owner_id="owner-provider")
            api_app.state.llm_provider = FailingProvider()

            response = await client.post(
                _interviews_url(f"/{session[FIELD_SESSION_ID]}/review"),
                json={FIELD_OWNER_ID: "owner-provider", "use_provider": True},
            )

            assert response.status_code == 502
            error = response.json()[ERROR_KEY]
            assert error[ERROR_CODE_KEY] == ERROR_LLM_PROVIDER_FAILED
            assert error[ERROR_REQUEST_ID_KEY]

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


async def _answered_session(client: httpx.AsyncClient, *, owner_id: str) -> dict[str, Any]:
    created = await _start_interview(client, owner_id=owner_id)
    answer_response = await client.post(
        _interviews_url(f"/{created[FIELD_SESSION_ID]}/answers"),
        json={
            FIELD_OWNER_ID: owner_id,
            FIELD_TURN_ID: created[FIELD_CURRENT_TURN][FIELD_TURN_ID],
            FIELD_CONTENT: "I would keep the API small and persist every snapshot.",
        },
    )
    assert answer_response.status_code == 200
    return answer_response.json()


async def _start_interview(client: httpx.AsyncClient, *, owner_id: str) -> dict[str, Any]:
    response = await client.post(
        _interviews_url(),
        json={
            FIELD_OWNER_ID: owner_id,
            FIELD_JOB: {"title": "Backend Engineer"},
            FIELD_RESUME: {"summary": "Python API experience"},
            FIELD_MODE: "r0_mock",
            FIELD_METADATA: {"source": "review-export-test"},
        },
    )
    assert response.status_code == 201
    return response.json()


async def _get_record(client: httpx.AsyncClient, *, record_id: str) -> dict[str, Any]:
    response = await client.get(_records_url(RECORD_ID_ROUTE.format(record_id=record_id)))
    assert response.status_code == 200
    return response.json()


def assert_error_code(response: httpx.Response, status_code: int) -> None:
    assert response.status_code == status_code
    assert response.json()[ERROR_KEY][ERROR_CODE_KEY] == (
        f"{HTTP_ERROR_CODE_PREFIX}_{status_code}"
    )


class FailingProvider:
    """复盘测试用 provider double，用于验证失败路径不会 fallback。"""

    def generate(self, request: LLMGenerateRequest) -> Any:
        """模拟 provider 边界失败，并保留 request_id。"""
        raise LLMProviderError(
            code=ERROR_LLM_PROVIDER_FAILED,
            message="provider failed",
            request_id=request.request_id,
        )


class SensitiveProvider:
    """provider success double，用于证明 raw provider content 不会被持久化。"""

    def generate(self, request: LLMGenerateRequest) -> LLMGenerateResult:
        """返回含敏感哨兵的 fake 内容，测试不得将其写入 payload 或 trace。"""
        return LLMGenerateResult(
            provider="fake-provider",
            model="fake-sensitive-model",
            content=(
                "88 FULL_PROMPT_SHOULD_NOT_PERSIST "
                "RAW_LLM_RESPONSE_SHOULD_NOT_PERSIST "
                "FAKE_SECRET_SHOULD_NOT_PERSIST "
                "s3://private-bucket/raw-export.md"
            ),
            finish_reason="stop",
            request_id=request.request_id,
        )
