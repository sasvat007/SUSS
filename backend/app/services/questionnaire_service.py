from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from app.models.user import User
from app.models.questionnaire import QuestionnaireResponse, ResponseType
from app.schemas.questionnaire import QuestionnaireSubmit, QuestionnaireOut, QuestionnaireDueResponse
import uuid


_WEEKLY_INTERVAL = timedelta(days=7)


async def check_due(user: User) -> QuestionnaireDueResponse:
    if not user.questionnaire_completed:
        return QuestionnaireDueResponse(due=True, reason="onboarding")
    if user.last_questionnaire_at is None:
        return QuestionnaireDueResponse(due=True, reason="onboarding")
    age = datetime.now(timezone.utc) - user.last_questionnaire_at
    if age >= _WEEKLY_INTERVAL:
        return QuestionnaireDueResponse(due=True, reason="weekly_refresh")
    return QuestionnaireDueResponse(due=False)


async def submit(
    payload: QuestionnaireSubmit, user: User, db: AsyncSession
) -> QuestionnaireOut:
    response_type = (
        ResponseType.onboarding if not user.questionnaire_completed else ResponseType.weekly
    )
    qr = QuestionnaireResponse(
        id=str(uuid.uuid4()),
        user_id=user.id,
        response_type=response_type,
        min_safety_buffer=payload.min_safety_buffer,
        partial_payments_allowed=payload.partial_payments_allowed,
        payment_delay_tolerance=payload.payment_delay_tolerance,
        non_negotiable_obligations=payload.non_negotiable_obligations,
    )
    db.add(qr)

    user.questionnaire_completed = True
    user.last_questionnaire_at = datetime.now(timezone.utc)
    await db.flush()
    return QuestionnaireOut.model_validate(qr)


async def get_latest(user: User, db: AsyncSession) -> QuestionnaireOut:
    result = await db.execute(
        select(QuestionnaireResponse)
        .where(QuestionnaireResponse.user_id == user.id)
        .order_by(desc(QuestionnaireResponse.submitted_at))
        .limit(1)
    )
    qr = result.scalar_one_or_none()
    if not qr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No questionnaire found")
    return QuestionnaireOut.model_validate(qr)
