from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.obligation import ObligationCreate, ObligationOut, MarkPaidRequest, MarkPaidResponse
from app.services import obligation_service

router = APIRouter(prefix="/obligations", tags=["Obligations"])


@router.post("", response_model=ObligationOut, status_code=status.HTTP_201_CREATED)
async def create(
    payload: ObligationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await obligation_service.create(payload, current_user, db)


@router.get("", response_model=List[ObligationOut])
async def list_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await obligation_service.list_all(current_user, db)


@router.get("/{ob_id}", response_model=ObligationOut)
async def get_one(
    ob_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await obligation_service.get_by_id(ob_id, current_user, db)


@router.patch("/{ob_id}/mark-paid", response_model=MarkPaidResponse)
async def mark_paid(
    ob_id: str,
    payload: MarkPaidRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await obligation_service.mark_paid(ob_id, payload, current_user, db)


@router.delete("/{ob_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    ob_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await obligation_service.soft_delete(ob_id, current_user, db)


@router.patch("/{ob_id}/defer", response_model=ObligationOut)
async def defer_obligation(
    ob_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await obligation_service.defer_obligation(ob_id, days, current_user, db)
