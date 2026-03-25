import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Date, Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class ReceivableStatus(str, enum.Enum):
    pending = "pending"
    partially_received = "partially_received"
    received = "received"
    overdue = "overdue"


class Receivable(Base):
    __tablename__ = "receivables"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_contact_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    amount_received: Mapped[float] = mapped_column(Float, default=0.0)
    due_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    status: Mapped[ReceivableStatus] = mapped_column(
        Enum(ReceivableStatus), default=ReceivableStatus.pending, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="receivables")

    __table_args__ = (
        Index("ix_receivables_user_id", "user_id"),
        Index("ix_receivables_due_date", "due_date"),
        Index("ix_receivables_status", "status"),
    )
