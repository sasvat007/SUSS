from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.receivable import ReceivableCreate, ReceivableOut, MarkReceivedRequest
from app.services import receivable_service

router = APIRouter(prefix="/receivables", tags=["Receivables"])


@router.post("", response_model=ReceivableOut, status_code=status.HTTP_201_CREATED)
async def create(
    payload: ReceivableCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await receivable_service.create(payload, current_user, db)


@router.get("", response_model=List[ReceivableOut])
async def list_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await receivable_service.list_all(current_user, db)


@router.patch("/{rec_id}/mark-received", response_model=ReceivableOut)
async def mark_received(
    rec_id: str,
    payload: MarkReceivedRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await receivable_service.mark_received(rec_id, payload, current_user, db)
