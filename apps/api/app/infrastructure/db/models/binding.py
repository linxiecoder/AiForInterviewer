"""Resume-job binding model skeleton."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class ResumeJobBinding(OwnedRecordMixin, Base):
    __tablename__ = "resume_job_bindings"

    resume_id: Mapped[str] = mapped_column(String(80), index=True)
    job_id: Mapped[str] = mapped_column(String(80), index=True)
    resume_version_id: Mapped[str] = mapped_column(String(80), nullable=False)
    job_version_id: Mapped[str] = mapped_column(String(80), nullable=False)
    unbound_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

