from pydantic import BaseModel
from typing import Optional, List
from app.schemas.obligation import ObligationOut
from app.schemas.receivable import ReceivableOut


class DashboardSummary(BaseModel):
    available_balance: float
    days_to_zero: Optional[float]     # estimated days until balance hits zero
    financial_health_score: Optional[float]  # 0-100 from ML (cached)
    total_payables: float
    total_receivables: float
    safety_buffer: float
    buffer_breached: bool
    upcoming_obligations: List[ObligationOut]
    overdue_obligations: List[ObligationOut]
    pending_receivables: List[ReceivableOut]
