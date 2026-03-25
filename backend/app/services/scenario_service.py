"""
Scenario & Chatbot Services
"""

import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.user import User
from app.models.scenario import ScenarioHistory
from app.schemas.scenario import ScenarioOut
from app.integrations.ml_client import call_ml_simulate, MLClientError

logger = logging.getLogger(__name__)


async def simulate(scenario: dict, user: User, db: AsyncSession) -> dict:
    """Proxy scenario to ML backend and persist history."""
    try:
        ml_response = await call_ml_simulate(scenario)
    except MLClientError as exc:
        raise HTTPException(status_code=502, detail=f"ML backend error: {exc}") from exc

    history = ScenarioHistory(
        id=str(uuid.uuid4()),
        user_id=user.id,
        scenario_input=scenario,
        ml_response=ml_response,
    )
    db.add(history)
    await db.flush()
    return ml_response


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
    """
    Simple financial assistant using OpenAI. Falls back gracefully if no key.
    """
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
