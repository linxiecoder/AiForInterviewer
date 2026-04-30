"""ST13_20 持久化边界的 SQLite adapter。"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from app.interview_record_contract import (
    DEFAULT_HISTORY_STATUS,
    FIELD_CREATED_AT,
    FIELD_ID,
    FIELD_OWNER_ID,
    FIELD_PAYLOAD,
    FIELD_PAYLOAD_JSON,
    FIELD_SOURCE,
    FIELD_UPDATED_AT,
    FIELD_VERSION,
    PAYLOAD_EXPORT,
    PAYLOAD_INTERVIEW,
    PAYLOAD_REVIEW,
    RESPONSE_EXPORT_TRACE_AVAILABLE,
    RESPONSE_REVIEW_AVAILABLE,
    RESPONSE_STATUS,
    SQL_COLUMNS,
    TABLE_INTERVIEW_RECORDS,
)
from app.traceability import TraceabilityRecord

if TYPE_CHECKING:
    from app.rag.models import (
        KnowledgeDocument,
        KnowledgeResource,
        RAGFoundationResult,
        RetrievalQuerySummary,
    )

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
SCHEMA_PATH = SCHEMA_DIR / "interview_records.sql"
TRACEABILITY_SCHEMA_PATH = SCHEMA_DIR / "traceability_records.sql"
RAG_SCHEMA_PATH = SCHEMA_DIR / "rag_records.sql"
SELECT_COLUMNS_SQL = ", ".join(SQL_COLUMNS)
INSERT_COLUMNS_SQL = ", ".join(SQL_COLUMNS)
INSERT_PLACEHOLDERS_SQL = ", ".join("?" for _ in SQL_COLUMNS)

INSERT_RECORD_SQL = f"""
    INSERT INTO {TABLE_INTERVIEW_RECORDS} ({INSERT_COLUMNS_SQL})
    VALUES ({INSERT_PLACEHOLDERS_SQL})
"""
SELECT_RECORD_SQL = f"""
    SELECT {SELECT_COLUMNS_SQL}
    FROM {TABLE_INTERVIEW_RECORDS}
    WHERE {FIELD_ID} = ?
"""
SELECT_RECORDS_SQL = f"""
    SELECT {SELECT_COLUMNS_SQL}
    FROM {TABLE_INTERVIEW_RECORDS}
    ORDER BY {FIELD_CREATED_AT} DESC, {FIELD_ID} DESC
"""
SELECT_RECORDS_BY_OWNER_SQL = f"""
    SELECT {SELECT_COLUMNS_SQL}
    FROM {TABLE_INTERVIEW_RECORDS}
    WHERE {FIELD_OWNER_ID} = ?
    ORDER BY {FIELD_CREATED_AT} DESC, {FIELD_ID} DESC
"""
PERSISTENCE_WRITE_FAILURE = "interview record was not persisted"

TABLE_TRACEABILITY_RECORDS = "traceability_records"
TRACEABILITY_COLUMNS = (
    FIELD_ID,
    FIELD_OWNER_ID,
    "trace_type",
    RESPONSE_STATUS,
    "request_id",
    "operation_id",
    "job_ref",
    "resume_ref",
    "session_ref",
    "turn_ref",
    "answer_ref",
    "score_ref",
    "review_ref",
    "export_ref",
    "retrieval_query_ref",
    "retrieval_result_ref",
    "citation_refs_json",
    "evidence_refs_json",
    "evidence_gap_ref",
    "source_snapshot_ref",
    "schema_version",
    "content_version",
    "retryable",
    "failure_reason",
    "metadata_json",
    FIELD_CREATED_AT,
    FIELD_UPDATED_AT,
)
TRACEABILITY_SELECT_COLUMNS_SQL = ", ".join(TRACEABILITY_COLUMNS)
TRACEABILITY_INSERT_COLUMNS_SQL = ", ".join(TRACEABILITY_COLUMNS)
TRACEABILITY_INSERT_PLACEHOLDERS_SQL = ", ".join("?" for _ in TRACEABILITY_COLUMNS)
INSERT_TRACE_SQL = f"""
    INSERT INTO {TABLE_TRACEABILITY_RECORDS} ({TRACEABILITY_INSERT_COLUMNS_SQL})
    VALUES ({TRACEABILITY_INSERT_PLACEHOLDERS_SQL})
