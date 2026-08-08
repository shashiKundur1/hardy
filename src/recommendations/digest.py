from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.catalog.models import Product
from src.config import settings
from src.constants import TriggerReason
from src.database import session_factory, utcnow
from src.events.constants import MEANINGFUL_TYPES
from src.events.models import Event
from src.integrations import mailer
from src.observability import get_logger
from src.recommendations import service
from src.recommendations.constants import (
    DIGEST_MAX_RECIPIENTS,
    DIGEST_PICKS,
    DIGEST_WINDOW_HOURS,
)
from src.recommendations.models import Recommendation
from src.rendering import templates

logger = get_logger("digest")


async def recipients(session: AsyncSession, since: datetime, limit: int) -> list[User]:
    statement = (
        select(User)
        .join(Event, Event.user_id == User.id)
        .where(Event.created_at >= since, Event.type.in_(tuple(MEANINGFUL_TYPES)))
        .group_by(User.id)
        .order_by(func.count(Event.id).desc())
        .limit(limit)
    )
    return list(await session.scalars(statement))


def subject_for(products: list[Product]) -> str:
    if not products:
        return "What Hardy makes of your browsing"
    return f"{products[0].title}, and {len(products) - 1} more worth keeping"


def link(path: str) -> str:
    return f"{settings.public_base_url.rstrip('/')}{path}"


def as_text(user: User, recommendation: Recommendation, products: list[Product]) -> str:
    lines = [f"Hello {user.shown_name},", "", recommendation.narrative, ""]
    for product in products:
        lines.append(
            f"- {product.title} by {product.brand}: "
            f"₹{product.cost_per_year:,.0f} per year over {product.expected_life_years} years"
        )
    lines += [
        "",
        f"The full case, with the record behind every claim: {link('/recommendations')}",
        "",
        f"Hardy read {recommendation.events_covered} of your actions to write this.",
        f"Everything it holds, and the control that deletes it: {link('/footprint')}",
    ]
    return "\n".join(lines)


def as_html(user: User, recommendation: Recommendation, products: list[Product]) -> str:
    return templates.env.get_template("digest_email.html").render(
        user=user,
        recommendation=recommendation,
        products=products,
        link=link,
    )


def compose(user: User, recommendation: Recommendation, products: list[Product]):
    return mailer.compose(
        user.email,
        subject_for(products),
        as_text(user, recommendation, products),
        as_html(user, recommendation, products),
    )


async def deliver(user: User) -> bool:
    await service.refresh(user.id, TriggerReason.SCHEDULED)
    async with session_factory() as session:
        active = await service.active_for(session, user.id)
        if active is None:
            return False
        products = (await service.products_for(session, active))[:DIGEST_PICKS]
    return await mailer.send(compose(user, active, products))


async def run() -> dict:
    since = utcnow() - timedelta(hours=DIGEST_WINDOW_HOURS)
    async with session_factory() as session:
        people = await recipients(session, since, DIGEST_MAX_RECIPIENTS)
    sent = 0
    for person in people:
        try:
            sent += await deliver(person)
        except Exception:
            logger.exception("digest failed for account %s", person.id)
    logger.info("digest considered %s accounts and sent %s", len(people), sent)
    return {"considered": len(people), "sent": sent}
