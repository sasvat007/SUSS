"""
Dashboard Router — Full financial analysis endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns complete financial analysis powered by 3 CapitalSense engines:
    - Financial State (health score, runway, pressure)
    - Risk Detection (best/base/worst scenario projections)
    - Decision Engine (9 payment strategies with recommendations)
    """
    return await dashboard_service.get_summary(current_user, db)
