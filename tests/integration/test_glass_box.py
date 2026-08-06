from decimal import Decimal

from httpx import ASGITransport, AsyncClient

from src.catalog import service as catalog
from src.catalog.schemas import ProductWrite
from src.database import session_factory
from src.main import app

SAMPLE = ProductWrite(
    title="Glass box skillet",
    brand="Testworks",
    description="A pan that exists so the dual-write panel has something to count.",
    category="cookware",
    price=Decimal("4200.00"),
    expected_life_years=40,
)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


async def test_the_glass_box_opens_without_signing_in():
    async with _client() as client:
        response = await client.get("/debug")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Glass box" in response.text


async def test_it_invites_a_signed_out_visitor_rather_than_showing_them_nothing():
    async with _client() as client:
        body = (await client.get("/debug")).text
    assert "Sign in" in body
    assert "Dual write" in body
    assert "Mesh" in body


async def test_the_dual_write_panel_counts_what_is_actually_stored(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        await catalog.create(session, SAMPLE)

    async with _client() as client:
        body = (await client.get("/debug")).text
    assert "SQLite rows" in body
    assert "Qdrant points" in body
    assert "YES" in body


async def test_the_glass_box_is_reachable_from_every_page():
    async with _client() as client:
        body = (await client.get("/")).text
    assert 'href="/debug"' in body
