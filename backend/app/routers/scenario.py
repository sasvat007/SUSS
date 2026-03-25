from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.scenario import ScenarioSimulateRequest, ScenarioOut
from app.services import scenario_service

router = APIRouter(prefix="/scenario", tags=["Scenario"])


@router.post("/simulate")
async def simulate(
    payload: ScenarioSimulateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Proxy scenario to ML backend and persist history.
    Backend does NO computation — passes scenario as-is.
    """
    return await scenario_service.simulate(payload.scenario, current_user, db)


@router.get("/history", response_model=List[ScenarioOut])
async def history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await scenario_service.get_history(current_user, db)
