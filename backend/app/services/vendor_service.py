import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.vendor import Vendor
from app.models.user import User
from app.schemas.vendor import VendorCreate, VendorOut, VendorUpdate
from app.utils.security import hash_field


async def create(payload: VendorCreate, user: User, db: AsyncSession) -> VendorOut:
    vendor = Vendor(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name=payload.name,
        contact_info_hash=hash_field(payload.contact_info) if payload.contact_info else None,
        relationship_type=payload.relationship_type,
    )
    db.add(vendor)
    await db.flush()
    return VendorOut.model_validate(vendor)


async def list_all(user: User, db: AsyncSession) -> List[VendorOut]:
    result = await db.execute(select(Vendor).where(Vendor.user_id == user.id))
    return [VendorOut.model_validate(v) for v in result.scalars().all()]


async def update(
    vendor_id: str, payload: VendorUpdate, user: User, db: AsyncSession
) -> VendorOut:
    vendor = await _fetch_or_404(vendor_id, user.id, db)
    if payload.name is not None:
        vendor.name = payload.name
    if payload.relationship_type is not None:
        vendor.relationship_type = payload.relationship_type
    if payload.confidence_score is not None:
        vendor.confidence_score = payload.confidence_score
    await db.flush()
    return VendorOut.model_validate(vendor)


async def _fetch_or_404(vendor_id: str, user_id: str, db: AsyncSession) -> Vendor:
    result = await db.execute(
        select(Vendor).where(and_(Vendor.id == vendor_id, Vendor.user_id == user_id))
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return v