"""
SELECT_TRACE_SQL = f"""
    SELECT {TRACEABILITY_SELECT_COLUMNS_SQL}
    FROM {TABLE_TRACEABILITY_RECORDS}
    WHERE {FIELD_ID} = ?
"""
TRACEABILITY_WRITE_FAILURE = "traceability record was not persisted"

TABLE_RAG_DOCUMENTS = "rag_documents"
TABLE_RAG_CHUNKS = "rag_chunks"
TABLE_RAG_RETRIEVAL_RECORDS = "rag_retrieval_records"
RAG_CONTENT_SUMMARY_MAX_LENGTH = 500
RAG_DOCUMENT_COLUMNS = (
    FIELD_ID,
    FIELD_OWNER_ID,
    "document_id",
    "visibility",
    "source_type",
    "source_label",
    "content_summary",
    "source_version",
    "index_status",
    "failure_reason",
    FIELD_CREATED_AT,
    FIELD_UPDATED_AT,
)
RAG_CHUNK_COLUMNS = (
    FIELD_ID,
    FIELD_OWNER_ID,
    "document_id",
    "resource_id",
    "chunk_ref",
    "chunk_index",
    "visibility",
    "source_type",
    "source_label",
    "content_summary",
    "source_version",
    "start_offset",
    "end_offset",
    "index_status",
    "failure_reason",
    FIELD_CREATED_AT,
    FIELD_UPDATED_AT,
)
RAG_RETRIEVAL_COLUMNS = (
    FIELD_ID,
    FIELD_OWNER_ID,
    "trace_ref",
    "request_id",
    "operation_id",
    "session_ref",
    "turn_ref",
    "answer_ref",
    "retrieval_query_ref",
    "retrieval_result_ref",
    "query_summary",
    "top_k",
    "trigger",
    "visibility_filter",
    "hit_count",
    "hit_summary_json",
    "empty_reason",
    "degraded",
    "retryable",
    "citation_refs_json",
    "evidence_refs_json",
    "evidence_gap_ref",
    "source_snapshot_ref",
    "permission_filtered_count",
    FIELD_CREATED_AT,
    FIELD_UPDATED_AT,
)
RAG_DOCUMENT_SELECT_COLUMNS_SQL = ", ".join(RAG_DOCUMENT_COLUMNS)
RAG_CHUNK_SELECT_COLUMNS_SQL = ", ".join(RAG_CHUNK_COLUMNS)
RAG_RETRIEVAL_SELECT_COLUMNS_SQL = ", ".join(RAG_RETRIEVAL_COLUMNS)
RAG_DOCUMENT_INSERT_COLUMNS_SQL = ", ".join(RAG_DOCUMENT_COLUMNS)
RAG_CHUNK_INSERT_COLUMNS_SQL = ", ".join(RAG_CHUNK_COLUMNS)
RAG_RETRIEVAL_INSERT_COLUMNS_SQL = ", ".join(RAG_RETRIEVAL_COLUMNS)
RAG_DOCUMENT_INSERT_PLACEHOLDERS_SQL = ", ".join("?" for _ in RAG_DOCUMENT_COLUMNS)
RAG_CHUNK_INSERT_PLACEHOLDERS_SQL = ", ".join("?" for _ in RAG_CHUNK_COLUMNS)
RAG_RETRIEVAL_INSERT_PLACEHOLDERS_SQL = ", ".join("?" for _ in RAG_RETRIEVAL_COLUMNS)
UPSERT_RAG_DOCUMENT_SQL = f"""
    INSERT INTO {TABLE_RAG_DOCUMENTS} ({RAG_DOCUMENT_INSERT_COLUMNS_SQL})
    VALUES ({RAG_DOCUMENT_INSERT_PLACEHOLDERS_SQL})
    ON CONFLICT(owner_id, document_id) DO UPDATE SET
        visibility = excluded.visibility,
        source_type = excluded.source_type,
        source_label = excluded.source_label,
        content_summary = excluded.content_summary,
        source_version = excluded.source_version,
        index_status = excluded.index_status,
        failure_reason = excluded.failure_reason,
        updated_at = excluded.updated_at
