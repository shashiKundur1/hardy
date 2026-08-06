from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from src.catalog import service as catalog
from src.catalog.schemas import ProductWrite
from src.constants import MAX_SQLITE_INTEGER
from src.database import Base, session_factory
from src.main import app
from src.models import TriggerDecision

SAMPLE = ProductWrite(
    title="Regression skillet",
    brand="Testworks",
    description="A pan kept around so old defects cannot come back.",
    category="cookware",
    price=Decimal("4200.00"),
    expected_life_years=40,
)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


async def test_counts_by_category_returns_a_dict_not_a_result_proxy(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        await catalog.create(session, SAMPLE)
        counts = await catalog.counts_by_category(session)
    assert counts == {"cookware": 1}


async def test_a_product_id_beyond_sqlites_range_is_rejected_not_a_server_error():
    async with _client() as client:
        response = await client.get(f"/product/{MAX_SQLITE_INTEGER + 1}")
    assert response.status_code == 422, response.text


async def test_storefront_pages_are_served_as_html():
    async with _client() as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


async def test_a_missing_product_renders_a_page_not_a_json_error():
    async with _client() as client:
        response = await client.get("/product/999999")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")


@pytest.mark.parametrize("model", [TriggerDecision])
async def test_every_registered_model_gets_a_table(model):
    async with session_factory() as session:
        await session.execute(model.__table__.select().limit(1))


def test_the_schema_covers_every_registered_table():
    registered = {table.name for table in Base.metadata.sorted_tables}
    assert "trigger_decisions" in registered
