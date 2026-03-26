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


def _strategy_name(strategy) -> str:
    return strategy.strategy_type.value if hasattr(strategy.strategy_type, "value") else str(strategy.strategy_type)


def _serialize_strategy_summary(strategy) -> dict:
    return {
        "name": _strategy_name(strategy),
        "total_payment": strategy.total_payment,
        "penalty_cost": strategy.total_penalty_cost,
        "survival_probability": strategy.survival_probability,
        "cash_after": strategy.estimated_cash_after,
        "decision_count": len(strategy.decisions),
        "decisions": [
            {
                "obligation_id": d.obligation_id,
                "status": d.status.value if hasattr(d.status, "value") else str(d.status),
                "pay_amount": d.pay_amount,
                "delay_days": d.delay_days,
                "potential_penalty": d.potential_penalty,
                "rationale": d.rationale,
                "vendor_name": getattr(d, "vendor_name", ""),
            }
            for d in strategy.decisions
        ],
    }


def _choose_strategy(decisions, risk_level: str):
    normalized = (risk_level or "MODERATE").upper()
    if normalized in {"MODERATE", "BALANCED"}:
        return decisions.base_case.balanced_strategy, "MODERATE"
    if normalized == "CONSERVATIVE":
        return decisions.base_case.conservative_strategy, "CONSERVATIVE"
    return decisions.base_case.aggressive_strategy, "AGGRESSIVE"


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

    selected_strategy, normalized_risk_level = _choose_strategy(decisions, risk_level)
    aggressive_strategy = decisions.base_case.aggressive_strategy
    balanced_strategy = decisions.base_case.balanced_strategy
    conservative_strategy = decisions.base_case.conservative_strategy

    # Calculate Post-Payment Health Score (Projected)
    post_payables = []
    from financial_state_engine.models import Payable
    for p in payables:
        # p is already an FSE.Payable model from _build_payables
        decision = next((d for d in selected_strategy.decisions if d.obligation_id == p.id), None)
        if decision:
            remaining = p.amount - decision.pay_amount
            if remaining > 0:
                post_payables.append(Payable(
                    id=p.id,
                    amount=remaining,
                    due_date=p.due_date, # already a string
                    description=p.description,
                    status=p.status,
                    priority_level=p.priority_level,
                    category=p.category
                ))
        else:
            post_payables.append(p)

    post_fs = compute_financial_state(
        current_balance=selected_strategy.estimated_cash_after,
        transactions=[],
        payables=post_payables,
        receivables=receivables,
        hidden_transactions=[],
        business_context=business_ctx,
        reference_date=today_str,
    )

    aggressive_summary = _serialize_strategy_summary(aggressive_strategy)
    balanced_summary = _serialize_strategy_summary(balanced_strategy)
    conservative_summary = _serialize_strategy_summary(conservative_strategy)
    comparison = {
        "aggressive": aggressive_summary,
        "moderate": balanced_summary,
        "conservative": conservative_summary,
    }
    selected_summary = comparison["moderate"] if normalized_risk_level == "MODERATE" else comparison[normalized_risk_level.lower()]
    comparison_key = "aggressive" if normalized_risk_level == "MODERATE" else "moderate"
    comparison_summary = comparison[comparison_key]

    result = {
        "health_score": financial_state.health_score,
        "projected_health_score": post_fs.health_score,
        "cash_runway_days": financial_state.cash_runway_days,
        "projected_runway_days": post_fs.cash_runway_days,
        "scenario_overrides": {
            "balance": balance,
            "risk_level": normalized_risk_level,
            "min_cash_buffer": min_buffer,
        },
        "selected_appetite": normalized_risk_level,
        "comparison_appetite": comparison_key.upper(),
        "appetite_difference": {
            "payment_delta": round(selected_summary["total_payment"] - comparison_summary["total_payment"], 2),
            "penalty_delta": round(selected_summary["penalty_cost"] - comparison_summary["penalty_cost"], 2),
            "cash_after_delta": round(selected_summary["cash_after"] - comparison_summary["cash_after"], 2),
            "survival_delta": round(selected_summary["survival_probability"] - comparison_summary["survival_probability"], 2),
            "is_identical": (
                round(selected_summary["total_payment"], 2) == round(comparison_summary["total_payment"], 2)
                and round(selected_summary["penalty_cost"], 2) == round(comparison_summary["penalty_cost"], 2)
                and round(selected_summary["cash_after"], 2) == round(comparison_summary["cash_after"], 2)
                and round(selected_summary["survival_probability"], 2) == round(comparison_summary["survival_probability"], 2)
            ),
        },
        "recommendation": _strategy_name(selected_strategy),
        "strategy_name": _strategy_name(selected_strategy),
        "strategy_metrics": {
            "total_payment": selected_strategy.total_payment,
            "penalty_cost": selected_strategy.total_penalty_cost,
            "survival_probability": selected_strategy.survival_probability,
            "cash_after": selected_strategy.estimated_cash_after,
        },
        "selected_strategy": selected_summary,
        "comparison_strategy": comparison_summary,
        "strategy_comparison": comparison,
        "strategy_reasoning": decisions.base_case.reasoning,
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
