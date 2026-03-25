from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from app.models.obligation import ObligationStatus


class ObligationCreate(BaseModel):
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = None
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    due_date: date
    invoice_id: Optional[str] = None   # raw — will be hashed in service

    model_config = {"str_strip_whitespace": True}


class ObligationOut(BaseModel):
    id: str
    user_id: str
    vendor_id: Optional[str]
    description: Optional[str]
    amount: float
    amount_paid: float
    due_date: date
    status: ObligationStatus
    priority_rank: Optional[int]
    priority_score: Optional[float]
    priority_reasoning: Optional[dict]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MarkPaidRequest(BaseModel):
    payment_type: str = Field(..., pattern="^(full|partial)$")
    amount: float = Field(..., gt=0)


class MarkPaidResponse(BaseModel):
    obligation: ObligationOut
    new_balance: float
    priorities: list[dict]
    alerts: list[dict]
