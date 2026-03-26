from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.obligation import Obligation, ObligationStatus
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentMarkPaid
from app.database import get_db
from app.dependencies import get_current_user
from app.integrations import setu_client
from app.services import ml_helpers

router = APIRouter(prefix="/payments", tags=["Payments"])

async def _process_payment_success(payment: Payment, db: AsyncSession):
    """Internal helper to mark a payment successful and update obligation."""
    if payment.status == "success":
        return # already processed
        
    payment.status = "success"
    
    ob_res = await db.execute(select(Obligation).where(Obligation.id == payment.obligation_id))
    obligation = ob_res.scalars().first()
    if obligation:
        obligation.amount_paid = (obligation.amount_paid or 0.0) + payment.amount
        if obligation.amount_paid >= obligation.amount - 0.01:
            obligation.status = ObligationStatus.paid
        else:
            obligation.status = ObligationStatus.partially_paid
        db.add(obligation)
        
    db.add(payment)
    await db.flush()
    
    # Reload user and re-prioritize
    user_res = await db.execute(select(User).where(User.id == payment.user_id))
    user = user_res.scalars().first()
    if user:
        await ml_helpers.rebuild_and_prioritize(user, db)

@router.get("", response_model=list[dict])
async def get_payments(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Payment).where(Payment.user_id == current_user.id))
    payments = result.scalars().all()
    return [
        {
            "id": p.id,
            "obligation_id": p.obligation_id,
            "amount": p.amount,
            "status": p.status,
            "payment_link_url": p.payment_link_url,
            "created_at": p.created_at
        }
        for p in payments
    ]

@router.post("/create", response_model=PaymentOut)
async def create_payment(payment_in: PaymentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Fetch obligation
    result = await db.execute(select(Obligation).where(Obligation.id == payment_in.obligation_id, Obligation.user_id == current_user.id))
    obligation = result.scalars().first()
    
    if not obligation:
        raise HTTPException(status_code=404, detail="Obligation not found")
        
    remaining = obligation.amount - (obligation.amount_paid or 0.0)
    if payment_in.amount > remaining + 0.01: # allow tiny floating point diff
        raise HTTPException(status_code=400, detail="Payment amount exceeds remaining balance")
        
    # 2. Create local payment record
    payment = Payment(
        user_id=current_user.id,
        obligation_id=obligation.id,
        amount=payment_in.amount,
        status="pending"
    )
    db.add(payment)
    await db.flush() # get id
    
    # 3. Generate Setu Link
    try:
        link_id, link_url = await setu_client.create_setu_payment_link(
            amount=payment.amount,
            bill_ref=str(payment.id),
            customer_name=current_user.full_name
        )
        payment.payment_link_url = link_url
        payment.setu_payment_link_id = link_id
        await db.flush()
    except Exception as e:
        payment.status = "failed"
        await db.flush()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Setu error: {str(e)}")
    
    return {
        "payment_id": payment.id,
        "obligation_id": obligation.id,
        "amount": payment.amount,
        "status": payment.status,
        "payment_link": payment.payment_link_url,
        "created_at": payment.created_at
    }

@router.get("/{payment_id}/verify")
async def verify_payment(payment_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch status from Setu and update locally if success."""
    res = await db.execute(select(Payment).where(Payment.id == payment_id, Payment.user_id == current_user.id))
    payment = res.scalars().first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    if not payment.setu_payment_link_id:
        return {"status": payment.status, "message": "No Setu link ID for this payment."}
        
    status_data = await setu_client.get_payment_link_status(payment.setu_payment_link_id)
    s_status = status_data.get("status") # paid, active, expired, cancelled
    
    if s_status == "paid":
        await _process_payment_success(payment, db)
        return {"status": "success", "message": "Payment verified and processed"}
    
    return {"status": payment.status, "setu_status": s_status}

@router.post("/webhook")
async def setu_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Setu V2 Webhook to auto-mark payments as paid."""
    # Note: In production, verify HMAC signature here using SETU_CLIENT_SECRET
    body = await request.json()
    
    bill_ref = body.get("billReferenceNumber")
    status = body.get("status") # paid
    
    if not bill_ref or status != "paid":
        return {"status": "ignored"}
        
    res = await db.execute(select(Payment).where(Payment.id == bill_ref))
    payment = res.scalars().first()
    if payment:
        await _process_payment_success(payment, db)
        return {"status": "processed"}
        
    return {"status": "payment_not_found"}

@router.post("/mark-paid")
async def mark_paid(payment_in: PaymentMarkPaid, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Manual override to mark a known payment success
    res = await db.execute(select(Payment).where(Payment.id == payment_in.payment_id, Payment.user_id == current_user.id))
    payment = res.scalars().first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    await _process_payment_success(payment, db)
    return {"message": "Payment manually marked successful"}
