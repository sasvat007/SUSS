import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, JSON, Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class ResponseType(str, enum.Enum):
    onboarding = "onboarding"
    weekly = "weekly"


class QuestionnaireResponse(Base):
    __tablename__ = "questionnaire_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    response_type: Mapped[ResponseType] = mapped_column(Enum(ResponseType), nullable=False)
    min_safety_buffer: Mapped[float] = mapped_column(Float, nullable=False)
    partial_payments_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    payment_delay_tolerance: Mapped[int] = mapped_column(default=0)       # days
    non_negotiable_obligations: Mapped[list | None] = mapped_column(JSON, nullable=True)  # list of obligation IDs / tags

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="questionnaire_responses")

    __table_args__ = (
        Index("ix_questionnaire_user_id", "user_id"),
    )
