"""Review ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class ReviewRepository(Protocol):
    def get_ref(self, review_id: str) -> ResourceRef | None: ...

