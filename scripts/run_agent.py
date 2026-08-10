import asyncio
import json
import os
import secrets
from uuid import uuid4

from sqlalchemy import delete, select

from src.agent import graph
from src.auth.models import User
from src.auth.service import hash_password
from src.catalog.models import Product
from src.constants import EventType, Role, TriggerReason
from src.database import create_schema, session_factory
from src.events.models import Event
from src.integrations import vectorstore
from src.recommendations import service as recommendations
from src.recommendations import triggers
from src.recommendations.models import Recommendation

DEMO_EMAIL = "demo@hardy.local"
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(24)


async def demo_user(session) -> User:
    user = await session.scalar(select(User).where(User.email == DEMO_EMAIL))
    if user is None:
        user = User(
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
            role=Role.USER,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def seed_behaviour(session, user: User) -> int:
    await session.execute(delete(Event).where(Event.user_id == user.id))
    cookware = list(
        await session.scalars(select(Product).where(Product.category == "cookware").limit(3))
    )
    tools = list(await session.scalars(select(Product).where(Product.category == "tools").limit(2)))
    stamp = uuid4().hex
    rows = [Event(user_id=user.id, batch=stamp, type=EventType.PAGE_VIEW, category="cookware")]
    for product in cookware:
        rows.append(
            Event(
                user_id=user.id,
                batch=stamp,
                type=EventType.PRODUCT_VIEW,
                product_id=product.id,
                category="cookware",
                dwell_ms=42_000,
            )
        )
    for product in tools:
        rows.append(
            Event(
                user_id=user.id,
                batch=stamp,
                type=EventType.PRODUCT_VIEW,
                product_id=product.id,
                category="tools",
                dwell_ms=18_000,
            )
        )
    rows.append(
        Event(
            user_id=user.id, batch=stamp, type=EventType.SEARCH, query="pan that lasts a lifetime"
        )
    )
    rows.append(
        Event(user_id=user.id, batch=stamp, type=EventType.SEARCH, query="repairable cast iron")
    )
    session.add_all(rows)
    await session.commit()
    return len(rows)


async def main() -> None:
    await create_schema()
    await vectorstore.ensure_collection()

    async with session_factory() as session:
        user = await demo_user(session)
        seeded = await seed_behaviour(session, user)

    print(f"demo user {user.id} with {seeded} behaviour events")

    async with session_factory() as session:
        active = await recommendations.active_for(session, user.id)
        decision = await triggers.decide(session, user.id, active, TriggerReason.MANUAL)
        await recommendations.record(session, user.id, decision)

    print(f"trigger: {decision.trigger_reason or decision.suppression_reason}")
    print(f"catalog version: {decision.catalog_version}")
    print(f"profile hash: {decision.profile_hash[:16]}")
    if not decision.fired:
        print("suppressed, no model call made")
        return

    state = await graph.run(user.id, decision.trigger_reason, decision.profile_hash)

    print("nodes visited:", " -> ".join(state["nodes_visited"]))
    print("refine loops:", state["refine_count"])
    print("query:", state["query"])
    print("intent:", json.dumps(state["intent"], indent=2))
    print("candidates:")
    for item in state["candidates"]:
        print(
            f"  {item['ranked_score']:.4f}  semantic {item['semantic_score']:.4f}  "
            f"{item['title']} ({item['cost_per_year']:.0f}/yr, "
            f"source: {'yes' if item['evidence_source'] else 'none'})"
        )
    print("\nnarrative:\n")
    print(state["narrative"])

    async with session_factory() as session:
        stored = await session.scalar(
            select(Recommendation)
            .where(
                Recommendation.user_id == user.id,
                Recommendation.is_active.is_(True),
            )
            .order_by(Recommendation.created_at.desc())
        )

    assert stored is not None, "the agent did not store a recommendation"
    assert stored.narrative.strip(), "the stored recommendation has no narrative"
    assert json.loads(stored.product_ids), "the stored recommendation names no products"
    print(
        f"\nstored recommendation {stored.id}: {stored.events_covered} events, "
        f"{stored.tokens_used} tokens, model {stored.model_used}"
    )


if __name__ == "__main__":
    asyncio.run(main())
