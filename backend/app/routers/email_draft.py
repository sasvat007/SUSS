from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.scenario import EmailDraftRequest, EmailDraftResponse
from app.services import email_service
from pydantic import BaseModel


class ReminderRequest(BaseModel):
    client_name: str
    amount: float
    due_date: str


router = APIRouter(prefix="/email-draft", tags=["Email Draft"])


@router.post("/deferral", response_model=EmailDraftResponse)
async def deferral(
    payload: EmailDraftRequest,
    current_user: User = Depends(get_current_user),
):
    result = await email_service.draft_deferral(
        payload.obligation_id, payload.reason, payload.proposed_date
    )
    return EmailDraftResponse(**result)


@router.post("/reminder", response_model=EmailDraftResponse)
async def reminder(
    payload: ReminderRequest,
    current_user: User = Depends(get_current_user),
):
    result = await email_service.draft_reminder(
        payload.client_name, payload.amount, payload.due_date
    )
    return EmailDraftResponse(**result)
