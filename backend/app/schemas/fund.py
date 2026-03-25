from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class FundCreate(BaseModel):
    source_name: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    date_received: date
    notes: Optional[str] = Field(None, max_length=512)

    model_config = {"str_strip_whitespace": True}


class FundOut(BaseModel):
    id: str
    user_id: str
    source_name: str
    amount: float
    date_received: date
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
