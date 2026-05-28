"""Database custom types."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator, UserDefinedType


class _PgVectorType(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int | None = None) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_kw) -> str:
        return f"vector({self.dimensions})" if self.dimensions is not None else "vector"


class PgVector(TypeDecorator):
    """Store pgvector values while keeping SQLite tests on TEXT."""

    impl = Text
    cache_ok = True

    def __init__(self, dimensions: int | None = None) -> None:
        self.dimensions = dimensions
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_PgVectorType(self.dimensions))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, Sequence):
            return "[" + ",".join(str(float(item)) for item in value) + "]"
        raise TypeError("pgvector value must be a sequence of floats")

    def process_result_value(self, value, dialect):
        return value
