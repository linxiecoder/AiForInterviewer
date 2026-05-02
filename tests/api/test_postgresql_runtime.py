"""R1 PostgreSQL runtime integration tests for persistence stores."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
import os
import sys
from pathlib import Path
from uuid import uuid4

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
    FIELD_RESUME,
    FIELD_SESSION_ID,
    FIELD_TURN_ID,
    INTERVIEWS_ROUTE_PREFIX,
)
from app.interview_record_contract import (  # noqa: E402
    API_DATABASE_PATH_ENV,
    DATABASE_URL_ENV,
    DEFAULT_RECORD_SOURCE,
    DEFAULT_RECORD_VERSION,
    FIELD_OWNER_ID,
)
from app.llm.constants import LLM_PROVIDER_DETERMINISTIC, LLM_PROVIDER_ENV  # noqa: E402
from app.main import create_app  # noqa: E402
from app.persistence import (  # noqa: E402
    InterviewRecordStore,
    RAGPersistenceStore,
    TraceabilityStore,
    _create_database_engine,
    _load_schema_sql,
    _schema_statements,
)
from app.rag.models import (  # noqa: E402
    EvidenceTarget,
    KnowledgeDocument,
    KnowledgeVisibility,
    RAGSourceType,
)
from app.rag.service import RAGService, chunk_document  # noqa: E402
from app.traceability import (  # noqa: E402
    TRACE_TYPE_INTERVIEW,
    TraceabilityRecord,
    TraceabilityStatus,
)


API_PREFIX = "/api/v1"


@contextmanager
def managed_workspace(label: str) -> Iterator[Path]:
    artifacts = ManagedTempArtifacts(test_id=f"tests.api.test_postgresql_runtime.{label}")
    try:
        yield artifacts.make_temp_dir(label)
    finally:
        artifacts.cleanup()


def test_database_url_takes_precedence_over_sqlite_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """DATABASE_URL 存在时，runtime 应优先使用显式数据库 URL。"""
    database_url = "postgresql+psycopg://user:pass@127.0.0.1:5432/interviewer"
    monkeypatch.setenv(DATABASE_URL_ENV, database_url)
    monkeypatch.setenv(API_DATABASE_PATH_ENV, "/tmp/ignored-api.sqlite3")

    settings = get_settings()

    assert settings.database_path == database_url


def test_postgresql_url_uses_psycopg_driver_without_connecting() -> None:
    """postgresql:// URL 应归一化到 psycopg 3 driver，并且创建 engine 不触发连接。"""
    engine = _create_database_engine("postgresql://user:pass@127.0.0.1:5432/interviewer")
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
    finally:
        engine.dispose()


def test_sqlite_path_still_uses_sqlite_engine() -> None:
    """普通文件路径仍然走 SQLite fallback，并自动创建父目录。"""
    with managed_workspace("sqlite-engine") as workspace:
        database_path = workspace / "nested" / "api.sqlite3"

        engine = _create_database_engine(str(database_path))
        try:
            assert engine.dialect.name == "sqlite"
            assert database_path.parent.exists()
        finally:
            engine.dispose()


def test_schema_statements_cover_current_runtime_tables() -> None:
    """PG schema-loader 分支应能从现有 schema 文件拆出稳定 DDL statement。"""
    statements = _schema_statements(_load_schema_sql())

    assert any("CREATE TABLE IF NOT EXISTS interview_records" in item for item in statements)
    interview_statement = next(
        item for item in statements if "CREATE TABLE IF NOT EXISTS interview_records" in item
    )
    assert "updated_at TEXT NOT NULL" in interview_statement
    assert interview_statement.rstrip().endswith(");")
    assert any("CREATE TABLE IF NOT EXISTS traceability_records" in item for item in statements)
    assert any("CREATE TABLE IF NOT EXISTS rag_documents" in item for item in statements)
    assert any("CREATE TABLE IF NOT EXISTS rag_chunks" in item for item in statements)
    assert any("CREATE TABLE IF NOT EXISTS rag_retrieval_records" in item for item in statements)
    assert not any("Restore lookup index" in item for item in statements)
    assert all(statement.strip().endswith(";") for statement in statements)


