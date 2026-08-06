import json
from collections import Counter
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import session_factory
from src.events.constants import MEANINGFUL_TYPES
from src.events.models import Event
from src.events.schemas import IncomingEvent


async def record(user_id: int, batch: list[IncomingEvent]) -> None:
    stamp = uuid4().hex
    async with session_factory() as session:
        session.add_all(
            Event(
                user_id=user_id,
                batch=stamp,
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


def as_rows(recent: list[Event]) -> list[dict]:
    return [
        {
            "type": str(event.type),
            "product_id": event.product_id,
            "category": event.category,
            "query": event.query,
            "dwell_ms": event.dwell_ms,
        }
        for event in recent
    ]


async def meaningful_since(session: AsyncSession, user_id: int, since: datetime | None) -> int:
    statement = (
        select(func.count())
        .select_from(Event)
        .where(Event.user_id == user_id, Event.type.in_(MEANINGFUL_TYPES))
    )
    if since is not None:
        statement = statement.where(Event.created_at > since)
    return await session.scalar(statement) or 0


async def leading_category(session: AsyncSession, user_id: int, window: int) -> str | None:
    statement = (
        select(Event.category)
        .where(Event.user_id == user_id, Event.category.isnot(None))
        .order_by(Event.created_at.desc(), Event.id.desc())
        .limit(window)
    )
    recent = list(await session.scalars(statement))
    if not recent:
        return None
    return Counter(recent).most_common(1)[0][0]
