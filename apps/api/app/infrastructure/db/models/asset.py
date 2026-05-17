"""Asset model skeletons."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Asset(OwnedRecordMixin, Base):
    __tablename__ = "assets"

    normalized_title: Mapped[str] = mapped_column(String(200), nullable=False)
    current_version_id: Mapped[str | None] = mapped_column(String(80), nullable=True)


class AssetVersion(OwnedRecordMixin, Base):
    __tablename__ = "asset_versions"

    asset_id: Mapped[str] = mapped_column(String(80), index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_from_candidate_id: Mapped[str | None] = mapped_column(String(80), nullable=True)

