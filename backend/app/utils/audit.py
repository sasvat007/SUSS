from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from typing import Optional
import uuid


async def write_audit_log(
    db: AsyncSession,
    action: str,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=ip_address,
        extra=extra,
    )
    db.add(log)
    # session commit is handled by the dependency
