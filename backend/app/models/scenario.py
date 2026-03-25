import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, JSON, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ScenarioHistory(Base):
    __tablename__ = "scenario_histories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    scenario_input: Mapped[dict] = mapped_column(JSON, nullable=False)
    ml_response: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="scenario_histories")

    __table_args__ = (
        Index("ix_scenario_user_id", "user_id"),
    )
