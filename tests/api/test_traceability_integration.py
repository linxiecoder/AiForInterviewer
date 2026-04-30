"""ST13_20 R1 traceability integration 最小闭环测试。"""

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
    FIELD_PROVIDER_TRACE,
    FIELD_RESUME,
    FIELD_SESSION_ID,
    FIELD_SNAPSHOT_INDEX,
    FIELD_TRACE_SUMMARY,
    FIELD_TURN_ID,
    FIELD_TURN_INDEX,
    FIELD_TURNS,
    INTERVIEWS_ROUTE_PREFIX,
    INTERVIEW_FLOW_RECORD_SOURCE,
    SESSION_STATUS_IN_PROGRESS,
)
from app.interview_record_contract import (  # noqa: E402
    API_DATABASE_PATH_ENV,
    DEFAULT_RECORD_VERSION,
    FIELD_OWNER_ID,
    PAYLOAD_INTERVIEW,
    RESPONSE_STATUS,
)
from app.llm.constants import LLM_PROVIDER_DETERMINISTIC, LLM_PROVIDER_ENV  # noqa: E402
from app.main import create_app  # noqa: E402
from app.persistence import TraceabilityStore  # noqa: E402
from app.rag.models import KnowledgeResource, KnowledgeVisibility, RAGSourceType  # noqa: E402
from app.rag.service import InMemoryRAGAdapter, RAGService  # noqa: E402
from app.traceability import (  # noqa: E402
    TRACE_TYPE_INTERVIEW,
    TRACE_TYPE_RAG_EVIDENCE,
    TRACE_TYPE_REVIEW_EXPORT,
    TraceabilityRecord,
    TraceabilityStatus,
)


API_PREFIX = "/api/v1"


@pytest.fixture()
def api_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    """创建隔离数据库，并显式使用 deterministic provider。"""
    artifacts = ManagedTempArtifacts(test_id="tests.api.test_traceability_integration")
    database_dir = artifacts.make_temp_dir("database")
    monkeypatch.setenv(API_DATABASE_PATH_ENV, str(database_dir / "traceability-flow.sqlite3"))
    monkeypatch.setenv(ENVIRONMENT_ENV, "test")
    monkeypatch.setenv(LLM_PROVIDER_ENV, LLM_PROVIDER_DETERMINISTIC)
    try:
        yield create_app(get_settings(), initialize_schema=True)
    finally:
        artifacts.cleanup()


