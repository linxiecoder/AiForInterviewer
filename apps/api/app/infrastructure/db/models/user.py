"""User account model skeleton."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class UserAccount(OwnedRecordMixin, Base):
    __tablename__ = "user_accounts"

    email_normalized: Mapped[str | None] = mapped_column(String(320), nullable=True, unique=True)

