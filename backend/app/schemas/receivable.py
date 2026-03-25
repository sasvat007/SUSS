from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from app.models.receivable import ReceivableStatus


class ReceivableCreate(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=255)
    client_contact: Optional[str] = None   # raw — will be hashed in service
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    due_date: date

    model_config = {"str_strip_whitespace": True}


class ReceivableOut(BaseModel):
    id: str
    user_id: str
    client_name: str
    description: Optional[str]
    amount: float
    amount_received: float
    due_date: date
    status: ReceivableStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MarkReceivedRequest(BaseModel):
    payment_type: str = Field(..., pattern="^(full|partial)$")
    amount: float = Field(..., gt=0)
