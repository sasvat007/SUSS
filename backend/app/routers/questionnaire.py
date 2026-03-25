from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.questionnaire import QuestionnaireSubmit, QuestionnaireOut, QuestionnaireDueResponse
from app.services import questionnaire_service

router = APIRouter(prefix="/questionnaire", tags=["Questionnaire"])


@router.get("/due", response_model=QuestionnaireDueResponse)
async def check_due(current_user: User = Depends(get_current_user)):
    return await questionnaire_service.check_due(current_user)


@router.post("/submit", response_model=QuestionnaireOut)
async def submit(
    payload: QuestionnaireSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await questionnaire_service.submit(payload, current_user, db)


@router.get("/latest", response_model=QuestionnaireOut)
async def latest(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await questionnaire_service.get_latest(current_user, db)
