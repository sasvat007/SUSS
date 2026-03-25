from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.fund import FundCreate, FundOut
from app.services import fund_service

router = APIRouter(prefix="/funds", tags=["Funds"])


@router.post("", response_model=FundOut, status_code=status.HTTP_201_CREATED)
async def create(
    payload: FundCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await fund_service.create(payload, current_user, db)


@router.get("", response_model=List[FundOut])
async def list_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await fund_service.list_all(current_user, db)


@router.delete("/{fund_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    fund_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await fund_service.delete(fund_id, current_user, db)
