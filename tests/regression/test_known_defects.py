from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from src.catalog import service as catalog
from src.catalog.schemas import ProductWrite
from src.config import settings
from src.constants import MAX_SQLITE_INTEGER, RESPONSE_GUARDS
from src.database import Base, session_factory
from src.integrations import vectorstore
from src.main import app, lifespan
from src.models import TriggerDecision
from src.recommendations import schedule

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


async def test_a_product_id_beyond_sqlites_range_is_rejected_not_a_server_error(shopper):
    response = await shopper.get(f"/product/{MAX_SQLITE_INTEGER + 1}")
    assert response.status_code == 422, response.text


async def test_storefront_pages_are_served_as_html():
    async with _client() as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


async def test_a_missing_product_renders_a_page_not_a_json_error(shopper):
    response = await shopper.get("/product/999999")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")


@pytest.mark.parametrize("model", [TriggerDecision])
async def test_every_registered_model_gets_a_table(model):
    async with session_factory() as session:
        await session.execute(model.__table__.select().limit(1))


def test_the_schema_covers_every_registered_table():
    registered = {table.name for table in Base.metadata.sorted_tables}
    assert "trigger_decisions" in registered


async def test_the_app_boots_when_the_vector_store_is_unreachable(monkeypatch):
    async def refuse():
        raise ConnectionError("all connection attempts failed")

    monkeypatch.setattr(vectorstore, "ensure_collection", refuse)
    async with lifespan(app):
        pass


async def test_the_glass_box_renders_when_the_vector_store_is_unreachable(monkeypatch):
    async def refuse():
        raise ConnectionError("all connection attempts failed")

    monkeypatch.setattr(vectorstore, "point_ids", refuse)
    async with _client() as client:
        response = await client.get("/debug")
    assert response.status_code == 200, response.text


def test_a_worker_process_does_not_start_a_second_copy_of_the_scheduler(monkeypatch):
    monkeypatch.setattr(settings, "scheduler_enabled", False)
    assert schedule.start_if_enabled() is None


def test_the_digest_is_registered_exactly_once():
    assert [job.id for job in schedule.build().get_jobs()] == [schedule.DIGEST_JOB_ID]


async def test_the_health_check_answers_even_with_no_vector_store(monkeypatch):
    async def refuse():
        raise ConnectionError("all connection attempts failed")

    monkeypatch.setattr(vectorstore, "count", refuse)
    async with _client() as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": True, "vector_store": False}


async def test_consistency_reports_an_unreachable_vector_store_rather_than_raising(monkeypatch):
    async def refuse():
        raise ConnectionError("all connection attempts failed")

    monkeypatch.setattr(vectorstore, "point_ids", refuse)
    async with session_factory() as session:
        state = await catalog.consistency(session)
    assert state["vector_store_reachable"] is False
    assert state["in_sync"] is False


async def test_internal_brand_documents_are_not_served_over_http():
    async with _client() as client:
        for path in ("/brand/BRAND.md", "/brand/cvd.py", "/brand/research/kings-audit.md"):
            assert (await client.get(path)).status_code == 404


async def test_the_design_tokens_are_still_served():
    async with _client() as client:
        response = await client.get("/brand/tokens.css")
    assert response.status_code == 200
    assert "--amber" in response.text


async def test_every_response_carries_the_security_guards():
    async with _client() as client:
        response = await client.get("/")
    for name, value in RESPONSE_GUARDS.items():
        assert response.headers[name] == value