"""
INSERT_RAG_CHUNK_SQL = f"""
    INSERT INTO {TABLE_RAG_CHUNKS} ({RAG_CHUNK_INSERT_COLUMNS_SQL})
    VALUES ({RAG_CHUNK_INSERT_PLACEHOLDERS_SQL})
"""
INSERT_RAG_RETRIEVAL_SQL = f"""
    INSERT INTO {TABLE_RAG_RETRIEVAL_RECORDS} ({RAG_RETRIEVAL_INSERT_COLUMNS_SQL})
    VALUES ({RAG_RETRIEVAL_INSERT_PLACEHOLDERS_SQL})
"""
RAG_WRITE_FAILURE = "rag record was not persisted"


class InterviewRecordStore:
    """保存、恢复、历史、复盘和导出追踪的最小 sqlite3 adapter。"""

    def __init__(self, database_path: str) -> None:
        """创建绑定到单个 SQLite 数据库路径的 store。"""
        self.database_path = database_path

    def initialize(self) -> None:
        """在显式 app startup 或测试边界加载 R0 schema。"""
        with self._connect() as connection:
            connection.executescript(_load_schema_sql())

    def create_record(
        self,
        *,
        owner_id: str,
        source: str,
        version: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """持久化一条 interview record 并返回保存后的表示。"""
        now = _utc_now()
        record_id = str(uuid4())
        with self._connect() as connection:
            connection.execute(
                INSERT_RECORD_SQL,
                (
                    record_id,
                    owner_id,
                    source,
                    version,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )
        record = self.get_record(record_id)
        if record is None:
            raise RuntimeError(PERSISTENCE_WRITE_FAILURE)
        return record

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        """按稳定 id 读取一条 interview record。"""
        with self._connect() as connection:
            row = connection.execute(SELECT_RECORD_SQL, (record_id,)).fetchone()
        if row is None:
            return None
        return _row_to_record(row)

    def list_records(self, *, owner_id: str | None = None) -> list[dict[str, Any]]:
        """返回最小历史摘要，可按 owner_id 收敛范围。"""
        query = SELECT_RECORDS_SQL
        params: tuple[str, ...] = ()
        if owner_id:
            query = SELECT_RECORDS_BY_OWNER_SQL
            params = (owner_id,)
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_record_summary(_row_to_record(row)) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        # 每次操作单独持有连接，避免测试和 runtime 跨请求共享可变连接状态。
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


class TraceabilityStore:
    """R1 最小数据追踪 sqlite3 adapter。"""

    def __init__(self, database_path: str) -> None:
        """创建绑定到单个 SQLite 数据库路径的 store。"""
        self.database_path = database_path

    def initialize(self) -> None:
        """在显式测试或 runtime 边界加载现有 schema 文件。"""
        with self._connect() as connection:
            connection.executescript(_load_schema_sql())

    def create_trace(self, record: TraceabilityRecord) -> dict[str, Any]:
        """持久化一条 traceability record 并返回保存后的表示。"""
        now = _utc_now()
        record_id = str(uuid4())
        with self._connect() as connection:
            connection.execute(
                INSERT_TRACE_SQL,
                (
                    record_id,
                    record.owner_id,
                    record.trace_type,
                    str(record.status),
                    record.request_id,
                    record.operation_id,
                    record.job_ref,
                    record.resume_ref,
                    record.session_ref,
                    record.turn_ref,
                    record.answer_ref,
                    record.score_ref,
                    record.review_ref,
                    record.export_ref,
                    record.retrieval_query_ref,
                    record.retrieval_result_ref,
                    json.dumps(list(record.citation_refs), ensure_ascii=False),
                    json.dumps(list(record.evidence_refs), ensure_ascii=False),
                    record.evidence_gap_ref,
                    record.source_snapshot_ref,
                    record.schema_version,
                    record.content_version,
                    int(record.retryable),
                    record.failure_reason,
                    json.dumps(record.metadata, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )
        saved = self.get_trace(record_id)
        if saved is None:
            raise RuntimeError(TRACEABILITY_WRITE_FAILURE)
        return saved

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        """按 id 读取一条 traceability record。"""
        with self._connect() as connection:
            row = connection.execute(SELECT_TRACE_SQL, (trace_id,)).fetchone()
        if row is None:
            return None
        return _trace_row_to_record(row)

    def list_traces(
        self,
        *,
        owner_id: str,
        trace_type: str | None = None,
        session_ref: str | None = None,
    ) -> list[dict[str, Any]]:
        """按 owner_id 收敛读取 traceability records，可选按类型和 session 过滤。"""
        clauses = [f"{FIELD_OWNER_ID} = ?"]
        params: list[str] = [owner_id]
        if trace_type:
            clauses.append("trace_type = ?")
            params.append(trace_type)
        if session_ref:
            clauses.append("session_ref = ?")
            params.append(session_ref)

        query = f"""
            SELECT {TRACEABILITY_SELECT_COLUMNS_SQL}
            FROM {TABLE_TRACEABILITY_RECORDS}
            WHERE {" AND ".join(clauses)}
            ORDER BY {FIELD_CREATED_AT} ASC, {FIELD_ID} ASC
        """
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [_trace_row_to_record(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


class RAGPersistenceStore:
    """R1 RAG 文档、chunk、检索结果与 trace 关联的最小 sqlite3 adapter。"""

    def __init__(self, database_path: str) -> None:
        """创建绑定到单个 SQLite 数据库路径的 store。"""
        self.database_path = database_path

    def initialize(self) -> None:
        """在显式测试或 runtime 边界加载现有 schema 文件。"""
        with self._connect() as connection:
            connection.executescript(_load_schema_sql())

    def save_document(
        self,
        document: KnowledgeDocument,
        *,
        chunks: Sequence[KnowledgeResource],
    ) -> dict[str, Any]:
        """保存一个最小 knowledge document 摘要和对应 deterministic chunks。"""
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                UPSERT_RAG_DOCUMENT_SQL,
                (
                    str(uuid4()),
                    document.owner_id,
                    document.document_id,
                    str(document.visibility),
                    str(document.source_type),
                    document.source_label,
                    _rag_content_summary(document.content),
                    document.source_version,
                    str(document.index_status),
                    document.failure_reason,
                    now,
                    now,
                ),
            )
            connection.execute(
                f"""
                    DELETE FROM {TABLE_RAG_CHUNKS}
                    WHERE {FIELD_OWNER_ID} = ? AND document_id = ?
                """,
                (document.owner_id, document.document_id),
            )
            for chunk in chunks:
                connection.execute(
                    INSERT_RAG_CHUNK_SQL,
                    (
                        str(uuid4()),
                        chunk.owner_id,
                        document.document_id,
                        chunk.resource_id,
                        chunk.chunk_ref,
                        chunk.chunk_index,
                        str(chunk.visibility),
                        str(chunk.source_type),
                        chunk.source_label,
                        chunk.content_summary,
                        chunk.source_version,
                        chunk.start_offset,
                        chunk.end_offset,
                        str(chunk.index_status),
                        chunk.failure_reason,
                        now,
                        now,
                    ),
                )
        saved = self.get_document(owner_id=document.owner_id, document_id=document.document_id)
        if saved is None:
            raise RuntimeError(RAG_WRITE_FAILURE)
        return saved

    def get_document(self, *, owner_id: str, document_id: str) -> dict[str, Any] | None:
        """按 owner_id 和 document_id 收敛读取 knowledge document。"""
        query = f"""
            SELECT {RAG_DOCUMENT_SELECT_COLUMNS_SQL}
            FROM {TABLE_RAG_DOCUMENTS}
            WHERE {FIELD_OWNER_ID} = ? AND document_id = ?
        """
        with self._connect() as connection:
            row = connection.execute(query, (owner_id, document_id)).fetchone()
        if row is None:
            return None
        return _rag_document_row_to_record(row)

    def list_documents(self, *, owner_id: str) -> list[dict[str, Any]]:
        """按 owner_id 列出最小 knowledge document 摘要。"""
        query = f"""
            SELECT {RAG_DOCUMENT_SELECT_COLUMNS_SQL}
            FROM {TABLE_RAG_DOCUMENTS}
            WHERE {FIELD_OWNER_ID} = ?
            ORDER BY {FIELD_UPDATED_AT} DESC, document_id ASC
        """
        with self._connect() as connection:
            rows = connection.execute(query, (owner_id,)).fetchall()
        return [_rag_document_row_to_record(row) for row in rows]

    def list_chunks(self, *, owner_id: str, document_id: str) -> list[dict[str, Any]]:
        """按 owner_id 和 document_id 收敛读取 chunk 摘要。"""
        query = f"""
            SELECT {RAG_CHUNK_SELECT_COLUMNS_SQL}
            FROM {TABLE_RAG_CHUNKS}
            WHERE {FIELD_OWNER_ID} = ? AND document_id = ?
            ORDER BY chunk_index ASC, chunk_ref ASC
        """
        with self._connect() as connection:
            rows = connection.execute(query, (owner_id, document_id)).fetchall()
        return [_rag_chunk_row_to_record(row) for row in rows]

    def search(self, query_summary: RetrievalQuerySummary) -> Sequence[KnowledgeResource]:
        """用持久化 chunk 执行本地 keyword / substring retrieval。"""
        rows = self._candidate_chunk_rows(query_summary)
        resources = [_rag_chunk_row_to_resource(row) for row in rows]
        selected_ids = set(query_summary.selected_resource_ids)
        if selected_ids:
            return resources[: query_summary.top_k]

        tokens = _rag_query_tokens(query_summary.query_summary)
        if not tokens:
            return resources[: query_summary.top_k]
        return [
            resource
            for resource in resources
            if any(token in resource.content_summary.lower() for token in tokens)
        ][: query_summary.top_k]

    def create_retrieval_record(
        self,
        *,
        owner_id: str,
        query_summary: RetrievalQuerySummary,
        result: RAGFoundationResult,
        trace_ref: str | None,
        request_id: str,
        operation_id: str,
        session_ref: str | None = None,
        turn_ref: str | None = None,
        answer_ref: str | None = None,
    ) -> dict[str, Any]:
        """保存一次 retrieval 的安全摘要、citation refs 与 evidence gap ref。"""
        now = _utc_now()
        record_id = str(uuid4())
        gap_reason = result.evidence_gap.reason if result.evidence_gap is not None else None
        retrieval_query_ref = f"rag-query:{query_summary.query_summary}"
        retrieval_result_ref = f"rag-result:{result.result_summary.hit_count}:{gap_reason or 'hit'}"
        with self._connect() as connection:
            connection.execute(
                INSERT_RAG_RETRIEVAL_SQL,
                (
                    record_id,
                    owner_id,
                    trace_ref,
                    request_id,
                    operation_id,
                    session_ref,
                    turn_ref,
                    answer_ref,
                    retrieval_query_ref,
                    retrieval_result_ref,
                    query_summary.query_summary,
                    query_summary.top_k,
                    query_summary.trigger,
                    query_summary.visibility_filter,
                    result.result_summary.hit_count,
                    json.dumps(list(result.result_summary.hit_summary), ensure_ascii=False),
                    result.result_summary.empty_reason,
                    int(result.degraded or result.result_summary.degraded),
                    int(result.result_summary.retryable),
                    json.dumps(
                        [citation.citation_ref for citation in result.citations],
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        [item.evidence_ref for item in result.evidence_items],
                        ensure_ascii=False,
                    ),
                    f"gap:{gap_reason}" if gap_reason else None,
                    _rag_source_snapshot_ref(result),
                    result.permission_filtered_count,
                    now,
                    now,
                ),
            )
        saved = self.get_retrieval_record(record_id)
        if saved is None:
            raise RuntimeError(RAG_WRITE_FAILURE)
        return saved

    def get_retrieval_record(self, record_id: str) -> dict[str, Any] | None:
        """按稳定 id 读取一条 RAG retrieval record。"""
        query = f"""
            SELECT {RAG_RETRIEVAL_SELECT_COLUMNS_SQL}
            FROM {TABLE_RAG_RETRIEVAL_RECORDS}
            WHERE {FIELD_ID} = ?
        """
        with self._connect() as connection:
            row = connection.execute(query, (record_id,)).fetchone()
        if row is None:
            return None
        return _rag_retrieval_row_to_record(row)

    def list_retrieval_records(
        self,
        *,
        owner_id: str,
        session_ref: str | None = None,
    ) -> list[dict[str, Any]]:
        """按 owner_id 收敛读取 retrieval records，可选按 session 过滤。"""
        clauses = [f"{FIELD_OWNER_ID} = ?"]
        params: list[str] = [owner_id]
        if session_ref:
            clauses.append("session_ref = ?")
            params.append(session_ref)
        query = f"""
            SELECT {RAG_RETRIEVAL_SELECT_COLUMNS_SQL}
            FROM {TABLE_RAG_RETRIEVAL_RECORDS}
            WHERE {" AND ".join(clauses)}
            ORDER BY {FIELD_CREATED_AT} ASC, {FIELD_ID} ASC
        """
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [_rag_retrieval_row_to_record(row) for row in rows]

    def _candidate_chunk_rows(self, query_summary: RetrievalQuerySummary) -> list[sqlite3.Row]:
        selected_ids = tuple(query_summary.selected_resource_ids)
        if selected_ids:
            placeholders = ", ".join("?" for _ in selected_ids)
            query = f"""
                SELECT {RAG_CHUNK_SELECT_COLUMNS_SQL}
                FROM {TABLE_RAG_CHUNKS}
                WHERE resource_id IN ({placeholders})
                   OR document_id IN ({placeholders})
                ORDER BY chunk_index ASC, chunk_ref ASC
            """
            params = selected_ids + selected_ids
        else:
            query = f"""
                SELECT {RAG_CHUNK_SELECT_COLUMNS_SQL}
                FROM {TABLE_RAG_CHUNKS}
                ORDER BY {FIELD_UPDATED_AT} DESC, document_id ASC, chunk_index ASC
            """
            params = ()
        with self._connect() as connection:
            return list(connection.execute(query, params).fetchall())

    def _connect(self) -> sqlite3.Connection:
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


def _row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    payload = json.loads(str(row[FIELD_PAYLOAD_JSON]))
    return {
        FIELD_ID: str(row[FIELD_ID]),
        FIELD_OWNER_ID: str(row[FIELD_OWNER_ID]),
        FIELD_SOURCE: str(row[FIELD_SOURCE]),
        FIELD_VERSION: int(row[FIELD_VERSION]),
        FIELD_PAYLOAD: payload,
        FIELD_CREATED_AT: str(row[FIELD_CREATED_AT]),
        FIELD_UPDATED_AT: str(row[FIELD_UPDATED_AT]),
    }


def _trace_row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    return {
        FIELD_ID: str(row[FIELD_ID]),
        FIELD_OWNER_ID: str(row[FIELD_OWNER_ID]),
        "trace_type": str(row["trace_type"]),
        RESPONSE_STATUS: str(row[RESPONSE_STATUS]),
        "request_id": str(row["request_id"]),
        "operation_id": str(row["operation_id"]),
        "job_ref": _optional_string(row["job_ref"]),
        "resume_ref": _optional_string(row["resume_ref"]),
        "session_ref": _optional_string(row["session_ref"]),
        "turn_ref": _optional_string(row["turn_ref"]),
        "answer_ref": _optional_string(row["answer_ref"]),
        "score_ref": _optional_string(row["score_ref"]),
        "review_ref": _optional_string(row["review_ref"]),
        "export_ref": _optional_string(row["export_ref"]),
        "retrieval_query_ref": _optional_string(row["retrieval_query_ref"]),
        "retrieval_result_ref": _optional_string(row["retrieval_result_ref"]),
        "citation_refs": json.loads(str(row["citation_refs_json"])),
        "evidence_refs": json.loads(str(row["evidence_refs_json"])),
        "evidence_gap_ref": _optional_string(row["evidence_gap_ref"]),
        "source_snapshot_ref": _optional_string(row["source_snapshot_ref"]),
        "schema_version": int(row["schema_version"]),
        "content_version": _optional_string(row["content_version"]),
        "retryable": bool(row["retryable"]),
        "failure_reason": _optional_string(row["failure_reason"]),
        "metadata": json.loads(str(row["metadata_json"])),
        FIELD_CREATED_AT: str(row[FIELD_CREATED_AT]),
        FIELD_UPDATED_AT: str(row[FIELD_UPDATED_AT]),
    }


def _rag_document_row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    from app.rag.models import KnowledgeIndexStatus, KnowledgeVisibility, RAGSourceType

    return {
        FIELD_ID: str(row[FIELD_ID]),
        FIELD_OWNER_ID: str(row[FIELD_OWNER_ID]),
        "document_id": str(row["document_id"]),
        "visibility": KnowledgeVisibility(str(row["visibility"])),
        "source_type": RAGSourceType(str(row["source_type"])),
        "source_label": str(row["source_label"]),
        "content_summary": str(row["content_summary"]),
        "source_version": str(row["source_version"]),
        "index_status": KnowledgeIndexStatus(str(row["index_status"])),
        "failure_reason": _optional_string(row["failure_reason"]),
        FIELD_CREATED_AT: str(row[FIELD_CREATED_AT]),
        FIELD_UPDATED_AT: str(row[FIELD_UPDATED_AT]),
    }


def _rag_chunk_row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    from app.rag.models import KnowledgeIndexStatus, KnowledgeVisibility, RAGSourceType

    return {
        FIELD_ID: str(row[FIELD_ID]),
        FIELD_OWNER_ID: str(row[FIELD_OWNER_ID]),
        "document_id": str(row["document_id"]),
        "resource_id": str(row["resource_id"]),
        "chunk_ref": str(row["chunk_ref"]),
        "chunk_index": int(row["chunk_index"]),
        "visibility": KnowledgeVisibility(str(row["visibility"])),
        "source_type": RAGSourceType(str(row["source_type"])),
        "source_label": str(row["source_label"]),
        "content_summary": str(row["content_summary"]),
        "source_version": str(row["source_version"]),
        "start_offset": int(row["start_offset"]),
        "end_offset": int(row["end_offset"]),
        "index_status": KnowledgeIndexStatus(str(row["index_status"])),
        "failure_reason": _optional_string(row["failure_reason"]),
        FIELD_CREATED_AT: str(row[FIELD_CREATED_AT]),
        FIELD_UPDATED_AT: str(row[FIELD_UPDATED_AT]),
    }


def _rag_retrieval_row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    return {
        FIELD_ID: str(row[FIELD_ID]),
        FIELD_OWNER_ID: str(row[FIELD_OWNER_ID]),
        "trace_ref": _optional_string(row["trace_ref"]),
        "request_id": str(row["request_id"]),
        "operation_id": str(row["operation_id"]),
        "session_ref": _optional_string(row["session_ref"]),
        "turn_ref": _optional_string(row["turn_ref"]),
        "answer_ref": _optional_string(row["answer_ref"]),
        "retrieval_query_ref": str(row["retrieval_query_ref"]),
        "retrieval_result_ref": str(row["retrieval_result_ref"]),
        "query_summary": str(row["query_summary"]),
        "top_k": int(row["top_k"]),
        "trigger": str(row["trigger"]),
        "visibility_filter": str(row["visibility_filter"]),
        "hit_count": int(row["hit_count"]),
        "hit_summary": json.loads(str(row["hit_summary_json"])),
        "empty_reason": _optional_string(row["empty_reason"]),
        "degraded": bool(row["degraded"]),
        "retryable": bool(row["retryable"]),
        "citation_refs": json.loads(str(row["citation_refs_json"])),
        "evidence_refs": json.loads(str(row["evidence_refs_json"])),
        "evidence_gap_ref": _optional_string(row["evidence_gap_ref"]),
        "source_snapshot_ref": _optional_string(row["source_snapshot_ref"]),
        "permission_filtered_count": int(row["permission_filtered_count"]),
        FIELD_CREATED_AT: str(row[FIELD_CREATED_AT]),
        FIELD_UPDATED_AT: str(row[FIELD_UPDATED_AT]),
    }


def _rag_chunk_row_to_resource(row: sqlite3.Row) -> KnowledgeResource:
    from app.rag.models import (
        KnowledgeIndexStatus,
        KnowledgeResource,
        KnowledgeVisibility,
        RAGSourceType,
    )

    return KnowledgeResource(
        resource_id=str(row["resource_id"]),
        owner_id=str(row[FIELD_OWNER_ID]),
        visibility=KnowledgeVisibility(str(row["visibility"])),
        source_type=RAGSourceType(str(row["source_type"])),
        source_label=str(row["source_label"]),
        content_summary=str(row["content_summary"]),
        chunk_ref=str(row["chunk_ref"]),
        source_version=str(row["source_version"]),
        index_status=KnowledgeIndexStatus(str(row["index_status"])),
        chunk_index=int(row["chunk_index"]),
        start_offset=int(row["start_offset"]),
        end_offset=int(row["end_offset"]),
        failure_reason=_optional_string(row["failure_reason"]),
    )


def _record_summary(record: dict[str, Any]) -> dict[str, Any]:
    payload = record[FIELD_PAYLOAD] if isinstance(record.get(FIELD_PAYLOAD), dict) else {}
    interview = payload.get(PAYLOAD_INTERVIEW)
    interview = interview if isinstance(interview, dict) else {}
    return {
        FIELD_ID: record[FIELD_ID],
        FIELD_OWNER_ID: record[FIELD_OWNER_ID],
        FIELD_SOURCE: record[FIELD_SOURCE],
        FIELD_VERSION: record[FIELD_VERSION],
        RESPONSE_STATUS: str(interview.get(RESPONSE_STATUS) or DEFAULT_HISTORY_STATUS),
        FIELD_CREATED_AT: record[FIELD_CREATED_AT],
        FIELD_UPDATED_AT: record[FIELD_UPDATED_AT],
        RESPONSE_REVIEW_AVAILABLE: isinstance(payload.get(PAYLOAD_REVIEW), dict),
        RESPONSE_EXPORT_TRACE_AVAILABLE: isinstance(payload.get(PAYLOAD_EXPORT), dict),
    }


def _load_schema_sql() -> str:
    return "\n\n".join(
        schema_path.read_text(encoding="utf-8")
        for schema_path in (SCHEMA_PATH, TRACEABILITY_SCHEMA_PATH, RAG_SCHEMA_PATH)
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _rag_content_summary(content: str) -> str:
    return " ".join(content.split())[:RAG_CONTENT_SUMMARY_MAX_LENGTH]


def _rag_query_tokens(query_summary: str) -> tuple[str, ...]:
    return tuple(token for token in query_summary.lower().split() if token)


def _rag_source_snapshot_ref(result: RAGFoundationResult) -> str | None:
    refs = [item.source_snapshot_ref for item in result.evidence_items]
    return ",".join(refs) if refs else None
