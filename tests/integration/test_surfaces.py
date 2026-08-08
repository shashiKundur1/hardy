import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app

PASSWORD = "surface-password"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


async def test_the_landing_page_does_not_load_the_behaviour_tracker():
    async with _client() as client:
        response = await client.get("/")
    assert "tracker.js" not in response.text


async def test_the_landing_page_sells_nothing():
    async with _client() as client:
        response = await client.get("/")
    assert "/product/" not in response.text
    assert "per year</span>" not in response.text


@pytest.mark.parametrize("path", ["/login", "/signup", "/admin/login"])
async def test_an_auth_page_does_not_load_the_behaviour_tracker(path):
    async with _client() as client:
        response = await client.get(path)
    assert "tracker.js" not in response.text


async def test_the_storefront_does_load_the_behaviour_tracker(shopper):
    response = await shopper.get("/shop")
    assert "tracker.js" in response.text


async def test_onboarding_offers_no_way_to_wander_off():
    async with _client() as client:
        await client.post("/signup", data={"email": "focus@hardy.test", "password": PASSWORD})
        response = await client.get("/welcome")
    assert 'aria-label="Categories"' not in response.text
    assert 'aria-label="Primary"' not in response.text
    assert "Skip for now" in response.text


async def test_a_signed_out_visitor_can_always_reach_sign_in_from_the_landing_page():
    async with _client() as client:
        response = await client.get("/")
    assert 'href="/login"' in response.text
    assert 'href="/signup"' in response.text
    assert "account--always" in response.text
