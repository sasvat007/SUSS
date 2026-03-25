from pydantic import BaseModel
from typing import Any, Dict, List
from datetime import datetime


class ScenarioSimulateRequest(BaseModel):
    scenario: Dict[str, Any]   # free-form scenario payload forwarded to ML backend as-is


class ScenarioOut(BaseModel):
    id: str
    user_id: str
    scenario_input: Dict[str, Any]
    ml_response: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatbotMessage(BaseModel):
    message: str


class ChatbotResponse(BaseModel):
    reply: str


class EmailDraftRequest(BaseModel):
    obligation_id: str
    reason: str
    proposed_date: str    # ISO date


class EmailDraftResponse(BaseModel):
    subject: str
    body: str
