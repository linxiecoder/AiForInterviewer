"""Training model skeleton."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class TrainingRecommendation(OwnedRecordMixin, Base):
    __tablename__ = "training_recommendations"

    normalized_topic: Mapped[str] = mapped_column(String(200), nullable=False)
    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    confirmation_id: Mapped[str | None] = mapped_column(String(80), nullable=True)

