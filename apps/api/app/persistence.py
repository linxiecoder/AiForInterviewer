"""ST13_20 持久化边界的 SQLite adapter。"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    insert,
    or_,
    select,
)
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine, URL
from sqlalchemy.pool import StaticPool

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
RAG_WRITE_FAILURE = "rag record was not persisted"
SQL_METADATA = MetaData()
INTEGER_SQL_COLUMNS = {
    FIELD_VERSION,
    "schema_version",
    "retryable",
    "chunk_index",
    "start_offset",
    "end_offset",
    "top_k",
    "hit_count",
    "degraded",
    "permission_filtered_count",
}


def _sql_column(column_name: str) -> Column[Any]:
    column_type = Integer if column_name in INTEGER_SQL_COLUMNS else String
    return Column(column_name, column_type)


INTERVIEW_RECORDS_TABLE = Table(
    TABLE_INTERVIEW_RECORDS,
    SQL_METADATA,
    *(_sql_column(column_name) for column_name in SQL_COLUMNS),
)
TRACEABILITY_RECORDS_TABLE = Table(
    TABLE_TRACEABILITY_RECORDS,
    SQL_METADATA,
    *(_sql_column(column_name) for column_name in TRACEABILITY_COLUMNS),
)
RAG_DOCUMENTS_TABLE = Table(
    TABLE_RAG_DOCUMENTS,
    SQL_METADATA,
    *(_sql_column(column_name) for column_name in RAG_DOCUMENT_COLUMNS),
)
RAG_CHUNKS_TABLE = Table(
    TABLE_RAG_CHUNKS,
    SQL_METADATA,
    *(_sql_column(column_name) for column_name in RAG_CHUNK_COLUMNS),
)
RAG_RETRIEVAL_RECORDS_TABLE = Table(
    TABLE_RAG_RETRIEVAL_RECORDS,
    SQL_METADATA,
    *(_sql_column(column_name) for column_name in RAG_RETRIEVAL_COLUMNS),
)


class InterviewRecordStore:
    """保存、恢复、历史、复盘和导出追踪的最小 SQLite adapter。"""

    def __init__(self, database_path: str) -> None:
        """创建绑定到单个 SQLite 数据库路径的 store。"""
        self.database_path = database_path
        self._engine = _create_sqlite_engine(database_path)

    def initialize(self) -> None:
        """在显式 app startup 或测试边界加载 R0 schema。"""
        _initialize_schema(self._engine)

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
        values = {
            FIELD_ID: record_id,
            FIELD_OWNER_ID: owner_id,
            FIELD_SOURCE: source,
            FIELD_VERSION: version,
            FIELD_PAYLOAD_JSON: json.dumps(payload, ensure_ascii=False, sort_keys=True),
            FIELD_CREATED_AT: now,
            FIELD_UPDATED_AT: now,
        }
        with self._engine.begin() as connection:
            connection.execute(insert(INTERVIEW_RECORDS_TABLE).values(values))
        record = self.get_record(record_id)
        if record is None:
            raise RuntimeError(PERSISTENCE_WRITE_FAILURE)
        return record

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        """按稳定 id 读取一条 interview record。"""
        statement = select(*_table_columns(INTERVIEW_RECORDS_TABLE, SQL_COLUMNS)).where(
            INTERVIEW_RECORDS_TABLE.c[FIELD_ID] == record_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().fetchone()
        if row is None:
            return None
        return _row_to_record(row)

    def list_records(self, *, owner_id: str | None = None) -> list[dict[str, Any]]:
        """返回最小历史摘要，可按 owner_id 收敛范围。"""
        statement = select(*_table_columns(INTERVIEW_RECORDS_TABLE, SQL_COLUMNS)).order_by(
            INTERVIEW_RECORDS_TABLE.c[FIELD_CREATED_AT].desc(),
            INTERVIEW_RECORDS_TABLE.c[FIELD_ID].desc(),
        )
        if owner_id:
            statement = statement.where(INTERVIEW_RECORDS_TABLE.c[FIELD_OWNER_ID] == owner_id)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().fetchall()
        return [_record_summary(_row_to_record(row)) for row in rows]


class TraceabilityStore:
    """R1 最小数据追踪 SQLite adapter。"""

    def __init__(self, database_path: str) -> None:
        """创建绑定到单个 SQLite 数据库路径的 store。"""
        self.database_path = database_path
        self._engine = _create_sqlite_engine(database_path)

    def initialize(self) -> None:
        """在显式测试或 runtime 边界加载现有 schema 文件。"""
        _initialize_schema(self._engine)

    def create_trace(self, record: TraceabilityRecord) -> dict[str, Any]:
        """持久化一条 traceability record 并返回保存后的表示。"""
        now = _utc_now()
        record_id = str(uuid4())
        values = {
            FIELD_ID: record_id,
            FIELD_OWNER_ID: record.owner_id,
            "trace_type": record.trace_type,
            RESPONSE_STATUS: str(record.status),
            "request_id": record.request_id,
            "operation_id": record.operation_id,
            "job_ref": record.job_ref,
            "resume_ref": record.resume_ref,
            "session_ref": record.session_ref,
            "turn_ref": record.turn_ref,
            "answer_ref": record.answer_ref,
            "score_ref": record.score_ref,
            "review_ref": record.review_ref,
            "export_ref": record.export_ref,
            "retrieval_query_ref": record.retrieval_query_ref,
            "retrieval_result_ref": record.retrieval_result_ref,
            "citation_refs_json": json.dumps(list(record.citation_refs), ensure_ascii=False),
            "evidence_refs_json": json.dumps(list(record.evidence_refs), ensure_ascii=False),
            "evidence_gap_ref": record.evidence_gap_ref,
            "source_snapshot_ref": record.source_snapshot_ref,
            "schema_version": record.schema_version,
            "content_version": record.content_version,
            "retryable": int(record.retryable),
            "failure_reason": record.failure_reason,
            "metadata_json": json.dumps(record.metadata, ensure_ascii=False, sort_keys=True),
            FIELD_CREATED_AT: now,
            FIELD_UPDATED_AT: now,
        }
        with self._engine.begin() as connection:
            connection.execute(insert(TRACEABILITY_RECORDS_TABLE).values(values))
        saved = self.get_trace(record_id)
        if saved is None:
            raise RuntimeError(TRACEABILITY_WRITE_FAILURE)
        return saved

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        """按 id 读取一条 traceability record。"""
        statement = select(*_table_columns(TRACEABILITY_RECORDS_TABLE, TRACEABILITY_COLUMNS)).where(
            TRACEABILITY_RECORDS_TABLE.c[FIELD_ID] == trace_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().fetchone()
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
        conditions = [TRACEABILITY_RECORDS_TABLE.c[FIELD_OWNER_ID] == owner_id]
        if trace_type:
            conditions.append(TRACEABILITY_RECORDS_TABLE.c["trace_type"] == trace_type)
        if session_ref:
            conditions.append(TRACEABILITY_RECORDS_TABLE.c["session_ref"] == session_ref)

        statement = (
            select(*_table_columns(TRACEABILITY_RECORDS_TABLE, TRACEABILITY_COLUMNS))
            .where(*conditions)
            .order_by(
                TRACEABILITY_RECORDS_TABLE.c[FIELD_CREATED_AT].asc(),
                TRACEABILITY_RECORDS_TABLE.c[FIELD_ID].asc(),
            )
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().fetchall()
        return [_trace_row_to_record(row) for row in rows]


class RAGPersistenceStore:
    """R1 RAG 文档、chunk、检索结果与 trace 关联的最小 SQLite adapter。"""

    def __init__(self, database_path: str) -> None:
        """创建绑定到单个 SQLite 数据库路径的 store。"""
        self.database_path = database_path
        self._engine = _create_sqlite_engine(database_path)

    def initialize(self) -> None:
        """在显式测试或 runtime 边界加载现有 schema 文件。"""
        _initialize_schema(self._engine)

    def save_document(
        self,
        document: KnowledgeDocument,
        *,
        chunks: Sequence[KnowledgeResource],
    ) -> dict[str, Any]:
        """保存一个最小 knowledge document 摘要和对应 deterministic chunks。"""
        now = _utc_now()
        document_values = {
            FIELD_ID: str(uuid4()),
            FIELD_OWNER_ID: document.owner_id,
            "document_id": document.document_id,
            "visibility": str(document.visibility),
            "source_type": str(document.source_type),
            "source_label": document.source_label,
            "content_summary": _rag_content_summary(document.content),
            "source_version": document.source_version,
            "index_status": str(document.index_status),
            "failure_reason": document.failure_reason,
            FIELD_CREATED_AT: now,
            FIELD_UPDATED_AT: now,
        }
        document_insert = sqlite_insert(RAG_DOCUMENTS_TABLE).values(document_values)
        document_upsert = document_insert.on_conflict_do_update(
            index_elements=[
                RAG_DOCUMENTS_TABLE.c[FIELD_OWNER_ID],
                RAG_DOCUMENTS_TABLE.c["document_id"],
            ],
            set_={
                "visibility": document_insert.excluded.visibility,
                "source_type": document_insert.excluded.source_type,
                "source_label": document_insert.excluded.source_label,
                "content_summary": document_insert.excluded.content_summary,
                "source_version": document_insert.excluded.source_version,
                "index_status": document_insert.excluded.index_status,
                "failure_reason": document_insert.excluded.failure_reason,
                FIELD_UPDATED_AT: document_insert.excluded.updated_at,
            },
        )
        delete_chunks = delete(RAG_CHUNKS_TABLE).where(
            RAG_CHUNKS_TABLE.c[FIELD_OWNER_ID] == document.owner_id,
            RAG_CHUNKS_TABLE.c["document_id"] == document.document_id,
        )
        chunk_values = [
            {
                FIELD_ID: str(uuid4()),
                FIELD_OWNER_ID: chunk.owner_id,
                "document_id": document.document_id,
                "resource_id": chunk.resource_id,
                "chunk_ref": chunk.chunk_ref,
                "chunk_index": chunk.chunk_index,
                "visibility": str(chunk.visibility),
                "source_type": str(chunk.source_type),
                "source_label": chunk.source_label,
                "content_summary": chunk.content_summary,
                "source_version": chunk.source_version,
                "start_offset": chunk.start_offset,
                "end_offset": chunk.end_offset,
                "index_status": str(chunk.index_status),
                "failure_reason": chunk.failure_reason,
                FIELD_CREATED_AT: now,
                FIELD_UPDATED_AT: now,
            }
            for chunk in chunks
        ]
        with self._engine.begin() as connection:
            connection.execute(document_upsert)
            connection.execute(delete_chunks)
            if chunk_values:
                connection.execute(insert(RAG_CHUNKS_TABLE), chunk_values)
        saved = self.get_document(owner_id=document.owner_id, document_id=document.document_id)
        if saved is None:
            raise RuntimeError(RAG_WRITE_FAILURE)
        return saved

    def get_document(self, *, owner_id: str, document_id: str) -> dict[str, Any] | None:
        """按 owner_id 和 document_id 收敛读取 knowledge document。"""
        statement = select(*_table_columns(RAG_DOCUMENTS_TABLE, RAG_DOCUMENT_COLUMNS)).where(
            RAG_DOCUMENTS_TABLE.c[FIELD_OWNER_ID] == owner_id,
            RAG_DOCUMENTS_TABLE.c["document_id"] == document_id,
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().fetchone()
        if row is None:
            return None
        return _rag_document_row_to_record(row)

    def list_documents(self, *, owner_id: str) -> list[dict[str, Any]]:
        """按 owner_id 列出最小 knowledge document 摘要。"""
        statement = (
            select(*_table_columns(RAG_DOCUMENTS_TABLE, RAG_DOCUMENT_COLUMNS))
            .where(RAG_DOCUMENTS_TABLE.c[FIELD_OWNER_ID] == owner_id)
            .order_by(
                RAG_DOCUMENTS_TABLE.c[FIELD_UPDATED_AT].desc(),
                RAG_DOCUMENTS_TABLE.c["document_id"].asc(),
            )
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().fetchall()
        return [_rag_document_row_to_record(row) for row in rows]

    def list_chunks(self, *, owner_id: str, document_id: str) -> list[dict[str, Any]]:
        """按 owner_id 和 document_id 收敛读取 chunk 摘要。"""
        statement = (
            select(*_table_columns(RAG_CHUNKS_TABLE, RAG_CHUNK_COLUMNS))
            .where(
                RAG_CHUNKS_TABLE.c[FIELD_OWNER_ID] == owner_id,
                RAG_CHUNKS_TABLE.c["document_id"] == document_id,
            )
            .order_by(
                RAG_CHUNKS_TABLE.c["chunk_index"].asc(),
                RAG_CHUNKS_TABLE.c["chunk_ref"].asc(),
            )
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().fetchall()
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
        values = {
            FIELD_ID: record_id,
            FIELD_OWNER_ID: owner_id,
            "trace_ref": trace_ref,
            "request_id": request_id,
            "operation_id": operation_id,
            "session_ref": session_ref,
            "turn_ref": turn_ref,
            "answer_ref": answer_ref,
            "retrieval_query_ref": retrieval_query_ref,
            "retrieval_result_ref": retrieval_result_ref,
            "query_summary": query_summary.query_summary,
            "top_k": query_summary.top_k,
            "trigger": query_summary.trigger,
            "visibility_filter": query_summary.visibility_filter,
            "hit_count": result.result_summary.hit_count,
            "hit_summary_json": json.dumps(
                list(result.result_summary.hit_summary), ensure_ascii=False
            ),
            "empty_reason": result.result_summary.empty_reason,
            "degraded": int(result.degraded or result.result_summary.degraded),
            "retryable": int(result.result_summary.retryable),
            "citation_refs_json": json.dumps(
                [citation.citation_ref for citation in result.citations],
                ensure_ascii=False,
            ),
            "evidence_refs_json": json.dumps(
                [item.evidence_ref for item in result.evidence_items],
                ensure_ascii=False,
            ),
            "evidence_gap_ref": f"gap:{gap_reason}" if gap_reason else None,
            "source_snapshot_ref": _rag_source_snapshot_ref(result),
            "permission_filtered_count": result.permission_filtered_count,
            FIELD_CREATED_AT: now,
            FIELD_UPDATED_AT: now,
        }
        with self._engine.begin() as connection:
            connection.execute(insert(RAG_RETRIEVAL_RECORDS_TABLE).values(values))
        saved = self.get_retrieval_record(record_id)
        if saved is None:
            raise RuntimeError(RAG_WRITE_FAILURE)
        return saved

    def get_retrieval_record(self, record_id: str) -> dict[str, Any] | None:
        """按稳定 id 读取一条 RAG retrieval record。"""
        statement = select(
            *_table_columns(RAG_RETRIEVAL_RECORDS_TABLE, RAG_RETRIEVAL_COLUMNS)
        ).where(RAG_RETRIEVAL_RECORDS_TABLE.c[FIELD_ID] == record_id)
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().fetchone()
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
        conditions = [RAG_RETRIEVAL_RECORDS_TABLE.c[FIELD_OWNER_ID] == owner_id]
        if session_ref:
            conditions.append(RAG_RETRIEVAL_RECORDS_TABLE.c["session_ref"] == session_ref)
        statement = (
            select(*_table_columns(RAG_RETRIEVAL_RECORDS_TABLE, RAG_RETRIEVAL_COLUMNS))
            .where(*conditions)
            .order_by(
                RAG_RETRIEVAL_RECORDS_TABLE.c[FIELD_CREATED_AT].asc(),
                RAG_RETRIEVAL_RECORDS_TABLE.c[FIELD_ID].asc(),
            )
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().fetchall()
        return [_rag_retrieval_row_to_record(row) for row in rows]

    def _candidate_chunk_rows(
        self, query_summary: RetrievalQuerySummary
    ) -> list[Mapping[str, Any]]:
        selected_ids = tuple(query_summary.selected_resource_ids)
        if selected_ids:
            statement = (
                select(*_table_columns(RAG_CHUNKS_TABLE, RAG_CHUNK_COLUMNS))
                .where(
                    or_(
                        RAG_CHUNKS_TABLE.c["resource_id"].in_(selected_ids),
                        RAG_CHUNKS_TABLE.c["document_id"].in_(selected_ids),
                    )
                )
                .order_by(
                    RAG_CHUNKS_TABLE.c["chunk_index"].asc(),
                    RAG_CHUNKS_TABLE.c["chunk_ref"].asc(),
                )
            )
        else:
            statement = select(*_table_columns(RAG_CHUNKS_TABLE, RAG_CHUNK_COLUMNS)).order_by(
                RAG_CHUNKS_TABLE.c[FIELD_UPDATED_AT].desc(),
                RAG_CHUNKS_TABLE.c["document_id"].asc(),
                RAG_CHUNKS_TABLE.c["chunk_index"].asc(),
            )
        with self._engine.connect() as connection:
            return list(connection.execute(statement).mappings().fetchall())


def _create_sqlite_engine(database_path: str) -> Engine:
    if database_path == ":memory:":
        return create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(URL.create("sqlite+pysqlite", database=database_path))


def _initialize_schema(engine: Engine) -> None:
    raw_connection = engine.raw_connection()
    try:
        raw_connection.executescript(_load_schema_sql())
        raw_connection.commit()
    finally:
        raw_connection.close()


def _table_columns(table: Table, column_names: Sequence[str]) -> tuple[Column[Any], ...]:
    return tuple(table.c[column_name] for column_name in column_names)


def _row_to_record(row: Mapping[str, Any]) -> dict[str, Any]:
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


def _trace_row_to_record(row: Mapping[str, Any]) -> dict[str, Any]:
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


def _rag_document_row_to_record(row: Mapping[str, Any]) -> dict[str, Any]:
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


def _rag_chunk_row_to_record(row: Mapping[str, Any]) -> dict[str, Any]:
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


def _rag_retrieval_row_to_record(row: Mapping[str, Any]) -> dict[str, Any]:
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


def _rag_chunk_row_to_resource(row: Mapping[str, Any]) -> KnowledgeResource:
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
