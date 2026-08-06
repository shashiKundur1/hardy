import json

from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from src.catalog.models import Product
from src.constants import SuppressionReason, TriggerReason
from src.database import session_factory
from src.events import service as events
from src.integrations import mesh
from src.recommendations import triggers
from src.recommendations.constants import DECISION_HISTORY
from src.recommendations.models import Recommendation, TriggerDecision
from src.recommendations.schemas import Decision, Efficiency


async def active_for(session: AsyncSession, user_id: int) -> Recommendation | None:
    statement = (
        select(Recommendation)
        .where(Recommendation.user_id == user_id, Recommendation.is_active.is_(True))
        .order_by(Recommendation.created_at.desc())
    )
    return (await session.scalars(statement)).first()


async def products_for(session: AsyncSession, recommendation: Recommendation) -> list[Product]:
    try:
        ordered = json.loads(recommendation.product_ids)
    except json.JSONDecodeError:
        return []
    if not ordered:
        return []
    found = {
        product.id: product
        for product in await session.scalars(select(Product).where(Product.id.in_(ordered)))
    }
    return [found[product_id] for product_id in ordered if product_id in found]


def reasons_for(recommendation: Recommendation) -> dict[int, dict]:
    try:
        trace = json.loads(recommendation.retrieval_trace or "{}")
    except json.JSONDecodeError:
        return {}
    grounds = {}
    for rank, item in enumerate(trace.get("after_rerank", []), start=1):
        facts = [f"{item['expected_life_years']} year life"]
        if item.get("repairability_score"):
            facts.append(f"repairability {item['repairability_score']:g} of 10")
        facts.append(
            "ownership on record" if item.get("evidence_source") else "no ownership record"
        )
        grounds[item["product_id"]] = {
            "rank": rank,
            "score": item["ranked_score"],
            "facts": facts,
            "sourced": bool(item.get("evidence_source")),
        }
    return grounds


async def record(session: AsyncSession, user_id: int, decision: Decision) -> None:
    session.add(
        TriggerDecision(
            user_id=user_id,
            fired=decision.fired,
            trigger_reason=decision.trigger_reason,
            suppression_reason=decision.suppression_reason,
            profile_hash=decision.profile_hash,
            catalog_version=decision.catalog_version,
            events_considered=decision.events_considered,
        )
    )
    await session.commit()


async def refresh(user_id: int, requested: TriggerReason | None = None) -> Decision:
    async with session_factory() as session:
        active = await active_for(session, user_id)
        decision = await triggers.decide(session, user_id, active, requested)
        await record(session, user_id, decision)

    if decision.fired:
        from src.agent import graph

        await graph.run(user_id, decision.trigger_reason, decision.profile_hash)
    return decision


async def decisions_for(session: AsyncSession, user_id: int) -> list[TriggerDecision]:
    statement = (
        select(TriggerDecision)
        .where(TriggerDecision.user_id == user_id)
        .order_by(TriggerDecision.created_at.desc(), TriggerDecision.id.desc())
        .limit(DECISION_HISTORY)
    )
    return list(await session.scalars(statement))


def _tally(column: ColumnElement, value: object) -> ColumnElement[int]:
    return func.sum(case((column == value, 1), else_=0))


async def efficiency(session: AsyncSession, user_id: int) -> Efficiency:
    counted = (
        await session.execute(
            select(
                func.count(),
                _tally(TriggerDecision.fired, True),
                _tally(TriggerDecision.suppression_reason, SuppressionReason.CACHE_HIT),
            ).where(TriggerDecision.user_id == user_id)
        )
    ).one()
    decisions, fired, cache_hits = counted[0], counted[1] or 0, counted[2] or 0
    recorded = await events.count_for(session, user_id)
    latest = await decisions_for(session, user_id)
    calls = mesh.call_count()
    return Efficiency(
        events_recorded=recorded,
        decisions=decisions,
        fired=fired,
        suppressed=decisions - fired,
        cache_hit_ratio=round(cache_hits / decisions, 4) if decisions else 0.0,
        llm_calls=calls,
        calls_per_event=round(calls / recorded, 4) if recorded else 0.0,
        last_trigger=next((row.trigger_reason for row in latest if row.fired), None),
        last_suppression=next((row.suppression_reason for row in latest if not row.fired), None),
    )


async def forget(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(Recommendation).where(Recommendation.user_id == user_id))
    await session.execute(delete(TriggerDecision).where(TriggerDecision.user_id == user_id))
    await session.commit()
