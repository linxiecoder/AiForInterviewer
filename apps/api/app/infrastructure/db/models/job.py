"""Job model skeletons."""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Job(OwnedRecordMixin, Base):
    __tablename__ = "jobs"

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    current_version_id: Mapped[str | None] = mapped_column(String(80), nullable=True)


class JobVersion(OwnedRecordMixin, Base):
    __tablename__ = "job_versions"

    job_id: Mapped[str] = mapped_column(String(80), index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    jd_text: Mapped[str] = mapped_column(Text, nullable=False)

