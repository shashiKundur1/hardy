from fastapi import APIRouter, BackgroundTasks, status

from src.auth.dependencies import OptionalUser
from src.events import service
from src.events.schemas import Accepted, EventBatch

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def ingest(batch: EventBatch, background: BackgroundTasks, user: OptionalUser) -> Accepted:
    if user is None:
        return Accepted(accepted=0)
    background.add_task(service.record, user.id, batch.events)
    return Accepted(accepted=len(batch.events))
