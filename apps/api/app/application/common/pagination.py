"""Pagination primitives for application queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PageRequest:
    cursor: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class PageResult:
    next_cursor: str | None
    has_more: bool
    limit: int

