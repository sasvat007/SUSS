import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone_number_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    office_address: Mapped[str] = mapped_column(String(512), nullable=True)
    gst_number_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Questionnaire state
    questionnaire_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    last_questionnaire_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Refresh token (stored hashed for logout invalidation)
    refresh_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    obligations: Mapped[list["Obligation"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    receivables: Mapped[list["Receivable"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    vendors: Mapped[list["Vendor"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    funds: Mapped[list["Fund"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    questionnaire_responses: Mapped[list["QuestionnaireResponse"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    scenario_histories: Mapped[list["ScenarioHistory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_users_email", "email"),
    )
