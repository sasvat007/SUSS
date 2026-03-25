from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.scenario import ChatbotMessage, ChatbotResponse
from app.services import scenario_service

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.post("/message", response_model=ChatbotResponse)
async def message(
    payload: ChatbotMessage,
    current_user: User = Depends(get_current_user),
):
    reply = await scenario_service.chatbot_reply(payload.message, current_user)
    return ChatbotResponse(reply=reply)
