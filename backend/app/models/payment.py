import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    obligation_id: Mapped[str] = mapped_column(String(36), ForeignKey("obligations.id", ondelete="CASCADE"), nullable=False)
    
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending") # pending, success, failed
    
    setu_payment_link_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_link_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="payments")
    obligation: Mapped["Obligation"] = relationship()

    __table_args__ = (
        Index("ix_payments_user_id", "user_id"),
        Index("ix_payments_obligation_id", "obligation_id"),
    )
