"""Resume model skeletons."""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Resume(OwnedRecordMixin, Base):
    __tablename__ = "resumes"

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    current_version_id: Mapped[str | None] = mapped_column(String(80), nullable=True)


class ResumeVersion(OwnedRecordMixin, Base):
    __tablename__ = "resume_versions"

    resume_id: Mapped[str] = mapped_column(String(80), index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    markdown_text: Mapped[str] = mapped_column(Text, nullable=False)

