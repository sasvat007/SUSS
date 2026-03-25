"""
Shared ML helper — assembles financial state payload and calls ML backend.
Used by obligation service (mark-paid) and dashboard service.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.user import User
from app.models.obligation import Obligation, ObligationStatus
from app.models.receivable import Receivable, ReceivableStatus
from app.models.vendor import Vendor
from app.models.fund import Fund
from app.models.questionnaire import QuestionnaireResponse
from app.schemas.ml import (
    MLPrioritizeRequest,
    MLPrioritizeResponse,
    MLObligationItem,
    MLReceivableItem,
    MLVendorScore,
    MLQuestionnaireContext,
)
from app.schemas.dashboard import DashboardSummary
from app.schemas.obligation import ObligationOut
from app.schemas.receivable import ReceivableOut
from app.integrations.ml_client import call_ml_prioritize, MLClientError
from app.utils.helpers import today_utc, safe_div
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)


async def rebuild_and_prioritize(
    user: User, db: AsyncSession
) -> tuple[DashboardSummary, MLPrioritizeResponse | None]:
    """
    1. Compute live financial state from DB
    2. Call ML backend for prioritization
    3. Write ML results back to obligations
    4. Return (DashboardSummary, MLPrioritizeResponse)
    """
    state = await _build_financial_state(user, db)
    questionnaire = await _get_latest_questionnaire(user, db)
    ml_resp = await _call_ml(user, state, questionnaire)

    # Persist ML rankings
    if ml_resp:
        await _apply_priorities(ml_resp, user, db)

    dashboard = _build_dashboard(state, ml_resp, questionnaire)
    return dashboard, ml_resp


# ─────────────────────────────────────────────────────────────────────────────

async def _build_financial_state(user: User, db: AsyncSession) -> dict:
    # Funds
    f_result = await db.execute(select(Fund).where(Fund.user_id == user.id))
    funds = f_result.scalars().all()
    total_funds = sum(f.amount for f in funds)

    # Obligations
    ob_result = await db.execute(
        select(Obligation).where(
            and_(Obligation.user_id == user.id, Obligation.deleted_at.is_(None))
        )
    )
    obligations = ob_result.scalars().all()
    total_paid = sum(o.amount_paid for o in obligations)

    # Receivables
    rec_result = await db.execute(
        select(Receivable).where(Receivable.user_id == user.id)
    )
    receivables = rec_result.scalars().all()
    total_received = sum(r.amount_received for r in receivables)

    # Vendors (for ML confidence scores)
    v_result = await db.execute(select(Vendor).where(Vendor.user_id == user.id))
    vendors = v_result.scalars().all()

    balance = total_funds + total_received - total_paid
    total_payables = sum(
        o.amount - o.amount_paid
        for o in obligations
        if o.status not in (ObligationStatus.paid,)
    )
    total_receivables = sum(
        r.amount - r.amount_received
        for r in receivables
        if r.status not in (ReceivableStatus.received,)
    )

    today = today_utc()
    upcoming = [o for o in obligations if o.due_date >= today and o.status != ObligationStatus.paid]
    overdue = [o for o in obligations if o.due_date < today and o.status != ObligationStatus.paid]

    return {
        "balance": balance,
        "total_funds": total_funds,
        "total_payables": total_payables,
        "total_receivables": total_receivables,
        "obligations": obligations,
        "receivables": receivables,
        "vendors": vendors,
        "upcoming": upcoming,
        "overdue": overdue,
    }


async def _get_latest_questionnaire(user: User, db: AsyncSession) -> QuestionnaireResponse | None:
    result = await db.execute(
        select(QuestionnaireResponse)
        .where(QuestionnaireResponse.user_id == user.id)
        .order_by(desc(QuestionnaireResponse.submitted_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _call_ml(
    user: User,
    state: dict,
    questionnaire: QuestionnaireResponse | None,
) -> MLPrioritizeResponse | None:
    payables = [
        MLObligationItem(
            obligation_id=o.id,
            vendor_name=None,
            amount=o.amount,
            amount_paid=o.amount_paid,
            due_date=str(o.due_date),
            status=o.status.value,
            relationship_type=None,
            confidence_score=1.0,
        )
        for o in state["obligations"]
        if o.status != ObligationStatus.paid and o.deleted_at is None
    ]
    rcv = [
        MLReceivableItem(
            receivable_id=r.id,
            client_name=r.client_name,
            amount=r.amount,
            amount_received=r.amount_received,
            due_date=str(r.due_date),
            status=r.status.value,
        )
        for r in state["receivables"]
    ]
    vendor_scores = [
        MLVendorScore(
            vendor_id=v.id,
            name=v.name,
            confidence_score=v.confidence_score,
            relationship_type=v.relationship_type,
        )
        for v in state["vendors"]
    ]
    q_ctx = None
    if questionnaire:
        q_ctx = MLQuestionnaireContext(
            min_safety_buffer=questionnaire.min_safety_buffer,
            partial_payments_allowed=questionnaire.partial_payments_allowed,
            payment_delay_tolerance=questionnaire.payment_delay_tolerance,
            non_negotiable_obligations=questionnaire.non_negotiable_obligations or [],
        )

    req = MLPrioritizeRequest(
        user_id=user.id,
        balance=state["balance"],
        payables=payables,
        receivables=rcv,
        questionnaire=q_ctx,
        vendor_scores=vendor_scores,
    )
    try:
        return await call_ml_prioritize(req)
    except MLClientError as exc:
        logger.warning("ML call failed, returning without prioritization: %s", exc)
        return None


async def _apply_priorities(ml_resp: MLPrioritizeResponse, user: User, db: AsyncSession) -> None:
    for p in ml_resp.priorities:
        result = await db.execute(
            select(Obligation).where(
                and_(Obligation.id == p.obligation_id, Obligation.user_id == user.id)
            )
        )
        ob = result.scalar_one_or_none()
        if ob:
            ob.priority_rank = p.priority_rank
            ob.priority_score = p.priority_score
            ob.priority_reasoning = p.reasoning


def _build_dashboard(
    state: dict,
    ml_resp: MLPrioritizeResponse | None,
    questionnaire: QuestionnaireResponse | None,
) -> DashboardSummary:
    balance = state["balance"]
    safety_buffer = questionnaire.min_safety_buffer if questionnaire else 0.0
    daily_burn = safe_div(state["total_payables"], 30)
    days_to_zero = safe_div(balance, daily_burn, 9999) if daily_burn > 0 else None
    health_score = ml_resp.financial_health_score if ml_resp else None

    return DashboardSummary(
        available_balance=round(balance, 2),
        days_to_zero=round(days_to_zero, 1) if days_to_zero else None,
        financial_health_score=health_score,
        total_payables=round(state["total_payables"], 2),
        total_receivables=round(state["total_receivables"], 2),
        safety_buffer=safety_buffer,
        buffer_breached=balance < safety_buffer,
        upcoming_obligations=[ObligationOut.model_validate(o) for o in state["upcoming"][:5]],
        overdue_obligations=[ObligationOut.model_validate(o) for o in state["overdue"][:5]],
        pending_receivables=[ReceivableOut.model_validate(r) for r in state["receivables"][:5]],
    )
