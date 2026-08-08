from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.auth.models import User
from src.auth.service import declared_interests
from src.database import session_factory
from src.main import app

PASSWORD = "onboarding-password"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


async def _stored(email: str) -> User:
    async with session_factory() as session:
        return await session.scalar(select(User).where(User.email == email))


async def test_a_new_account_lands_in_onboarding_not_the_shop():
    async with _client() as client:
        response = await client.post(
            "/signup", data={"email": "fresh@hardy.test", "password": PASSWORD}
        )
    assert response.status_code == 303
    assert response.headers["location"] == "/welcome"


async def test_onboarding_records_what_the_shopper_declared():
    async with _client() as client:
        await client.post("/signup", data={"email": "keen@hardy.test", "password": PASSWORD})
        await client.post("/welcome/interests", data={"interests": ["cookware", "tools"]})
        await client.post(
            "/welcome/finish",
            data={"shopping_for": "a pan for life", "display_name": "Keen"},
        )
    person = await _stored("keen@hardy.test")
    assert declared_interests(person) == ["cookware", "tools"]
    assert person.shopping_for == "a pan for life"
    assert person.display_name == "Keen"
    assert person.onboarded_at is not None


async def test_onboarding_is_shown_once_and_never_again():
    async with _client() as client:
        await client.post("/signup", data={"email": "once@hardy.test", "password": PASSWORD})
        first = await client.get("/welcome")
        await client.post("/welcome/skip")
        second = await client.get("/welcome")
    assert first.status_code == 200
    assert second.status_code == 303
    assert second.headers["location"] == "/shop"


async def test_skipping_costs_the_shopper_nothing():
    async with _client() as client:
        await client.post("/signup", data={"email": "hurry@hardy.test", "password": PASSWORD})
        response = await client.post("/welcome/skip")
        shop = await client.get("/shop")
    assert response.headers["location"] == "/shop"
    assert shop.status_code == 200
    person = await _stored("hurry@hardy.test")
    assert person.onboarded_at is not None
    assert declared_interests(person) == []


async def test_a_category_that_is_not_ours_is_refused():
    async with _client() as client:
        await client.post("/signup", data={"email": "sneaky@hardy.test", "password": PASSWORD})
        response = await client.post("/welcome/interests", data={"interests": ["not-a-thing"]})
    assert response.status_code == 422
    assert declared_interests(await _stored("sneaky@hardy.test")) == []


async def test_signing_in_before_finishing_returns_to_onboarding():
    async with _client() as client:
        await client.post("/signup", data={"email": "paused@hardy.test", "password": PASSWORD})
    async with _client() as returning:
        response = await returning.post(
            "/login", data={"email": "paused@hardy.test", "password": PASSWORD, "next": "/shop"}
        )
    assert response.headers["location"] == "/welcome"


async def test_signing_in_after_finishing_goes_where_the_shopper_was_headed():
    async with _client() as client:
        await client.post("/signup", data={"email": "done@hardy.test", "password": PASSWORD})
        await client.post("/welcome/skip")
    async with _client() as returning:
        response = await returning.post(
            "/login",
            data={"email": "done@hardy.test", "password": PASSWORD, "next": "/category/tools"},
        )
    assert response.headers["location"] == "/category/tools"


async def test_a_failed_sign_in_keeps_the_email_and_names_the_field():
    async with _client() as client:
        await client.post("/signup", data={"email": "typo@hardy.test", "password": PASSWORD})
    async with _client() as returning:
        response = await returning.post(
            "/login", data={"email": "typo@hardy.test", "password": "wrong-password"}
        )
    assert response.status_code == 401
    assert 'value="typo@hardy.test"' in response.text


async def test_a_short_password_is_refused_against_the_password_field():
    async with _client() as client:
        response = await client.post(
            "/signup", data={"email": "short@hardy.test", "password": "abc"}
        )
    assert response.status_code == 422
    assert 'id="password-error"' in response.text
    assert 'value="short@hardy.test"' in response.text
