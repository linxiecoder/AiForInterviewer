"""RAG document and chunk models."""

from typing import Any

from sqlalchemy import Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin
from app.infrastructure.db.types import PgVector

ASSET_RAG_EMBEDDING_DIMENSION = 1536


class RagDocument(OwnedRecordMixin, Base):
    __tablename__ = "rag_documents"

    source_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    source_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class RagChunk(OwnedRecordMixin, Base):
    __tablename__ = "rag_chunks"

    document_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    source_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    asset_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    heading_path_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    embedding: Mapped[str] = mapped_column(PgVector(ASSET_RAG_EMBEDDING_DIMENSION), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(160), nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
