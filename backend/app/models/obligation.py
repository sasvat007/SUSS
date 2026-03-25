import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Date, JSON, Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class ObligationStatus(str, enum.Enum):
    pending = "pending"
    overdue = "overdue"
    partially_paid = "partially_paid"
    paid = "paid"


class Obligation(Base):
    __tablename__ = "obligations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vendor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)

    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    amount_paid: Mapped[float] = mapped_column(Float, default=0.0)
    due_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    invoice_id_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ObligationStatus] = mapped_column(
        Enum(ObligationStatus), default=ObligationStatus.pending, nullable=False
    )

    # ML-populated fields
    priority_rank: Mapped[int | None] = mapped_column(nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_reasoning: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="obligations")
    vendor: Mapped["Vendor | None"] = relationship(back_populates="obligations")

    __table_args__ = (
        Index("ix_obligations_user_id", "user_id"),
        Index("ix_obligations_due_date", "due_date"),
        Index("ix_obligations_status", "status"),
    )
