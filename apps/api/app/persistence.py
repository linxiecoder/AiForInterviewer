"""SQLite persistence adapter for the ST13_20 R0 interview record boundary."""

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

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "interview_records.sql"
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


class InterviewRecordStore:
    """Minimal sqlite3 adapter for save, restore, history, review, and export trace."""

    def __init__(self, database_path: str) -> None:
        """Create a store bound to one SQLite database path."""
        self.database_path = database_path

    def initialize(self) -> None:
        """Load the R0 schema at an explicit app startup or test boundary."""
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
        """Persist one interview record and return the saved representation."""
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
        """Restore one interview record by its stable id."""
        with self._connect() as connection:
            row = connection.execute(SELECT_RECORD_SQL, (record_id,)).fetchone()
        if row is None:
            return None
        return _row_to_record(row)

    def list_records(self, *, owner_id: str | None = None) -> list[dict[str, Any]]:
        """Return minimal history summaries, optionally scoped by owner_id."""
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
        # Keep connection ownership local to each operation so tests and runtime
        # do not share mutable sqlite connection state across requests.
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
    return SCHEMA_PATH.read_text(encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
