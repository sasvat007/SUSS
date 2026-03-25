from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services import ml_helpers


async def get_summary(user: User, db: AsyncSession) -> DashboardSummary:
    """Build financial state, call ML, return dashboard."""
    dashboard, _ = await ml_helpers.rebuild_and_prioritize(user, db)
    return dashboard
