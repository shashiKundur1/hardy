import hashlib
import json
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.catalog import service as catalog
from src.constants import (
    EVENT_THRESHOLD,
    INTEREST_SHIFT_WINDOW,
    MIN_EVENTS_TO_REASON,
    RATE_FLOOR_MINUTES,
    SuppressionReason,
    TriggerReason,
)
from src.database import utcnow
from src.events import service as events
from src.events.constants import MEANINGFUL_TYPES, RECENT_LIMIT
from src.recommendations.models import Recommendation
from src.recommendations.schemas import Decision


def profile_hash(rows: list[dict], catalog_version: str) -> str:
    signature = json.dumps(
        {
            "categories": sorted({row["category"] for row in rows if row["category"]}),
            "product_ids": sorted({row["product_id"] for row in rows if row["product_id"]}),
            "queries": sorted({row["query"] for row in rows if row["query"]}),
            "catalog_version": catalog_version,
        },
        sort_keys=True,
    )
    return hashlib.sha256(signature.encode()).hexdigest()


def _stored_categories(active: Recommendation) -> set[str]:
    try:
        return set(json.loads(active.interest_profile).get("categories", []))
    except (TypeError, AttributeError, json.JSONDecodeError):
        return set()


async def decide(
    session: AsyncSession,
    user_id: int,
    active: Recommendation | None,
    requested: TriggerReason | None = None,
) -> Decision:
    rows = events.as_rows(await events.recent_for(session, user_id, RECENT_LIMIT))
    meaningful = [row for row in rows if row["type"] in MEANINGFUL_TYPES]
    catalog_version = await catalog.version(session)
    fingerprint = profile_hash(meaningful, catalog_version)
    verdict = Decision(
        fired=False,
        profile_hash=fingerprint,
        catalog_version=catalog_version,
        events_considered=len(meaningful),
    )

    def suppress(reason: SuppressionReason) -> Decision:
        return verdict.model_copy(update={"suppression_reason": reason})

    def fire(reason: TriggerReason) -> Decision:
        return verdict.model_copy(update={"fired": True, "trigger_reason": reason})

    if len(meaningful) < MIN_EVENTS_TO_REASON:
        return suppress(SuppressionReason.TOO_FEW_EVENTS)

    if active is None:
        if requested is not None:
            return fire(requested)
        if len(meaningful) < EVENT_THRESHOLD:
            return suppress(SuppressionReason.THIN_SIGNAL)
        return fire(TriggerReason.EVENT_THRESHOLD)

    if active.profile_hash == fingerprint:
        return suppress(SuppressionReason.CACHE_HIT)

    if requested is not None:
        return fire(requested)

    if active.created_at > utcnow() - timedelta(minutes=RATE_FLOOR_MINUTES):
        return suppress(SuppressionReason.RATE_FLOOR)

    if await events.meaningful_since(session, user_id, active.created_at) >= EVENT_THRESHOLD:
        return fire(TriggerReason.EVENT_THRESHOLD)

    leading = await events.leading_category(session, user_id, INTEREST_SHIFT_WINDOW)
    if leading is not None and leading not in _stored_categories(active):
        return fire(TriggerReason.INTEREST_SHIFT)

    return suppress(SuppressionReason.THIN_SIGNAL)
