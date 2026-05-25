"""Shared SQLAlchemy repository helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.session import get_session_factory


class SqlAlchemyRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
        *,
        session: Session | None = None,
    ) -> None:
        self._external_session = session
        self._session_factory = session_factory or get_session_factory()

    @contextmanager
    def session_scope(self, *, commit: bool = False) -> Iterator[Session]:
        if self._external_session is not None:
            yield self._external_session
            return

        with self._session_factory() as session:
            yield session
            if commit:
                session.commit()
