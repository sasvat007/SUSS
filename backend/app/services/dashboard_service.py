"""
Dashboard Service — now powered by direct CapitalSense engine integration.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.services import engine_service


async def get_summary(user: User, db: AsyncSession) -> dict:
    """
    Runs the full 3-engine pipeline and returns the complete analysis.
    Replaces the old ML HTTP proxy approach.
    """
    return await engine_service.run_full_analysis(user, db)
