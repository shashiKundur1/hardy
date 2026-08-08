from datetime import timedelta
from uuid import uuid4

import pytest

from src.auth.models import User
from src.auth.service import hash_password
from src.constants import EventType
from src.database import session_factory, utcnow
from src.events.models import Event
from src.integrations import mailer, mesh
from src.recommendations import digest
from src.recommendations.constants import DIGEST_WINDOW_HOURS
from src.recommendations.models import Recommendation

PASSWORD = "digest-password"


async def _person(email: str, *, active_events: int = 3, recommended: bool = True) -> User:
    async with session_factory() as session:
        person = User(email=email, password_hash=hash_password(PASSWORD))
        session.add(person)
        await session.commit()
        await session.refresh(person)
        stamp = uuid4().hex
        session.add_all(
            [
                Event(
                    user_id=person.id,
                    batch=stamp,
                    type=EventType.PRODUCT_VIEW,
                    category="cookware",
                )
                for _ in range(active_events)
            ]
        )
        if recommended:
            session.add(
                Recommendation(
                    user_id=person.id,
                    narrative="Cast iron outlives the kitchen it was bought for.",
                    product_ids="[]",
                    interest_profile='{"categories": ["cookware"], "stage": "browsing"}',
                    trigger_reason="scheduled",
                    profile_hash="stable",
                    events_covered=active_events,
                    model_used="offline",
                )
            )
        await session.commit()
        return person


async def _stale_person(email: str) -> User:
    person = await _person(email)
    async with session_factory() as session:
        old = utcnow() - timedelta(hours=DIGEST_WINDOW_HOURS + 2)
        await session.execute(
            Event.__table__.update().where(Event.user_id == person.id).values(created_at=old)
        )
        await session.commit()
    return person


@pytest.fixture
def outbox(monkeypatch):
    posted = []

    async def capture(message):
        posted.append(message)
        return True

    monkeypatch.setattr(mailer, "send", capture)
    return posted


@pytest.fixture(autouse=True)
def _offline(offline_mesh):
    offline_mesh()


async def test_only_accounts_active_in_the_window_get_a_digest():
    await _person("recent@hardy.test")
    await _stale_person("stale@hardy.test")
    async with session_factory() as session:
        people = await digest.recipients(
            session, utcnow() - timedelta(hours=DIGEST_WINDOW_HOURS), 50
        )
    assert [person.email for person in people] == ["recent@hardy.test"]


async def test_the_recipient_list_is_capped_so_a_run_always_terminates():
    for index in range(6):
        await _person(f"crowd{index}@hardy.test")
    async with session_factory() as session:
        people = await digest.recipients(
            session, utcnow() - timedelta(hours=DIGEST_WINDOW_HOURS), 4
        )
    assert len(people) == 4


async def test_an_account_with_nothing_to_say_is_not_mailed(outbox):
    await _person("quiet@hardy.test", recommended=False)
    result = await digest.run()
    assert result["sent"] == 0
    assert outbox == []


async def test_a_digest_carries_the_narrative_and_a_plain_text_alternative(outbox):
    await _person("reader@hardy.test")
    await digest.run()
    assert len(outbox) == 1
    message = outbox[0]
    assert message["To"] == "reader@hardy.test"
    body = message.get_body(("plain",)).get_content()
    assert "Cast iron outlives" in body
    assert message.get_body(("html",)) is not None


async def test_links_in_the_digest_are_absolute_because_email_has_no_origin(outbox):
    await _person("linked@hardy.test")
    await digest.run()
    body = outbox[0].get_body(("plain",)).get_content()
    assert "http://localhost:8000/recommendations" in body
    assert "http://localhost:8000/footprint" in body


async def test_one_failing_account_does_not_stop_the_run(monkeypatch, outbox):
    await _person("good@hardy.test")
    await _person("bad@hardy.test")
    original = digest.deliver

    async def explode(user):
        if user.email == "bad@hardy.test":
            raise RuntimeError("smtp refused")
        return await original(user)

    monkeypatch.setattr(digest, "deliver", explode)
    result = await digest.run()
    assert result["considered"] == 2
    assert result["sent"] == 1


async def test_a_scheduled_run_over_unchanged_behaviour_costs_no_ai_call(outbox):
    await _person("thrifty@hardy.test")
    mesh.reset_call_log()
    await digest.run()
    await digest.run()
    assert mesh.call_count() == 0


async def test_an_unconfigured_mailer_declines_rather_than_raising():
    await _person("nowhere@hardy.test")
    result = await digest.run()
    assert result["considered"] == 1
    assert result["sent"] == 0
