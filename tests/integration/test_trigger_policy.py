import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.auth.models import User
from src.catalog import service as catalog
from src.catalog.schemas import ProductWrite
from src.constants import (
    EVENT_THRESHOLD,
    EventType,
    Ownership,
    SuppressionReason,
    TriggerReason,
)
from src.database import session_factory
from src.events.models import Event
from src.recommendations import service as recommendations
from src.recommendations import triggers
from src.recommendations.models import Recommendation

INTENT = json.dumps(
    {
        "categories": ["cookware"],
        "budget_hint": "mid",
        "priorities": ["repairable", "long life"],
        "stage": "comparing",
        "evidence": "five cookware views",
    }
)
NARRATIVE = "Cast iron outlasts everything else in this list, and the parts are still made."


def _product(index: int) -> ProductWrite:
    return ProductWrite(
        title=f"Skillet {index}",
        brand="Testworks",
        description="A pan that exists to prove the trigger policy.",
        category="cookware",
        price=Decimal("4200.00"),
        expected_life_years=40,
        ownership_type=Ownership.FAMILY,
        ownership_note="Held by the founding family since 1896.",
        evidence_source="https://example.test/ownership",
    )


async def _user(session) -> User:
    person = User(email="trigger@hardy.test", password_hash="x")
    session.add(person)
    await session.commit()
    await session.refresh(person)
    return person


async def _browse(session, user: User, count: int, category: str = "cookware") -> None:
    stamp = uuid4().hex
    session.add_all(
        Event(
            user_id=user.id,
            batch=stamp,
            type=EventType.PRODUCT_VIEW,
            product_id=None,
            category=category,
            dwell_ms=1000 + index,
        )
        for index in range(count)
    )
    await session.commit()


async def test_too_few_events_suppresses_before_any_model_call(offline_mesh):
    fake = offline_mesh()
    async with session_factory() as session:
        user = await _user(session)
        await _browse(session, user, 2)
        decision = await triggers.decide(session, user.id, None)
    assert decision.fired is False
    assert decision.suppression_reason == SuppressionReason.TOO_FEW_EVENTS
    assert fake.calls == 0


async def test_a_thin_signal_waits_for_the_threshold(offline_mesh):
    fake = offline_mesh()
    async with session_factory() as session:
        user = await _user(session)
        await _browse(session, user, 6)
        decision = await triggers.decide(session, user.id, None)
    assert decision.fired is False
    assert decision.suppression_reason == SuppressionReason.THIN_SIGNAL
    assert fake.calls == 0


