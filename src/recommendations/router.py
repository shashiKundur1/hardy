from fastapi import APIRouter

from src.auth.dependencies import CurrentUser
from src.constants import TriggerReason
from src.recommendations import service
from src.recommendations.schemas import Decision

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("/refresh")
async def refresh(user: CurrentUser) -> Decision:
    return await service.refresh(user.id, TriggerReason.MANUAL)