def test_interview_review_export_history_flow_writes_readable_traceability_records(
    api_app: Any,
) -> None:
    """主业务链路应写入 session/turn/answer/score/review/export/history trace。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            started = await _start_interview(client, owner_id="owner-trace")
            answered = await _submit_answer(
                client,
                owner_id="owner-trace",
                session_id=started[FIELD_SESSION_ID],
                turn_id=started[FIELD_CURRENT_TURN][FIELD_TURN_ID],
            )
            await _generate_review(client, owner_id="owner-trace", session_id=answered[FIELD_SESSION_ID])
            await _generate_export(client, owner_id="owner-trace", session_id=answered[FIELD_SESSION_ID])
            await _history(client, owner_id="owner-trace")

        traces = api_app.state.traceability_store.list_traces(owner_id="owner-trace")
        interview_traces = [
            item for item in traces if item["trace_type"] == TRACE_TYPE_INTERVIEW
        ]
        review_export_traces = [
            item for item in traces if item["trace_type"] == TRACE_TYPE_REVIEW_EXPORT
        ]

        assert any(
            item["session_ref"] == started[FIELD_SESSION_ID]
            and item["turn_ref"] == started[FIELD_CURRENT_TURN][FIELD_TURN_ID]
            for item in interview_traces
        )
        assert any(item["answer_ref"] == f"answer:{started[FIELD_CURRENT_TURN][FIELD_TURN_ID]}" for item in interview_traces)
        assert any(item["score_ref"] for item in review_export_traces)
        assert any(item["review_ref"] for item in review_export_traces)
        assert any(item["export_ref"] for item in review_export_traces)
        assert any(item["metadata"].get("operation") == "history.list" for item in traces)

        loaded = api_app.state.traceability_store.get_trace(interview_traces[0]["id"])
        assert loaded is not None
        assert loaded["owner_id"] == "owner-trace"

    asyncio.run(run_case())


def test_interview_read_surfaces_return_safe_trace_summary(api_app: Any) -> None:
    """detail/history/review/export 应返回可消费且已过滤的 trace summary。"""

    async def run_case() -> None:
        async with _client(api_app) as client:
            started = await _start_interview(client, owner_id="owner-read")
            answered = await _submit_answer(
                client,
                owner_id="owner-read",
                session_id=started[FIELD_SESSION_ID],
                turn_id=started[FIELD_CURRENT_TURN][FIELD_TURN_ID],
            )
            session_id = answered[FIELD_SESSION_ID]
            _write_rag_gap_trace(api_app, owner_id="owner-read", session_id=session_id)
            _write_hidden_trace(api_app)

            review = await _generate_review(client, owner_id="owner-read", session_id=session_id)
            export = await _generate_export(client, owner_id="owner-read", session_id=session_id)
            detail = await _get_session(client, owner_id="owner-read", session_id=session_id)
            history = await _history(client, owner_id="owner-read")

        detail_summary = detail[FIELD_TRACE_SUMMARY]
        history_summary = history["items"][0][FIELD_TRACE_SUMMARY]
        review_summary = review[FIELD_TRACE_SUMMARY]
        export_summary = export[FIELD_TRACE_SUMMARY]

        assert detail_summary["status"] == "available"
        assert detail_summary["session_refs"] == [session_id]
        assert started[FIELD_CURRENT_TURN][FIELD_TURN_ID] in detail_summary["turn_refs"]
        assert f"answer:{started[FIELD_CURRENT_TURN][FIELD_TURN_ID]}" in detail_summary["answer_refs"]
        assert "gap:permission_filtered_empty" in detail_summary["rag"]["evidence_gap_refs"]
        assert detail_summary["score_refs"]
        assert detail_summary["review_refs"]
        assert detail_summary["export_refs"]
        assert review_summary["review_refs"] == detail_summary["review_refs"]
        assert export_summary["export_refs"] == detail_summary["export_refs"]
        assert history_summary["session_refs"] == [session_id]
        assert "hidden-resource-id" not in str(detail_summary)
        assert "hidden-resource-id" not in str(history)
        assert all("source_snapshot_ref" not in item for item in detail_summary["request_refs"])
        assert all("metadata" not in item for item in detail_summary["request_refs"])

    asyncio.run(run_case())


def test_interview_detail_returns_stable_empty_trace_summary(api_app: Any) -> None:
    """没有 trace 的历史记录也应返回稳定空 trace_summary，而不是 500。"""
    session_id = "session-empty-trace"
    record = api_app.state.interview_record_store.create_record(
        owner_id="owner-empty",
        source=INTERVIEW_FLOW_RECORD_SOURCE,
        version=DEFAULT_RECORD_VERSION,
        payload={
            PAYLOAD_INTERVIEW: {
                FIELD_SESSION_ID: session_id,
                FIELD_MODE: "empty_trace",
                RESPONSE_STATUS: SESSION_STATUS_IN_PROGRESS,
                FIELD_METADATA: {},
                FIELD_SNAPSHOT_INDEX: 0,
                FIELD_TURNS: [
                    {
                        FIELD_TURN_ID: "turn-empty-trace",
                        FIELD_TURN_INDEX: 0,
                        "question": "How do you keep trace reads stable?",
                    }
                ],
                FIELD_PROVIDER_TRACE: [],
            }
        },
    )

    async def run_case() -> None:
        async with _client(api_app) as client:
            detail = await _get_session(client, owner_id="owner-empty", session_id=session_id)
            history = await _history(client, owner_id="owner-empty")

        assert detail["record_id"] == record["id"]
        assert detail[FIELD_TRACE_SUMMARY] == {
            "status": "empty",
            "counts": {"total": 0, "interview": 0, "rag_evidence": 0, "review_export": 0},
            "session_refs": [],
            "turn_refs": [],
            "answer_refs": [],
            "score_refs": [],
            "review_refs": [],
            "export_refs": [],
            "rag": {
                "retrieval_query_refs": [],
                "retrieval_result_refs": [],
                "citation_refs": [],
                "evidence_refs": [],
                "evidence_gap_refs": [],
                "statuses": [],
            },
            "request_refs": [],
        }
        assert history["items"][0][FIELD_TRACE_SUMMARY]["status"] == "empty"

    asyncio.run(run_case())


def test_rag_permission_filtered_empty_writes_degraded_gap_without_invisible_resource_id(
    api_app: Any,
) -> None:
    """RAG 权限过滤 empty state 应写 evidence gap，且不泄露不可见 resource id。"""
    private_resource = KnowledgeResource(
        resource_id="private-resource-other-owner",
        owner_id="owner-other",
        visibility=KnowledgeVisibility.PRIVATE,
        source_type=RAGSourceType.PRIVATE_DOCUMENT,
        source_label="Other private doc",
        content_summary="backend persistence evidence",
        chunk_ref="chunk-secret",
        source_version="v1",
    )
    service = RAGService(
        adapter=InMemoryRAGAdapter(resources=(private_resource,)),
        trace_store=api_app.state.traceability_store,
    )

    result = service.retrieve(
        actor_id="owner-rag",
        query_text="backend persistence evidence",
        selected_resource_ids=("private-resource-other-owner",),
        trigger="review",
    )

    assert result.degraded is True
    assert result.evidence_gap is not None
    traces = api_app.state.traceability_store.list_traces(
        owner_id="owner-rag",
        trace_type=TRACE_TYPE_RAG_EVIDENCE,
    )
    assert len(traces) == 1
    trace = traces[0]
    assert trace["status"] == TraceabilityStatus.DEGRADED
    assert trace["evidence_gap_ref"] == "gap:permission_filtered_empty"
    assert trace["citation_refs"] == []
    assert trace["evidence_refs"] == []
    assert "private-resource-other-owner" not in str(trace["metadata"])


def test_traceability_read_helper_filters_by_owner(api_app: Any) -> None:
    """读取 helper 必须按 owner_id 收敛，不能泄露其他 owner 的 resource id。"""
    trace_store: TraceabilityStore = api_app.state.traceability_store
    own = trace_store.create_trace(
        TraceabilityRecord(
            owner_id="owner-visible",
            trace_type=TRACE_TYPE_INTERVIEW,
            status=TraceabilityStatus.COMPLETED,
            request_id="req-visible",
            operation_id="op-visible",
            session_ref="session-visible",
        )
    )
    trace_store.create_trace(
        TraceabilityRecord(
            owner_id="owner-hidden",
            trace_type=TRACE_TYPE_INTERVIEW,
            status=TraceabilityStatus.COMPLETED,
            request_id="req-hidden",
            operation_id="op-hidden",
            session_ref="session-hidden",
            source_snapshot_ref="resource-hidden",
        )
    )

    visible = trace_store.list_traces(owner_id="owner-visible")

    assert [item["id"] for item in visible] == [own["id"]]
    assert "resource-hidden" not in str(visible)


def _client(api_app: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app),
        base_url="http://testserver",
    )


def _interviews_url(suffix: str = "") -> str:
    return f"{API_PREFIX}{INTERVIEWS_ROUTE_PREFIX}{suffix}"


async def _start_interview(client: httpx.AsyncClient, *, owner_id: str) -> dict[str, Any]:
    response = await client.post(
        _interviews_url(),
        json={
            FIELD_OWNER_ID: owner_id,
            FIELD_JOB: {"title": "Backend Engineer"},
            FIELD_RESUME: {"summary": "Python API and RAG experience"},
            FIELD_MODE: "r1_trace",
            FIELD_METADATA: {"source": "traceability-integration-test"},
        },
    )
    assert response.status_code == 201
    return response.json()


async def _submit_answer(
    client: httpx.AsyncClient,
    *,
    owner_id: str,
    session_id: str,
    turn_id: str,
) -> dict[str, Any]:
    response = await client.post(
        _interviews_url(f"/{session_id}/answers"),
        json={
            FIELD_OWNER_ID: owner_id,
            FIELD_TURN_ID: turn_id,
            FIELD_CONTENT: "I would preserve request ids and evidence refs across the flow.",
        },
    )
    assert response.status_code == 200
    return response.json()


async def _generate_review(
    client: httpx.AsyncClient,
    *,
    owner_id: str,
    session_id: str,
) -> dict[str, Any]:
    response = await client.post(
        _interviews_url(f"/{session_id}/review"),
        json={FIELD_OWNER_ID: owner_id},
    )
    assert response.status_code == 200
    return response.json()


async def _generate_export(
    client: httpx.AsyncClient,
    *,
    owner_id: str,
    session_id: str,
) -> dict[str, Any]:
    response = await client.post(
        _interviews_url(f"/{session_id}/export"),
        json={FIELD_OWNER_ID: owner_id},
    )
    assert response.status_code == 200
    return response.json()


async def _get_session(
    client: httpx.AsyncClient,
    *,
    owner_id: str,
    session_id: str,
) -> dict[str, Any]:
    response = await client.get(_interviews_url(f"/{session_id}"), params={FIELD_OWNER_ID: owner_id})
    assert response.status_code == 200
    return response.json()


async def _history(client: httpx.AsyncClient, *, owner_id: str) -> dict[str, Any]:
    response = await client.get(_interviews_url(), params={FIELD_OWNER_ID: owner_id})
    assert response.status_code == 200
    return response.json()


def _write_rag_gap_trace(api_app: Any, *, owner_id: str, session_id: str) -> None:
    api_app.state.traceability_store.create_trace(
        TraceabilityRecord(
            owner_id=owner_id,
            trace_type=TRACE_TYPE_RAG_EVIDENCE,
            status=TraceabilityStatus.DEGRADED,
            request_id="rag-visible-request",
            operation_id="rag.retrieve:review",
            session_ref=session_id,
            retrieval_query_ref="rag-query:backend persistence",
            retrieval_result_ref="rag-result:0:permission_filtered_empty",
            evidence_gap_ref="gap:permission_filtered_empty",
            failure_reason="permission_filtered_empty",
            metadata={"hidden_resource_id": "hidden-resource-id"},
        )
    )


def _write_hidden_trace(api_app: Any) -> None:
    api_app.state.traceability_store.create_trace(
        TraceabilityRecord(
            owner_id="owner-hidden",
            trace_type=TRACE_TYPE_INTERVIEW,
            status=TraceabilityStatus.COMPLETED,
            request_id="hidden-request",
            operation_id="interview.hidden",
            session_ref="hidden-session",
            source_snapshot_ref="hidden-resource-id",
            metadata={"hidden_resource_id": "hidden-resource-id"},
        )
    )
