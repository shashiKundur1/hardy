from httpx import ASGITransport, AsyncClient

from src.auth.models import User
from src.auth.service import hash_password
from src.database import session_factory
from src.integrations import mesh
from src.main import app
from src.recommendations.models import Recommendation

PASSWORD = "in-context-password"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


async def _person(email: str, *, recommended: bool = True) -> User:
    async with session_factory() as session:
        person = User(email=email, password_hash=hash_password(PASSWORD))
        session.add(person)
        await session.commit()
        await session.refresh(person)
        if recommended:
            session.add(
                Recommendation(
                    user_id=person.id,
                    narrative="Three cookware views and a search for repairable says one thing.",
                    product_ids="[]",
                    interest_profile='{"categories": ["cookware"]}',
                    trigger_reason="event_threshold",
                    profile_hash="stable",
                    events_covered=14,
                    model_used="offline",
                )
            )
            await session.commit()
        return person


async def _signed_in(client: AsyncClient, email: str) -> None:
    await client.post("/login", data={"email": email, "password": PASSWORD})


async def test_silence_is_the_default_before_the_behaviour_says_anything():
    await _person("quiet@hardy.test", recommended=False)
    async with _client() as client:
        await _signed_in(client, "quiet@hardy.test")
        response = await client.get("/category/cookware")
    assert 'class="nudge"' not in response.text


async def test_the_recommendation_surfaces_while_browsing_not_only_on_its_own_page():
    await _person("browsing@hardy.test")
    async with _client() as client:
        await _signed_in(client, "browsing@hardy.test")
        response = await client.get("/category/cookware")
    assert 'class="nudge"' in response.text
    assert "Three cookware views" in response.text


async def test_it_stays_out_of_the_way_where_the_shopper_has_stated_their_intent():
    await _person("deliberate@hardy.test")
    async with _client() as client:
        await _signed_in(client, "deliberate@hardy.test")
        for path in ("/search?q=pan", "/product/1"):
            response = await client.get(path)
            assert 'class="nudge"' not in response.text, path


async def test_it_says_which_behaviour_earned_it():
    await _person("why@hardy.test")
    async with _client() as client:
        await _signed_in(client, "why@hardy.test")
        response = await client.get("/category/cookware")
    assert "Hardy read 14 of your actions" in response.text
    assert "what you have been looking at" in response.text


async def test_a_dismissal_is_respected_on_the_next_page_too():
    await _person("done@hardy.test")
    async with _client() as client:
        await _signed_in(client, "done@hardy.test")
        dismissed = await client.post(
            "/recommendations/dismiss", data={"back": "/category/cookware"}
        )
        assert dismissed.headers["location"] == "/category/cookware"
        for path in ("/category/cookware", "/search?q=pan", "/category/tools"):
            response = await client.get(path)
            assert 'class="nudge"' not in response.text, path


async def test_a_dismissal_returns_the_shopper_where_they_were_filters_and_all():
    await _person("filtered@hardy.test")
    async with _client() as client:
        await _signed_in(client, "filtered@hardy.test")
        response = await client.post(
            "/recommendations/dismiss", data={"back": "/category/cookware?sort=rate&sourced=True"}
        )
    assert response.headers["location"] == "/category/cookware?sort=rate&sourced=True"


async def test_a_dismissal_cannot_be_used_to_send_someone_off_site():
    await _person("safe@hardy.test")
    async with _client() as client:
        await _signed_in(client, "safe@hardy.test")
        response = await client.post(
            "/recommendations/dismiss", data={"back": "https://evil.example/steal"}
        )
    assert response.headers["location"] == "/shop"


async def test_a_fresh_recommendation_speaks_again_after_an_earlier_one_was_dismissed():
    person = await _person("again@hardy.test")
    async with _client() as client:
        await _signed_in(client, "again@hardy.test")
        await client.post("/recommendations/dismiss", data={"back": "/category/cookware"})
        assert 'class="nudge"' not in (await client.get("/category/cookware")).text
        async with session_factory() as session:
            session.add(
                Recommendation(
                    user_id=person.id,
                    narrative="Your browsing moved to tools, and that changes the argument.",
                    product_ids="[]",
                    interest_profile='{"categories": ["tools"]}',
                    trigger_reason="interest_shift",
                    profile_hash="moved",
                    events_covered=20,
                    model_used="offline",
                )
            )
            await session.commit()
        response = await client.get("/category/cookware")
    assert 'class="nudge"' in response.text
    assert "your browsing moving to a new category" in response.text


async def test_showing_the_surface_costs_no_ai_call():
    await _person("thrifty@hardy.test")
    async with _client() as client:
        await _signed_in(client, "thrifty@hardy.test")
        mesh.reset_call_log()
        for _ in range(5):
            await client.get("/category/cookware")
    assert mesh.call_count() == 0


async def test_the_surface_never_covers_what_the_shopper_came_to_read():
    await _person("unblocked@hardy.test")
    async with _client() as client:
        await _signed_in(client, "unblocked@hardy.test")
        response = await client.get("/category/cookware")
    assert 'role="dialog"' not in response.text
    assert "aria-modal" not in response.text
    assert 'role="status"' in response.text
