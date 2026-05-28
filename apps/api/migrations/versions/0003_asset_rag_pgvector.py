"""asset rag pgvector"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.types import UserDefinedType

revision = "0003_asset_rag_pgvector"
down_revision = "0002_known_column_backfills"
branch_labels = None
depends_on = None
ASSET_RAG_EMBEDDING_DIMENSION = 1536
RAG_DOCUMENT_COLUMNS = {
    "source_type",
    "source_id",
    "title",
    "metadata_json",
    "id",
    "owner_id",
    "actor_id",
    "record_version",
    "status",
    "created_at",
    "updated_at",
    "trace_ref_ids",
    "evidence_ref_ids",
}
RAG_CHUNK_COLUMNS = {
    "document_id",
    "source_type",
    "source_id",
    "asset_id",
    "chunk_index",
    "heading_path_json",
    "content",
    "char_count",
    "metadata_json",
    "embedding",
    "embedding_model",
    "embedding_dimension",
    "id",
    "owner_id",
    "actor_id",
    "record_version",
    "status",
    "created_at",
    "updated_at",
    "trace_ref_ids",
    "evidence_ref_ids",
}


class PgVector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_kw) -> str:
        return f"vector({self.dimensions})"


def upgrade() -> None:
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"
    if is_postgresql:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    if _current_rag_schema_exists(bind):
        _create_rag_indexes(bind, is_postgresql)
        return

    _preserve_legacy_rag_tables(bind)
    op.create_table(
        "rag_documents",
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_id", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("owner_id", sa.String(length=80), nullable=False),
        sa.Column("actor_id", sa.String(length=80), nullable=True),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trace_ref_ids", sa.JSON(), nullable=True),
        sa.Column("evidence_ref_ids", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "rag_chunks",
        sa.Column("document_id", sa.String(length=80), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_id", sa.String(length=80), nullable=False),
        sa.Column("asset_id", sa.String(length=80), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("heading_path_json", sa.JSON(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "embedding",
            PgVector(ASSET_RAG_EMBEDDING_DIMENSION) if is_postgresql else sa.Text(),
            nullable=False,
        ),
        sa.Column("embedding_model", sa.String(length=160), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("owner_id", sa.String(length=80), nullable=False),
        sa.Column("actor_id", sa.String(length=80), nullable=True),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trace_ref_ids", sa.JSON(), nullable=True),
        sa.Column("evidence_ref_ids", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_rag_indexes(bind, is_postgresql)


def _current_rag_schema_exists(bind) -> bool:
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())
    if not {"rag_documents", "rag_chunks"}.issubset(table_names):
        return False
    document_columns = {column["name"] for column in inspector.get_columns("rag_documents")}
    chunk_columns = {column["name"] for column in inspector.get_columns("rag_chunks")}
    return RAG_DOCUMENT_COLUMNS.issubset(document_columns) and RAG_CHUNK_COLUMNS.issubset(chunk_columns)


def _preserve_legacy_rag_tables(bind) -> None:
    table_names = set(sa.inspect(bind).get_table_names())
    for table_name in ("rag_chunks", "rag_documents"):
        if table_name not in table_names:
            continue
        legacy_name = _available_legacy_table_name(table_name, table_names)
        op.rename_table(table_name, legacy_name)
        table_names.remove(table_name)
        table_names.add(legacy_name)


def _available_legacy_table_name(table_name: str, table_names: set[str]) -> str:
    base_name = f"{table_name}_legacy_pre_0003"
    if base_name not in table_names:
        return base_name
    suffix = 2
    while f"{base_name}_{suffix}" in table_names:
        suffix += 1
    return f"{base_name}_{suffix}"


def _create_rag_indexes(bind, is_postgresql: bool) -> None:
    _create_index_if_missing(bind, "ix_rag_documents_owner_id", "rag_documents", ["owner_id"])
    _create_index_if_missing(bind, "ix_rag_documents_source_id", "rag_documents", ["source_id"])
    _create_index_if_missing(bind, "ix_rag_documents_source_type", "rag_documents", ["source_type"])
    _create_index_if_missing(bind, "ix_rag_chunks_asset_id", "rag_chunks", ["asset_id"])
    _create_index_if_missing(bind, "ix_rag_chunks_document_id", "rag_chunks", ["document_id"])
    _create_index_if_missing(bind, "ix_rag_chunks_owner_id", "rag_chunks", ["owner_id"])
    _create_index_if_missing(bind, "ix_rag_chunks_source_id", "rag_chunks", ["source_id"])
    _create_index_if_missing(bind, "ix_rag_chunks_source_type", "rag_chunks", ["source_type"])
    _create_index_if_missing(
        bind,
        "ix_rag_chunks_owner_source",
        "rag_chunks",
        ["owner_id", "source_type", "source_id"],
    )
    if is_postgresql:
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_rag_chunks_embedding_hnsw "
            "ON rag_chunks USING hnsw (embedding vector_cosine_ops)"
        )


def _create_index_if_missing(bind, index_name: str, table_name: str, columns: list[str]) -> None:
    index_names = {index["name"] for index in sa.inspect(bind).get_indexes(table_name)}
    if index_name in index_names:
        return
    op.create_index(index_name, table_name, columns, unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_rag_chunks_embedding_hnsw")
    op.drop_index("ix_rag_chunks_owner_source", table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_source_type"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_source_id"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_owner_id"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_document_id"), table_name="rag_chunks")
    op.drop_index(op.f("ix_rag_chunks_asset_id"), table_name="rag_chunks")
    op.drop_table("rag_chunks")
    op.drop_index(op.f("ix_rag_documents_source_type"), table_name="rag_documents")
    op.drop_index(op.f("ix_rag_documents_source_id"), table_name="rag_documents")
    op.drop_index(op.f("ix_rag_documents_owner_id"), table_name="rag_documents")
    op.drop_table("rag_documents")
