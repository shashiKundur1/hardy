import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import session_factory
from src.events.models import Event
from src.events.schemas import IncomingEvent


async def record(user_id: int, batch: list[IncomingEvent]) -> None:
    async with session_factory() as session:
        session.add_all(
            Event(
                user_id=user_id,
                type=incoming.type,
                product_id=incoming.product_id,
                category=incoming.category,
                query=incoming.query,
                dwell_ms=incoming.dwell_ms,
                payload=json.dumps({"path": incoming.path}) if incoming.path else None,
            )
            for incoming in batch
        )
        await session.commit()


async def count_for(session: AsyncSession, user_id: int) -> int:
    statement = select(func.count()).select_from(Event).where(Event.user_id == user_id)
    return await session.scalar(statement) or 0


async def recent_for(session: AsyncSession, user_id: int, limit: int) -> list[Event]:
    statement = (
        select(Event)
        .where(Event.user_id == user_id)
        .order_by(Event.created_at.desc(), Event.id.desc())
        .limit(limit)
    )
    return list(await session.scalars(statement))
