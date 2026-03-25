import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, RefreshRequest
from app.utils.security import (
    hash_password,
    verify_password,
    hash_field,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)
from app.utils.audit import write_audit_log
from jose import JWTError


async def signup(payload: SignupRequest, db: AsyncSession, ip: str) -> TokenResponse:
    # Duplicate email check
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        full_name=payload.full_name,
        email=payload.email,
        phone_number_hash=hash_field(payload.phone_number),
        business_name=payload.business_name,
        office_address=payload.office_address,
        gst_number_hash=hash_field(payload.gst_number),
        hashed_password=hash_password(payload.password),
        questionnaire_completed=False,
    )
    db.add(user)
    await db.flush()  # get ID before commit

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    user.refresh_token_hash = hash_token(refresh)

    await write_audit_log(db, "SIGNUP", user_id=user.id, ip_address=ip)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        requires_questionnaire=True,
    )


async def login(payload: LoginRequest, db: AsyncSession, ip: str) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    user.refresh_token_hash = hash_token(refresh)

    from datetime import datetime, timezone, timedelta
    
    last_q = user.last_questionnaire_at
    if last_q and last_q.tzinfo is None:
        last_q = last_q.replace(tzinfo=timezone.utc)

    needs_q = (
        not user.questionnaire_completed
        or last_q is None
        or (datetime.now(timezone.utc) - last_q) > timedelta(days=7)
    )

    await write_audit_log(db, "LOGIN", user_id=user.id, ip_address=ip)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        requires_questionnaire=needs_q,
    )


async def refresh_tokens(payload: RefreshRequest, db: AsyncSession) -> TokenResponse:
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise JWTError()
        user_id = data["sub"]
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.refresh_token_hash != hash_token(payload.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    user.refresh_token_hash = hash_token(refresh)
    return TokenResponse(access_token=access, refresh_token=refresh)


async def logout(refresh_token: str, user: User, db: AsyncSession) -> None:
    if user.refresh_token_hash == hash_token(refresh_token):
        user.refresh_token_hash = None
    await write_audit_log(db, "LOGOUT", user_id=user.id)
