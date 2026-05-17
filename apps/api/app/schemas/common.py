"""Common API DTOs."""

from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    next_cursor: str | None = None
    has_more: bool
    limit: int = Field(ge=1, le=100)
    total_count_available: bool = False

