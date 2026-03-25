from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.vendor import VendorCreate, VendorOut, VendorUpdate
from app.services import vendor_service

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.post("", response_model=VendorOut, status_code=status.HTTP_201_CREATED)
async def create(
    payload: VendorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await vendor_service.create(payload, current_user, db)


@router.get("", response_model=List[VendorOut])
async def list_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await vendor_service.list_all(current_user, db)


@router.patch("/{vendor_id}", response_model=VendorOut)
async def update(
    vendor_id: str,
    payload: VendorUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await vendor_service.update(vendor_id, payload, current_user, db)
