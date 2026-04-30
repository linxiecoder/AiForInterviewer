"""ST13_20 持久化边界的 SQLite adapter。"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
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

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
SCHEMA_PATH = SCHEMA_DIR / "interview_records.sql"
TRACEABILITY_SCHEMA_PATH = SCHEMA_DIR / "traceability_records.sql"
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
        for schema_path in (SCHEMA_PATH, TRACEABILITY_SCHEMA_PATH)
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
