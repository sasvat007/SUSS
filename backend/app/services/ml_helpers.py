"""
Shared ML helper — now uses direct CapitalSense engine integration.
Used by obligation service (mark-paid) and dashboard service.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import date

from app.models.user import User
from app.models.obligation import Obligation, ObligationStatus
from app.models.receivable import Receivable, ReceivableStatus
from app.models.vendor import Vendor
from app.models.fund import Fund
from app.models.questionnaire import QuestionnaireResponse
from app.schemas.dashboard import DashboardSummary
from app.schemas.obligation import ObligationOut
from app.schemas.receivable import ReceivableOut
from app.utils.helpers import today_utc, safe_div

from app.services.engine_service import (
    _load_user_data,
    _get_questionnaire,
    _build_payables,
    _build_receivables,
    _build_business_context,
)
from financial_state_engine import compute_financial_state

import logging

logger = logging.getLogger(__name__)


async def rebuild_and_prioritize(
    user: User, db: AsyncSession
) -> tuple[DashboardSummary, dict | None]:
    """
    1. Compute live financial state from DB using CapitalSense engines
    2. Return (DashboardSummary, engine_result)
    """
    data = await _load_user_data(user, db)
    questionnaire = await _get_questionnaire(user, db)

    payables = _build_payables(data["obligations"])
    receivables = _build_receivables(data["receivables"])
    business_ctx = _build_business_context(questionnaire)
    today_str = date.today().isoformat()

    health_score = None
    try:
        financial_state = compute_financial_state(
            current_balance=data["balance"],
            transactions=[],
            payables=payables,
            receivables=receivables,
            hidden_transactions=[],
            business_context=business_ctx,
            reference_date=today_str,
        )
        health_score = financial_state.health_score
    except Exception as exc:
        logger.warning("Engine failed in rebuild_and_prioritize: %s", exc)

    # Build the dashboard summary
    today = today_utc()
    total_payables = sum(
        o.amount - o.amount_paid for o in data["obligations"]
        if o.status != ObligationStatus.paid
    )
    total_receivables = sum(
        r.amount - r.amount_received for r in data["receivables"]
        if r.status != ReceivableStatus.received
    )
    safety_buffer = questionnaire.min_safety_buffer if questionnaire else 0.0
    daily_burn = safe_div(total_payables, 30)
    days_to_zero = safe_div(data["balance"], daily_burn, 9999) if daily_burn > 0 else None

    upcoming = [o for o in data["obligations"] if o.due_date >= today and o.status != ObligationStatus.paid]
    overdue = [o for o in data["obligations"] if o.due_date < today and o.status != ObligationStatus.paid]

    dashboard = DashboardSummary(
        available_balance=round(data["balance"], 2),
        days_to_zero=round(days_to_zero, 1) if days_to_zero else None,
        financial_health_score=health_score,
        total_payables=round(total_payables, 2),
        total_receivables=round(total_receivables, 2),
        safety_buffer=safety_buffer,
        buffer_breached=data["balance"] < safety_buffer,
        upcoming_obligations=[ObligationOut.model_validate(o) for o in upcoming[:5]],
        overdue_obligations=[ObligationOut.model_validate(o) for o in overdue[:5]],
        pending_receivables=[ReceivableOut.model_validate(r) for r in data["receivables"][:5]],
    )
    return dashboard, None
