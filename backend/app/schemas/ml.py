from pydantic import BaseModel
from typing import Any, Dict, List, Optional


# ── Outbound to ML backend ────────────────────────────────────────────────────

class MLObligationItem(BaseModel):
    obligation_id: str
    vendor_name: Optional[str]
    amount: float
    amount_paid: float
    due_date: str           # ISO date string
    status: str
    relationship_type: Optional[str]
    confidence_score: float


class MLReceivableItem(BaseModel):
    receivable_id: str
    client_name: str
    amount: float
    amount_received: float
    due_date: str
    status: str


class MLVendorScore(BaseModel):
    vendor_id: str
    name: str
    confidence_score: float
    relationship_type: Optional[str]


class MLQuestionnaireContext(BaseModel):
    min_safety_buffer: float
    partial_payments_allowed: bool
    payment_delay_tolerance: int
    non_negotiable_obligations: Optional[List[str]]


class MLPrioritizeRequest(BaseModel):
    user_id: str
    balance: float
    payables: List[MLObligationItem]
    receivables: List[MLReceivableItem]
    questionnaire: Optional[MLQuestionnaireContext]
    vendor_scores: List[MLVendorScore]


# ── Inbound from ML backend ───────────────────────────────────────────────────

class PriorityItem(BaseModel):
    obligation_id: str
    priority_rank: int
    priority_score: float
    reasoning: Dict[str, Any]


class MLPrioritizeResponse(BaseModel):
    priorities: List[PriorityItem]
    alerts: List[Dict[str, Any]]
    risk: Dict[str, Any]
    financial_health_score: Optional[float] = None
