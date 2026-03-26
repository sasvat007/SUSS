import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.fund import Fund
from app.models.user import User
from app.schemas.fund import FundCreate, FundOut


async def create(payload: FundCreate, user: User, db: AsyncSession) -> FundOut:
    fund = Fund(
        id=str(uuid.uuid4()),
        user_id=user.id,
        source_name=payload.source_name,
        amount=payload.amount,
        date_received=payload.date_received,
        notes=payload.notes,
    )
    db.add(fund)
    await db.flush()
    
    from app.utils.audit import write_audit_log
    await write_audit_log(db, "CREATE_FUND", user.id, "fund", fund.id, extra={"amount": fund.amount})
    
    return FundOut.model_validate(fund)


async def list_all(user: User, db: AsyncSession) -> List[FundOut]:
    result = await db.execute(
        select(Fund).where(Fund.user_id == user.id).order_by(Fund.date_received.desc())
    )
    return [FundOut.model_validate(f) for f in result.scalars().all()]


async def delete(fund_id: str, user: User, db: AsyncSession) -> None:
    result = await db.execute(
        select(Fund).where(and_(Fund.id == fund_id, Fund.user_id == user.id))
    )
    fund = result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fund not found")
    await db.delete(fund)