async def test_the_event_threshold_fires_the_first_recommendation(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        user = await _user(session)
        await _browse(session, user, EVENT_THRESHOLD)
        decision = await triggers.decide(session, user.id, None)
    assert decision.fired is True
    assert decision.trigger_reason == TriggerReason.EVENT_THRESHOLD


async def test_page_views_alone_never_reach_the_threshold(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        user = await _user(session)
        session.add_all(
            Event(user_id=user.id, batch=uuid4().hex, type=EventType.PAGE_VIEW, category="cookware")
            for _ in range(EVENT_THRESHOLD * 2)
        )
        await session.commit()
        decision = await triggers.decide(session, user.id, None)
    assert decision.fired is False
    assert decision.suppression_reason == SuppressionReason.TOO_FEW_EVENTS


async def test_a_matching_profile_is_a_cache_hit(offline_mesh):
    fake = offline_mesh()
    async with session_factory() as session:
        user = await _user(session)
        await _browse(session, user, EVENT_THRESHOLD)
        first = await triggers.decide(session, user.id, None)
        active = Recommendation(
            user_id=user.id,
            narrative=NARRATIVE,
            product_ids="[]",
            interest_profile=INTENT,
            trigger_reason=TriggerReason.EVENT_THRESHOLD,
            profile_hash=first.profile_hash,
            events_covered=EVENT_THRESHOLD,
            model_used="offline",
        )
        session.add(active)
        await session.commit()
        second = await triggers.decide(session, user.id, active)
    assert second.fired is False
    assert second.suppression_reason == SuppressionReason.CACHE_HIT
    assert fake.calls == 0


async def test_a_catalog_change_invalidates_the_cache(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        user = await _user(session)
        await _browse(session, user, EVENT_THRESHOLD)
        first = await triggers.decide(session, user.id, None)
        active = Recommendation(
            user_id=user.id,
            narrative=NARRATIVE,
            product_ids="[]",
            interest_profile=INTENT,
            trigger_reason=TriggerReason.EVENT_THRESHOLD,
            profile_hash=first.profile_hash,
            events_covered=EVENT_THRESHOLD,
            model_used="offline",
        )
        session.add(active)
        await session.commit()
        assert (await triggers.decide(session, user.id, active)).suppression_reason == (
            SuppressionReason.CACHE_HIT
        )

        await catalog.create(session, _product(1))
        after = await triggers.decide(session, user.id, active)
    assert after.suppression_reason != SuppressionReason.CACHE_HIT


async def test_the_rate_floor_holds_a_fresh_recommendation(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        user = await _user(session)
        await _browse(session, user, EVENT_THRESHOLD)
        active = Recommendation(
            user_id=user.id,
            narrative=NARRATIVE,
            product_ids="[]",
            interest_profile=INTENT,
            trigger_reason=TriggerReason.EVENT_THRESHOLD,
            profile_hash="a-profile-that-does-not-match",
            events_covered=1,
            model_used="offline",
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        session.add(active)
        await session.commit()
        decision = await triggers.decide(session, user.id, active)
    assert decision.fired is False
    assert decision.suppression_reason == SuppressionReason.RATE_FLOOR


async def test_a_manual_request_beats_the_rate_floor_but_not_the_cache(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        user = await _user(session)
        await _browse(session, user, EVENT_THRESHOLD)
        stale = Recommendation(
            user_id=user.id,
            narrative=NARRATIVE,
            product_ids="[]",
            interest_profile=INTENT,
            trigger_reason=TriggerReason.EVENT_THRESHOLD,
            profile_hash="a-profile-that-does-not-match",
            events_covered=1,
            model_used="offline",
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        session.add(stale)
        await session.commit()
        forced = await triggers.decide(session, user.id, stale, TriggerReason.MANUAL)
        assert forced.fired is True
        assert forced.trigger_reason == TriggerReason.MANUAL

        stale.profile_hash = forced.profile_hash
        await session.commit()
        cached = await triggers.decide(session, user.id, stale, TriggerReason.MANUAL)
    assert cached.fired is False
    assert cached.suppression_reason == SuppressionReason.CACHE_HIT


async def test_an_interest_shift_fires_once_the_rate_floor_has_passed(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        user = await _user(session)
        await _browse(session, user, EVENT_THRESHOLD - 6, category="footwear")
        active = Recommendation(
            user_id=user.id,
            narrative=NARRATIVE,
            product_ids="[]",
            interest_profile=INTENT,
            trigger_reason=TriggerReason.EVENT_THRESHOLD,
            profile_hash="a-profile-that-does-not-match",
            events_covered=1,
            model_used="offline",
            created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2),
        )
        session.add(active)
        await session.commit()
        decision = await triggers.decide(session, user.id, active)
    assert decision.fired is True
    assert decision.trigger_reason == TriggerReason.INTEREST_SHIFT


async def test_twenty_clicks_produce_one_agent_run(offline_mesh):
    fake = offline_mesh([INTENT, NARRATIVE])
    async with session_factory() as session:
        user = await _user(session)
        for index in range(3):
            await catalog.create(session, _product(index))
        await _browse(session, user, EVENT_THRESHOLD)

    first = await recommendations.refresh(user.id)
    assert first.fired is True, first
    after_first = fake.calls
    assert after_first > 0, "the agent never reached Mesh"

    for _ in range(20):
        assert (await recommendations.refresh(user.id)).fired is False

    assert fake.calls == after_first, "browsing on an unchanged profile called the model again"

    async with session_factory() as session:
        report = await recommendations.efficiency(session, user.id)
    assert report.decisions == 21
    assert report.fired == 1
    assert report.suppressed == 20
    assert report.cache_hit_ratio > 0.0
    assert report.last_suppression == SuppressionReason.CACHE_HIT