def test_postgresql_traceability_and_rag_round_trip_when_enabled() -> None:
    """设置 TEST_DATABASE_URL 时，PG 下应完成 schema 初始化、trace、RAG hit 与 gap round trip。"""
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL 未设置，跳过 PostgreSQL 集成测试。")

    suffix = uuid4().hex
    owner_id = f"owner-pg-{suffix}"
    other_owner_id = f"owner-pg-other-{suffix}"
    session_ref = f"session-pg-{suffix}"
    interview_store = InterviewRecordStore(database_url)
    trace_store = TraceabilityStore(database_url)
    rag_store = RAGPersistenceStore(database_url)
    interview_store.initialize()
    trace_store.initialize()
    rag_store.initialize()

    interview = interview_store.create_record(
        owner_id=owner_id,
        source=DEFAULT_RECORD_SOURCE,
        version=DEFAULT_RECORD_VERSION,
        payload={
            "interview": {
                "session_id": session_ref,
                "status": "saved",
            }
        },
    )
    assert interview_store.get_record(interview["id"]) is not None
    assert interview_store.list_records(owner_id=owner_id)[0]["owner_id"] == owner_id

    saved_trace = trace_store.create_trace(
        TraceabilityRecord(
            owner_id=owner_id,
            trace_type=TRACE_TYPE_INTERVIEW,
            status=TraceabilityStatus.RETRYABLE,
            request_id=f"req-pg-{suffix}",
            operation_id="interview.answer",
            session_ref=session_ref,
            turn_ref=f"turn-{suffix}",
            answer_ref=f"answer-{suffix}",
            retryable=True,
            failure_reason="provider_timeout",
            metadata={"runtime": "postgresql", "case": suffix},
        )
    )
    trace_store.create_trace(
        TraceabilityRecord(
            owner_id=other_owner_id,
            trace_type=TRACE_TYPE_INTERVIEW,
            status=TraceabilityStatus.COMPLETED,
            request_id=f"req-pg-hidden-{suffix}",
            operation_id="interview.answer",
            session_ref=session_ref,
        )
    )

    visible_traces = trace_store.list_traces(owner_id=owner_id, session_ref=session_ref)
    assert [trace["id"] for trace in visible_traces] == [saved_trace["id"]]
    assert visible_traces[0]["retryable"] is True
    assert visible_traces[0]["metadata"] == {"runtime": "postgresql", "case": suffix}

    document = KnowledgeDocument(
        document_id=f"doc-pg-{suffix}",
        owner_id=owner_id,
        visibility=KnowledgeVisibility.PRIVATE,
        source_type=RAGSourceType.PRIVATE_DOCUMENT,
        source_label="PostgreSQL notes",
        content="postgresql runtime citation evidence gap durable retrieval",
        source_version="v1",
    )
    rag_store.save_document(document, chunks=chunk_document(document, max_tokens=4))
    chunks = rag_store.list_chunks(owner_id=owner_id, document_id=document.document_id)
    assert chunks[0]["chunk_ref"] == f"{document.document_id}:chunk-0"

    service = RAGService(adapter=rag_store, trace_store=trace_store, rag_store=rag_store)
    hit_result = service.retrieve(
        actor_id=owner_id,
        query_text="postgresql citation",
        evidence_target=EvidenceTarget.REVIEW,
        trigger="review",
        session_ref=session_ref,
    )
    gap_result = service.retrieve(
        actor_id=owner_id,
        query_text="unmatched query token",
        evidence_target=EvidenceTarget.REVIEW,
        trigger="review",
        session_ref=f"{session_ref}-gap",
    )

    hit_records = rag_store.list_retrieval_records(owner_id=owner_id, session_ref=session_ref)
    gap_records = rag_store.list_retrieval_records(
        owner_id=owner_id,
        session_ref=f"{session_ref}-gap",
    )

    assert hit_result.result_summary.hit_count == 1
    assert hit_records[0]["citation_refs"] == [hit_result.citations[0].citation_ref]
    assert hit_records[0]["evidence_refs"] == [hit_result.evidence_items[0].evidence_ref]
    assert hit_records[0]["evidence_gap_ref"] is None
    assert gap_result.result_summary.empty_reason == "no_result"
    assert gap_records[0]["degraded"] is True
    assert gap_records[0]["retryable"] is False
    assert gap_records[0]["evidence_gap_ref"] == "gap:no_result"


def test_postgresql_scoring_review_round_trip_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """设置 TEST_DATABASE_URL 时，PG 下应完成 score/review payload round trip。"""
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL 未设置，跳过 PostgreSQL 集成测试。")

    monkeypatch.setenv(DATABASE_URL_ENV, database_url)
    monkeypatch.setenv(ENVIRONMENT_ENV, "test")
    monkeypatch.setenv(LLM_PROVIDER_ENV, LLM_PROVIDER_DETERMINISTIC)
    app = create_app(get_settings(), initialize_schema=True)

    async def run_case() -> None:
        suffix = uuid4().hex
        owner_id = f"owner-pg-score-{suffix}"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            started_response = await client.post(
                _interviews_url(),
                json={
                    FIELD_OWNER_ID: owner_id,
                    FIELD_JOB: {"title": "Backend Engineer"},
                    FIELD_RESUME: {"summary": "PostgreSQL and API persistence"},
                    FIELD_MODE: "pg_score_review",
                    FIELD_METADATA: {"source": "postgresql-score-review-test"},
                },
            )
            assert started_response.status_code == 201
            started = started_response.json()
            answer_response = await client.post(
                _interviews_url(f"/{started[FIELD_SESSION_ID]}/answers"),
                json={
                    FIELD_OWNER_ID: owner_id,
                    FIELD_TURN_ID: started[FIELD_CURRENT_TURN][FIELD_TURN_ID],
                    FIELD_CONTENT: "I keep trace refs and score payloads durable in PostgreSQL.",
                },
            )
            assert answer_response.status_code == 200

            review_response = await client.post(
                _interviews_url(f"/{started[FIELD_SESSION_ID]}/review"),
                json={FIELD_OWNER_ID: owner_id},
            )
            assert review_response.status_code == 200
            review_payload = review_response.json()

            detail_response = await client.get(
                _interviews_url(f"/{started[FIELD_SESSION_ID]}"),
                params={FIELD_OWNER_ID: owner_id},
            )
            assert detail_response.status_code == 200
            detail = detail_response.json()

            assert 0 <= review_payload["score"]["score_total"] <= 100
            assert review_payload["score"]["dimensions"]
            assert all(item["reason"] for item in review_payload["score"]["dimensions"])
            assert review_payload["review"]["review_summary"]
            assert review_payload["review"]["suggestions"]
            assert review_payload["review"]["weak_areas"]
            assert detail["score"]["score_total"] == review_payload["score"]["score_total"]
            assert detail["review"]["review_summary"] == review_payload["review"]["review_summary"]
            assert detail["trace_summary"]["score_refs"]
            assert detail["trace_summary"]["review_refs"]

    asyncio.run(run_case())


def _interviews_url(suffix: str = "") -> str:
    return f"{API_PREFIX}{INTERVIEWS_ROUTE_PREFIX}{suffix}"
