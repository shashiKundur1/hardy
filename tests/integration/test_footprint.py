from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from src.auth.models import User
from src.auth.service import hash_password
from src.constants import EventType
from src.database import session_factory
from src.events import service as events
from src.events.models import Event
from src.main import app
from src.recommendations import service as recommendations
from src.recommendations.models import Recommendation, TriggerDecision

PASSWORD = "footprint-test-password"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


async def _person_with_history(session) -> User:
    person = User(email="footprint@hardy.test", password_hash=hash_password(PASSWORD))
    session.add(person)
    await session.commit()
    await session.refresh(person)
    stamp = uuid4().hex
    session.add_all(
        [
            Event(user_id=person.id, batch=stamp, type=EventType.PRODUCT_VIEW, category="cookware"),
            Event(user_id=person.id, batch=stamp, type=EventType.SEARCH, query="cast iron"),
            Event(user_id=person.id, batch=uuid4().hex, type=EventType.PAGE_VIEW, category="tools"),
        ]
    )
    session.add(
        Recommendation(
            user_id=person.id,
            narrative="A narrative that should not survive being forgotten.",
            product_ids="[]",
            interest_profile='{"categories": ["cookware"], "stage": "browsing"}',
            trigger_reason="manual",
            profile_hash="x",
            events_covered=3,
            model_used="offline",
        )
    )
    session.add(
        TriggerDecision(
            user_id=person.id,
            fired=True,
            trigger_reason="manual",
            profile_hash="x",
            catalog_version="0@empty",
            events_considered=3,
        )
    )
    await session.commit()
    return person


async def _signed_in(client: AsyncClient, email: str) -> None:
    await client.post("/login", data={"email": email, "password": PASSWORD})


async def test_a_signed_out_visitor_is_asked_to_sign_in():
    async with _client() as client:
        response = await client.get("/footprint")
    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=/footprint"


async def test_the_footprint_counts_each_kind_of_action():
    async with session_factory() as session:
        person = await _person_with_history(session)
        summary = await events.summary_for(session, person.id)
    kinds = {row["type"]: row["total"] for row in summary}
    assert kinds == {"product_view": 1, "search": 1, "page_view": 1}
    assert all(row["example"] is not None for row in summary)
    assert all(row["last_seen"] is not None for row in summary)


async def test_the_page_shows_the_actions_and_what_was_concluded():
    async with session_factory() as session:
        person = await _person_with_history(session)

    async with _client() as client:
        await _signed_in(client, person.email)
        body = (await client.get("/footprint")).text
    assert "cast iron" in body
    assert "What Hardy concluded" in body
    assert "cookware" in body
    assert "Delete" in body


async def test_forgetting_removes_the_actions_the_recommendations_and_the_decisions():
    async with session_factory() as session:
        person = await _person_with_history(session)
        assert await events.count_for(session, person.id) == 3

    async with _client() as client:
        await _signed_in(client, person.email)
        response = await client.post("/footprint/forget")
    assert response.status_code == 303

    async with session_factory() as session:
        assert await events.count_for(session, person.id) == 0
        assert await recommendations.active_for(session, person.id) is None
        assert await recommendations.decisions_for(session, person.id) == []


async def test_forgetting_needs_an_account():
    async with _client() as client:
        response = await client.post("/footprint/forget")
    assert response.status_code in (303, 401)
