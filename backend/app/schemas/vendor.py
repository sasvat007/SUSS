from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VendorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    contact_info: Optional[str] = None    # raw — hashed in service
    relationship_type: Optional[str] = None

    model_config = {"str_strip_whitespace": True}


class VendorUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    relationship_type: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class VendorOut(BaseModel):
    id: str
    user_id: str
    name: str
    relationship_type: Optional[str]
    confidence_score: float
    created_at: datetime

    model_config = {"from_attributes": True}
