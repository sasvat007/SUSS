"""
Scenario Service — Direct engine integration for what-if simulations.
"""

import uuid
import logging
from datetime import datetime, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException

from app.models.user import User
from app.models.scenario import ScenarioHistory
from app.schemas.scenario import ScenarioOut
from app.services.engine_service import _load_user_data, _get_questionnaire, _build_payables, _build_receivables, _build_business_context, _build_vendor_relationships

from financial_state_engine import compute_financial_state, BusinessContext
from risk_detection_engine import detect_risks
from deterministic_decision_engine import make_payment_decisions

logger = logging.getLogger(__name__)


async def simulate(scenario: dict, user: User, db: AsyncSession) -> dict:
    """
    Run a what-if scenario through all 3 engines.
    Scenario dict can override: balance, risk_level, min_cash_buffer, time_horizon_days
    """
    data = await _load_user_data(user, db)
    questionnaire = await _get_questionnaire(user, db)

    # Apply scenario overrides
    balance = scenario.get("balance", data["balance"])
    risk_level = scenario.get("risk_level", "MODERATE")
    min_buffer = scenario.get("min_cash_buffer", questionnaire.min_safety_buffer if questionnaire else 50000)
    time_horizon = scenario.get("time_horizon_days", 30)

    payables = _build_payables(data["obligations"])
    receivables = _build_receivables(data["receivables"])
    business_ctx = BusinessContext(
        min_cash_buffer=min_buffer,
        allow_partial_payments=True,
        time_horizon_days=time_horizon,
    )
    today_str = date.today().isoformat()

    try:
        financial_state = compute_financial_state(
            current_balance=balance,
            transactions=[],
            payables=payables,
            receivables=receivables,
            hidden_transactions=[],
            business_context=business_ctx,
            reference_date=today_str,
        )

        risk_result = detect_risks(financial_state, payables=payables, receivables=receivables)

        vendor_rels = _build_vendor_relationships(data["vendors"])
        decisions = make_payment_decisions(
            financial_state=financial_state,
            risk_detection_result=risk_result,
            payables=payables,
            vendor_relationships=vendor_rels,
            reference_date=datetime.now(),
            risk_level=risk_level,
        )
    except Exception as exc:
        logger.error("Scenario simulation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {exc}") from exc

    result = {
        "health_score": financial_state.health_score,
        "cash_runway_days": financial_state.cash_runway_days,
        "scenario_overrides": {
            "balance": balance,
            "risk_level": risk_level,
            "min_cash_buffer": min_buffer,
        },
        "recommendation": decisions.base_case.recommended_strategy.value if hasattr(decisions.base_case.recommended_strategy, 'value') else str(decisions.base_case.recommended_strategy) if decisions.base_case else None,
        "overall_recommendation": decisions.overall_recommendation,
    }

    # Persist
    history = ScenarioHistory(
        id=str(uuid.uuid4()),
        user_id=user.id,
        scenario_input=scenario,
        ml_response=result,
    )
    db.add(history)
    await db.flush()

    return result


async def get_history(user: User, db: AsyncSession) -> list[ScenarioOut]:
    result = await db.execute(
        select(ScenarioHistory)
        .where(ScenarioHistory.user_id == user.id)
        .order_by(ScenarioHistory.created_at.desc())
        .limit(20)
    )
    return [ScenarioOut.model_validate(s) for s in result.scalars().all()]


# ── Chatbot ───────────────────────────────────────────────────────────────────

async def chatbot_reply(message: str, user: User) -> str:
    from app.config import settings
    if not settings.OPENAI_API_KEY:
        return "AI assistant is not configured. Please set OPENAI_API_KEY."
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are CapitalSense, a financial assistant for small business owners. "
                        "Help them understand their cash flow, obligations, and receivables. "
                        "Keep responses concise and actionable."
                    ),
                },
                {"role": "user", "content": message},
            ],
            max_tokens=512,
        )
        return completion.choices[0].message.content or "No response."
    except Exception as exc:
        logger.error("OpenAI error: %s", exc)
        return "Assistant temporarily unavailable."
