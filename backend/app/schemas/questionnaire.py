from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from app.models.questionnaire import ResponseType


class QuestionnaireSubmit(BaseModel):
    min_safety_buffer: float = Field(..., ge=0)
    partial_payments_allowed: bool = True
    payment_delay_tolerance: int = Field(0, ge=0, le=90)
    non_negotiable_obligations: Optional[List[str]] = None   # list of obligation IDs


class QuestionnaireOut(BaseModel):
    id: str
    user_id: str
    response_type: ResponseType
    min_safety_buffer: float
    partial_payments_allowed: bool
    payment_delay_tolerance: int
    non_negotiable_obligations: Optional[List[Any]]
    submitted_at: datetime

    model_config = {"from_attributes": True}


class QuestionnaireDueResponse(BaseModel):
    due: bool
    reason: Optional[str] = None   # "onboarding" | "weekly_refresh"
