"""Interview session model skeletons."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class InterviewSession(OwnedRecordMixin, Base):
    __tablename__ = "interview_sessions"

    binding_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resume_version_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    job_version_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)


class PolishSessionDetail(OwnedRecordMixin, Base):
    __tablename__ = "polish_session_details"

    session_id: Mapped[str] = mapped_column(String(80), unique=True)
    topic_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    subtopic_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)


class PressureSessionDetail(OwnedRecordMixin, Base):
    __tablename__ = "pressure_session_details"

    session_id: Mapped[str] = mapped_column(String(80), unique=True)

