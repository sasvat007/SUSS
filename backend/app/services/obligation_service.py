"""
Obligation Service
Handles CRUD + mark-paid flow including ML re-prioritization.
"""

import uuid
from datetime import datetime, timezone, date
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.obligation import Obligation, ObligationStatus
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.obligation import ObligationCreate, ObligationOut, MarkPaidRequest, MarkPaidResponse
from app.utils.security import hash_field
from app.utils.audit import write_audit_log
from app.services import ml_helpers


async def create(payload: ObligationCreate, user: User, db: AsyncSession) -> ObligationOut:
    v_id = payload.vendor_id

    # Auto-create or resolve vendor by name if ID is missing but name exists
    if not v_id and payload.vendor_name:
        v_name = payload.vendor_name.strip()
        v_result = await db.execute(
            select(Vendor).where(
                and_(Vendor.user_id == user.id, Vendor.name == v_name)
            )
        )
        existing_v = v_result.scalar_one_or_none()
        if existing_v:
            v_id = existing_v.id
        else:
            new_v = Vendor(
                id=str(uuid.uuid4()),
                user_id=user.id,
                name=v_name,
                relationship_type="supplier"
            )
            db.add(new_v)
            v_id = new_v.id

    ob = Obligation(
        id=str(uuid.uuid4()),
        user_id=user.id,
        vendor_id=v_id,
        description=payload.description,
        amount=payload.amount,
        due_date=payload.due_date,
        invoice_id_hash=hash_field(payload.invoice_id) if payload.invoice_id else None,
    )
    db.add(ob)
    await db.flush()
    await write_audit_log(db, "CREATE_OBLIGATION", user.id, "obligation", ob.id)
    return ObligationOut.model_validate(ob)


async def list_all(user: User, db: AsyncSession) -> List[ObligationOut]:
    result = await db.execute(
        select(Obligation).where(
            and_(Obligation.user_id == user.id, Obligation.deleted_at.is_(None))
        ).order_by(Obligation.due_date)
    )
    return [ObligationOut.model_validate(o) for o in result.scalars().all()]


async def get_by_id(ob_id: str, user: User, db: AsyncSession) -> ObligationOut:
    ob = await _fetch_or_404(ob_id, user.id, db)
    return ObligationOut.model_validate(ob)


async def mark_paid(
    ob_id: str,
    payload: MarkPaidRequest,
    user: User,
    db: AsyncSession,
) -> MarkPaidResponse:
    ob = await _fetch_or_404(ob_id, user.id, db)

    remaining = ob.amount - ob.amount_paid
    if payload.amount > remaining + 0.01:
        raise HTTPException(status_code=400, detail="Payment exceeds remaining amount")

    from app.utils.financial import categorize_description, is_must_pay_in_full
    v_name = ob.vendor.name if ob.vendor else ""
    cat = categorize_description(ob.description or "", v_name)
    if is_must_pay_in_full(cat) and payload.payment_type == "partial":
        raise HTTPException(status_code=400, detail=f"{cat} obligations cannot be partially paid. Full payment required.")

    ob.amount_paid = (ob.amount_paid or 0.0) + payload.amount
    ob.status = (
        ObligationStatus.paid
        if payload.payment_type == "full" or ob.amount_paid >= ob.amount - 0.01
        else ObligationStatus.partially_paid
    )
    await db.flush()
    await write_audit_log(db, "MARK_PAID", user.id, "obligation", ob.id,
                          extra={"amount": payload.amount, "type": payload.payment_type})

    # Rebuild financial state and call ML
    dashboard, ml_resp = await ml_helpers.rebuild_and_prioritize(user, db)
    priorities = [p.model_dump() for p in ml_resp.priorities] if ml_resp else []
    alerts = ml_resp.alerts if ml_resp else []

    return MarkPaidResponse(
        obligation=ObligationOut.model_validate(ob),
        new_balance=dashboard.available_balance,
        priorities=priorities,
        alerts=alerts,
    )


async def defer_obligation(
    ob_id: str,
    days: int,
    user: User,
    db: AsyncSession,
) -> ObligationOut:
    ob = await _fetch_or_404(ob_id, user.id, db)
    
    # Update due date and status
    from datetime import timedelta
    ob.due_date = ob.due_date + timedelta(days=days)
    ob.status = ObligationStatus.deferred
    
    await db.flush()
    await ml_helpers.rebuild_and_prioritize(user, db)
    await write_audit_log(db, "DEFER_OBLIGATION", user.id, "obligation", ob.id, 
                          extra={"days": days, "new_due_date": ob.due_date.isoformat()})
    
    return ObligationOut.model_validate(ob)


async def soft_delete(ob_id: str, user: User, db: AsyncSession) -> None:
    ob = await _fetch_or_404(ob_id, user.id, db)
    ob.deleted_at = datetime.now(timezone.utc)
    await write_audit_log(db, "DELETE_OBLIGATION", user.id, "obligation", ob.id)


async def _fetch_or_404(ob_id: str, user_id: str, db: AsyncSession) -> Obligation:
    result = await db.execute(
        select(Obligation).where(
            and_(Obligation.id == ob_id, Obligation.user_id == user_id,
                 Obligation.deleted_at.is_(None))
        ).options(selectinload(Obligation.vendor))
    )
    ob = result.scalar_one_or_none()
    if not ob:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obligation not found")
    return ob
