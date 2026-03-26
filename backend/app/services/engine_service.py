"""
CapitalSense Engine Integration Service
────────────────────────────────────────
Directly invokes the 3 CapitalSense engines (Financial State, Risk Detection,
Deterministic Decision) using the user's live DB data.

Replaces the old external ML HTTP client with native Python calls.
"""

import logging
from datetime import datetime, date
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.config import settings
from app.models.user import User
from app.models.obligation import Obligation, ObligationStatus
from app.models.receivable import Receivable, ReceivableStatus
from app.models.vendor import Vendor
from app.models.fund import Fund
from app.models.questionnaire import QuestionnaireResponse

# ── CapitalSense Engines ──────────────────────────────────────────────────────
from financial_state_engine import (
    compute_financial_state,
    Payable,
    Receivable as FSEReceivable,
    HiddenTransaction,
    BusinessContext,
    Transaction,
)
from risk_detection_engine import detect_risks
from deterministic_decision_engine import make_payment_decisions
from deterministic_decision_engine.models import VendorRelationship, VendorRelationshipType

logger = logging.getLogger(__name__)


# ── Public API ────────────────────────────────────────────────────────────────

async def run_full_analysis(user: User, db: AsyncSession) -> dict:
    """
    End-to-end pipeline:
      1. Load user's financial data from DB
      2. Run Financial State Engine   → health score, runway, pressure
      3. Run Risk Detection Engine    → 3-scenario risk projections
      4. Run Deterministic Decision Engine → 9 payment strategies
      5. Return structured result ready for the dashboard API
    """
    data = await _load_user_data(user, db)
    questionnaire = await _get_questionnaire(user, db)

    # Build engine input models from DB records
    payables = _build_payables(data["obligations"])
    receivables = _build_receivables(data["receivables"])
    business_ctx = _build_business_context(questionnaire)
    today_str = date.today().isoformat()

    # ── Engine 1: Financial State ─────────────────────────────────────────
    try:
        financial_state = compute_financial_state(
            current_balance=data["balance"],
            transactions=[],           # No raw tx history yet
            payables=payables,
            receivables=receivables,
            hidden_transactions=[],    # No recurring yet
            business_context=business_ctx,
            reference_date=today_str,
        )
    except Exception as exc:
        logger.error("Financial State Engine failed: %s", exc, exc_info=True)
        return _fallback_response(data)

    # ── Engine 2: Risk Detection ──────────────────────────────────────────
    try:
        risk_result = detect_risks(
            financial_state=financial_state,
            payables=payables,
            receivables=receivables,
            avg_payment_delay=business_ctx.avg_payment_delay_days,
            min_buffer=business_ctx.min_cash_buffer,
        )
    except Exception as exc:
        logger.warning("Risk Detection Engine failed: %s", exc, exc_info=True)
        risk_result = None

    # ── Engine 3: Decision Engine ─────────────────────────────────────────
    decisions = None
    if risk_result and payables:
        try:
            vendor_rels = _build_vendor_relationships(data["vendors"])
            decisions = make_payment_decisions(
                financial_state=financial_state,
                risk_detection_result=risk_result,
                payables=payables,
                vendor_relationships=vendor_rels,
                reference_date=datetime.now(),
                risk_level="MODERATE",
            )
        except Exception as exc:
            logger.warning("Decision Engine failed: %s", exc, exc_info=True)
    else:
        logger.info("Skipping Decision Engine: risk_result=%s, payables_count=%d", 
                    bool(risk_result), len(payables))

    # ── Build response ────────────────────────────────────────────────────
    return _build_analysis_response(data, financial_state, risk_result, decisions)


# ── Data Loaders ──────────────────────────────────────────────────────────────

async def _load_user_data(user: User, db: AsyncSession) -> dict:
    """Load all financial records from DB for a user."""
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

    # Vendors
    v_result = await db.execute(select(Vendor).where(Vendor.user_id == user.id))
    vendors = v_result.scalars().all()

    # Calculate balance. 
    # Use the DEFAULT_BANK_BALANCE as the starting point for the demo/user.
    initial_balance = float(settings.DEFAULT_BANK_BALANCE)
    balance = initial_balance + total_funds + total_received - total_paid

    return {
        "balance": balance,
        "total_funds": total_funds,
        "funds": funds,
        "obligations": obligations,
        "receivables": receivables,
        "vendors": vendors,
    }


