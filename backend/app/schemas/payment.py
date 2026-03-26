from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaymentCreate(BaseModel):
    obligation_id: str
    amount: float

class PaymentOut(BaseModel):
    payment_id: str
    obligation_id: str
    amount: float
    status: str
    payment_link: Optional[str] = None
    created_at: Optional[datetime] = None

class PaymentMarkPaid(BaseModel):
    payment_id: str
    payment_type: str = "full" # full or partial
    amount: Optional[float] = None # only for partial
