from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.recommendations.models import Recommendation


async def active_for(session: AsyncSession, user_id: int) -> Recommendation | None:
    statement = (
        select(Recommendation)
        .where(Recommendation.user_id == user_id, Recommendation.is_active.is_(True))
        .order_by(Recommendation.created_at.desc())
    )
    return (await session.scalars(statement)).first()