async def _get_questionnaire(user: User, db: AsyncSession) -> QuestionnaireResponse | None:
    result = await db.execute(
        select(QuestionnaireResponse)
        .where(QuestionnaireResponse.user_id == user.id)
        .order_by(desc(QuestionnaireResponse.submitted_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


from app.utils.financial import categorize_description

# ── Model Converters (DB → Engine Input) ──────────────────────────────────────

def _build_payables(obligations: list[Obligation]) -> list[Payable]:
    """Convert DB Obligations to FSE Payable models."""
    payables = []
    today = date.today()
    for o in obligations:
        if o.status == ObligationStatus.paid:
            continue
        remaining = o.amount - o.amount_paid
        if remaining <= 0:
            continue

        due = o.due_date if isinstance(o.due_date, date) else date.fromisoformat(str(o.due_date))

        if due < today:
            status = "overdue"
        elif due == today:
            status = "due"
        else:
            status = "pending"

        v_name = o.vendor.name if o.vendor else ""
        category = categorize_description(o.description or "", v_name)

        payables.append(Payable(
            id=o.id,
            amount=remaining,
            due_date=due.isoformat(),
            description=o.description or "Obligation",
            status=status,
            priority_level="high" if o.priority_rank and o.priority_rank <= 3 else "normal",
            category=category,
        ))
    return payables


def _build_receivables(receivables: list[Receivable]) -> list[FSEReceivable]:
    """Convert DB Receivables to FSE Receivable models."""
    results = []
    for r in receivables:
        if r.status == ReceivableStatus.received:
            continue
        remaining = r.amount - r.amount_received
        if remaining <= 0:
            continue

        due = r.due_date if isinstance(r.due_date, date) else date.fromisoformat(str(r.due_date))

        # Map DB status to confidence
        confidence = 80  # default
        if r.status == ReceivableStatus.overdue:
            confidence = 40
        elif r.status == ReceivableStatus.partially_received:
            confidence = 70

        results.append(FSEReceivable(
            id=r.id,
            amount=remaining,
            expected_date=due.isoformat(),
            description=r.description or f"From {r.client_name}",
            confidence=confidence / 100.0,
            status="pending",
            category=None,
        ))
    return results


def _build_business_context(questionnaire: QuestionnaireResponse | None) -> BusinessContext:
    """Build BusinessContext from questionnaire answers or defaults."""
    if questionnaire:
        return BusinessContext(
            min_cash_buffer=questionnaire.min_safety_buffer or 50000.0,
            allow_partial_payments=questionnaire.partial_payments_allowed if questionnaire.partial_payments_allowed is not None else True,
            avg_payment_delay_days=questionnaire.payment_delay_tolerance or 5,
            time_horizon_days=30,
        )
    return BusinessContext(
        min_cash_buffer=50000.0,
        allow_partial_payments=True,
        avg_payment_delay_days=5,
        time_horizon_days=30,
    )


def _build_vendor_relationships(vendors: list[Vendor]) -> dict[str, VendorRelationship]:
    """Convert DB vendors to DDE VendorRelationship models."""
    rels = {}
    for v in vendors:
        rel_type = VendorRelationshipType.EXISTING
        if v.relationship_type:
            rt = v.relationship_type.upper()
            if rt in ("CORE", "KEY"):
                rel_type = VendorRelationshipType.CORE
            elif rt in ("NEW",):
                rel_type = VendorRelationshipType.NEW

        rels[v.id] = VendorRelationship(
            vendor_id=v.id,
            vendor_name=v.name,
            relationship_type=rel_type,
            years_with_business=2.0,  # Default
            payment_reliability=v.confidence_score * 100 if v.confidence_score <= 1.0 else v.confidence_score,
        )
    return rels


# ── Response Builders ─────────────────────────────────────────────────────────

def _build_analysis_response(data: dict, fs, risk, decisions) -> dict:
    """Build the complete analysis response for the API. Handles inf/nan safety."""
    
    def _safe(v, default=0.0):
        if v is None: return None
        if isinstance(v, (float, int)) and (math.isinf(v) or math.isnan(v)):
            return default
        return round(float(v), 2)

    # Calculate totals for the UI
    total_ob = sum(o.amount - o.amount_paid for o in data["obligations"])
    total_rec = sum(r.amount - r.amount_received for r in data["receivables"])

    response = {
        # Financial State (Engine 1)
        "financial_state": {
            "available_balance": _safe(data["balance"]),
            "available_cash": _safe(fs.available_cash),
            "health_score": _safe(fs.health_score),
            "health_reasoning": fs.health_reasoning,
            "cash_runway_days": _safe(fs.cash_runway_days, 999),
            "obligation_pressure_ratio": _safe(fs.obligation_pressure_ratio),
            "total_payables_due_now": _safe(fs.total_payables_due_now),
            "total_payables_due_soon": _safe(fs.total_payables_due_soon),
            "total_payables": _safe(total_ob),
            "total_receivables": _safe(total_rec),
            "weighted_receivables": _safe(fs.weighted_receivables),
            "buffer_sufficiency_days": _safe(fs.buffer_sufficiency_days, 999),
            "status_flags": fs.status_flags,
        },
        "funds": [{
            "id": f.id,
            "source_name": f.source_name,
            "amount": f.amount,
            "date_received": f.date_received.isoformat() if hasattr(f.date_received, "isoformat") else str(f.date_received),
            "notes": f.notes
        } for f in data.get("funds", [])],
        "obligations": [{
            "id": o.id,
            "description": o.description,
            "amount": o.amount,
            "amount_paid": o.amount_paid,
            "due_date": o.due_date.isoformat() if hasattr(o.due_date, "isoformat") else str(o.due_date),
            "status": o.status
        } for o in data.get("obligations", [])],
        "receivables": [{
            "id": r.id,
            "client_name": r.client_name,
            "amount": r.amount,
            "amount_received": r.amount_received,
            "due_date": r.due_date.isoformat() if hasattr(r.due_date, "isoformat") else str(r.due_date),
            "status": r.status
        } for r in data.get("receivables", [])],
    }

    # Risk Detection (Engine 2)
    if risk:
        response["risk_detection"] = {
            "best_case": _serialize_projection(risk.best_case),
            "base_case": _serialize_projection(risk.base_case),
            "worst_case": _serialize_projection(risk.worst_case),
        }

    # Decision Engine (Engine 3)
    if decisions:
        response["decisions"] = {
            "overall_recommendation": decisions.overall_recommendation,
            "best_case": _serialize_decision_result(decisions.best_case),
            "base_case": _serialize_decision_result(decisions.base_case),
            "worst_case": _serialize_decision_result(decisions.worst_case),
        }

    return response


def _serialize_projection(proj) -> dict:
    """Serialize a RiskProjection to dict."""
    def _date_str(val):
        if val is None:
            return None
        return val.isoformat() if hasattr(val, 'isoformat') else str(val)

    return {
        "scenario_type": proj.scenario_type if isinstance(proj.scenario_type, str) else str(proj.scenario_type),
        "first_shortfall_date": _date_str(proj.first_shortfall_date),
        "days_to_shortfall": proj.days_to_shortfall,
        "minimum_cash_amount": round(proj.minimum_cash_amount, 2) if proj.minimum_cash_amount is not None else None,
        "minimum_cash_date": _date_str(getattr(proj, "minimum_cash_date", None)),
        "risk_severity": proj.risk_severity.value if hasattr(proj, "risk_severity") and hasattr(proj.risk_severity, "value") else str(proj.risk_severity) if proj.risk_severity else None,
        "risk_summary": getattr(proj, "risk_summary", None),
    }


def _serialize_decision_result(dr) -> dict:
    """Serialize a DecisionResult to dict."""
    return {
        "recommended_strategy": dr.recommended_strategy.value if hasattr(dr.recommended_strategy, "value") else str(dr.recommended_strategy),
        "reasoning": dr.reasoning,
        "cash_available": round(dr.cash_available, 2) if dr.cash_available else None,
        "aggressive": _serialize_strategy(dr.aggressive_strategy) if dr.aggressive_strategy else None,
        "balanced": _serialize_strategy(dr.balanced_strategy) if dr.balanced_strategy else None,
        "conservative": _serialize_strategy(dr.conservative_strategy) if dr.conservative_strategy else None,
    }


def _serialize_strategy(strat) -> dict:
    """Serialize a PaymentStrategy to dict."""
    return {
        "strategy_type": strat.strategy_type.value if hasattr(strat.strategy_type, "value") else str(strat.strategy_type),
        "total_payment": round(strat.total_payment, 2),
        "total_penalty_cost": round(strat.total_penalty_cost, 2),
        "estimated_cash_after": round(strat.estimated_cash_after, 2),
        "survival_probability": round(strat.survival_probability, 1),
        "decisions": [
            {
                "obligation_id": d.obligation_id,
                "status": d.status.value if hasattr(d.status, "value") else str(d.status),
                "pay_amount": round(d.pay_amount, 2),
                "delay_days": d.delay_days,
                "potential_penalty": round(d.potential_penalty, 2),
                "rationale": d.rationale,
                "vendor_name": getattr(d, "vendor_name", ""),
            }
            for d in strat.decisions
        ],
    }


def _fallback_response(data: dict) -> dict:
    """Minimal response when engines fail."""
    total_payables = sum(
        o.amount - o.amount_paid for o in data["obligations"]
        if o.status != ObligationStatus.paid
    )
    total_receivables = sum(
        r.amount - r.amount_received for r in data["receivables"]
        if r.status != ReceivableStatus.received
    )
    return {
        "financial_state": {
            "available_balance": round(data["balance"], 2),
            "available_cash": round(data["balance"], 2),
            "health_score": None,
            "health_reasoning": "Engine unavailable",
            "cash_runway_days": None,
            "obligation_pressure_ratio": None,
            "total_payables_due_now": round(total_payables, 2),
            "total_payables_due_soon": 0,
            "weighted_receivables": round(total_receivables, 2),
            "buffer_sufficiency_days": None,
            "status_flags": {},
        },
    }
