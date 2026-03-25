import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationOut


async def list_unread(user: User, db: AsyncSession) -> List[NotificationOut]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    return [NotificationOut.model_validate(n) for n in result.scalars().all()]


async def mark_read(notif_id: str, user: User, db: AsyncSession) -> NotificationOut:
    result = await db.execute(
        select(Notification).where(
            and_(Notification.id == notif_id, Notification.user_id == user.id)
        )
    )
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    n.is_read = True
    await db.flush()
    return NotificationOut.model_validate(n)


async def create_notification(
    user_id: str,
    title: str,
    body: str,
    notif_type: str,
    db: AsyncSession,
) -> None:
    from app.models.notification import NotificationType
    n = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title,
        body=body,
        type=notif_type,
    )
    db.add(n)
