from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base

class BankLink(Base):
    __tablename__ = "bank_links"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Setu / AA Fields
    consent_id = Column(String, nullable=True)
    status = Column(String, default="PENDING")  # PENDING, ACTIVE, EXPIRED, REVOKED
    account_id = Column(String, nullable=True)  # Setu's internal account reference
    
    bank_name = Column(String, nullable=True)
    account_number_mask = Column(String, nullable=True)
    last_balance = Column(Float, nullable=True)
    last_fetched_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="bank_link")
