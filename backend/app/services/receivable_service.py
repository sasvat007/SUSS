import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.receivable import Receivable, ReceivableStatus
from app.models.user import User
from app.schemas.receivable import ReceivableCreate, ReceivableOut, MarkReceivedRequest
from app.utils.security import hash_field
from app.utils.audit import write_audit_log


async def create(payload: ReceivableCreate, user: User, db: AsyncSession) -> ReceivableOut:
    rec = Receivable(
        id=str(uuid.uuid4()),
        user_id=user.id,
        client_name=payload.client_name,
        client_contact_hash=hash_field(payload.client_contact) if payload.client_contact else None,
        description=payload.description,
        amount=payload.amount,
        due_date=payload.due_date,
    )
    db.add(rec)
    await db.flush()
    return ReceivableOut.model_validate(rec)


async def list_all(user: User, db: AsyncSession) -> List[ReceivableOut]:
    result = await db.execute(
        select(Receivable).where(Receivable.user_id == user.id).order_by(Receivable.due_date)
    )
    return [ReceivableOut.model_validate(r) for r in result.scalars().all()]


async def mark_received(
    rec_id: str, payload: MarkReceivedRequest, user: User, db: AsyncSession
) -> ReceivableOut:
    rec = await _fetch_or_404(rec_id, user.id, db)
    remaining = rec.amount - rec.amount_received

    if payload.amount > remaining + 0.01:
        raise HTTPException(status_code=400, detail="Amount exceeds remaining receivable")

    rec.amount_received += payload.amount
    rec.status = (
        ReceivableStatus.received
        if payload.payment_type == "full" or rec.amount_received >= rec.amount - 0.01
        else ReceivableStatus.partially_received
    )
    await db.flush()
    await write_audit_log(db, "MARK_RECEIVED", user.id, "receivable", rec.id,
                          extra={"amount": payload.amount})
    return ReceivableOut.model_validate(rec)


async def _fetch_or_404(rec_id: str, user_id: str, db: AsyncSession) -> Receivable:
    result = await db.execute(
        select(Receivable).where(
            and_(Receivable.id == rec_id, Receivable.user_id == user_id)
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receivable not found")
    return rec
