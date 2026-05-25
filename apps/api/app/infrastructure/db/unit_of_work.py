"""SQLAlchemy Unit of Work foundation."""

from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.infrastructure.db.session import get_session_factory


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()
        self.session: Session | None = None
        self.jobs: SqlAlchemyJobRepository | None = None
        self.resumes: SqlAlchemyResumeRepository | None = None
        self.bindings: SqlAlchemyBindingRepository | None = None
        self._committed = False
        self._closed = False

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.jobs = SqlAlchemyJobRepository(session=self.session)
        self.resumes = SqlAlchemyResumeRepository(session=self.session)
        self.bindings = SqlAlchemyBindingRepository(session=self.session)
        self._committed = False
        self._closed = False
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.session is None or self._closed:
            return
        try:
            if exc_type is not None or not self._committed:
                self.rollback()
        finally:
            self.session.close()
            self._closed = True

    def commit(self) -> None:
        if self.session is None or self._closed:
            return
        self.session.commit()
        self._committed = True

    def rollback(self) -> None:
        if self.session is None or self._closed:
            return
        self.session.rollback()
        self._committed = False
