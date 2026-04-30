"""API persistence SQL access layer hardening tests."""

from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import app.persistence as persistence  # noqa: E402


def test_runtime_sql_uses_sqlalchemy_core_table_definitions() -> None:
    """运行时 DML / SELECT 应基于 SQLAlchemy Core Table 定义。"""
    tables = (
        persistence.INTERVIEW_RECORDS_TABLE,
        persistence.TRACEABILITY_RECORDS_TABLE,
        persistence.RAG_DOCUMENTS_TABLE,
        persistence.RAG_CHUNKS_TABLE,
        persistence.RAG_RETRIEVAL_RECORDS_TABLE,
    )

    assert [table.name for table in tables] == [
        "interview_records",
        "traceability_records",
        "rag_documents",
        "rag_chunks",
        "rag_retrieval_records",
    ]
    assert all(hasattr(table, "insert") for table in tables)
    assert all("id" in table.c for table in tables)


def test_legacy_placeholder_sql_constants_are_removed() -> None:
    """业务代码不再维护手写列名 join 和问号 placeholder 顺序。"""
    legacy_names = (
        "SELECT_COLUMNS_SQL",
        "INSERT_COLUMNS_SQL",
        "INSERT_PLACEHOLDERS_SQL",
        "INSERT_RECORD_SQL",
        "SELECT_RECORD_SQL",
        "SELECT_RECORDS_SQL",
        "SELECT_RECORDS_BY_OWNER_SQL",
        "TRACEABILITY_SELECT_COLUMNS_SQL",
        "TRACEABILITY_INSERT_COLUMNS_SQL",
        "TRACEABILITY_INSERT_PLACEHOLDERS_SQL",
        "INSERT_TRACE_SQL",
        "SELECT_TRACE_SQL",
        "RAG_DOCUMENT_SELECT_COLUMNS_SQL",
        "RAG_CHUNK_SELECT_COLUMNS_SQL",
        "RAG_RETRIEVAL_SELECT_COLUMNS_SQL",
        "RAG_DOCUMENT_INSERT_COLUMNS_SQL",
        "RAG_CHUNK_INSERT_COLUMNS_SQL",
        "RAG_RETRIEVAL_INSERT_COLUMNS_SQL",
        "RAG_DOCUMENT_INSERT_PLACEHOLDERS_SQL",
        "RAG_CHUNK_INSERT_PLACEHOLDERS_SQL",
        "RAG_RETRIEVAL_INSERT_PLACEHOLDERS_SQL",
        "UPSERT_RAG_DOCUMENT_SQL",
        "INSERT_RAG_CHUNK_SQL",
        "INSERT_RAG_RETRIEVAL_SQL",
    )

    assert [name for name in legacy_names if hasattr(persistence, name)] == []
