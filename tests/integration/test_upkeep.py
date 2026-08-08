from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from src.catalog import service as catalog
from src.catalog.schemas import ProductWrite
from src.constants import CATEGORIES, Wear
from src.database import session_factory, utcnow
from src.main import app
from src.orders import service
from src.orders.constants import CARE_INTERVALS

PASSWORD = "upkeep-password"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


def _product() -> ProductWrite:
    return ProductWrite(
        title="Upkeep fixture skillet",
        brand="Testworks",
        description="A pan bought so its care schedule and warranty can be tracked.",
        category="cookware",
        price=Decimal("6000.00"),
        expected_life_years=30,
        warranty="Lifetime against manufacturing defects",
    )


@pytest.fixture(autouse=True)
def _offline(offline_mesh):
    offline_mesh()


@pytest.fixture
async def bought():
    async with session_factory() as session:
        product_id = (await catalog.create(session, _product())).id
    async with _client() as client:
        await client.post("/signup", data={"email": "owner@hardy.test", "password": PASSWORD})
        await client.post("/welcome/skip")
        await client.post("/cart/add", data={"product_id": product_id})
        await client.post("/checkout")
        yield client, product_id


@pytest.mark.parametrize("category", CATEGORIES)
def test_every_category_has_a_care_interval_and_a_real_instruction(category):
    months, task = CARE_INTERVALS[category]
    assert months > 0
    assert len(task) > 20


def test_nothing_is_due_the_day_a_thing_arrives():
    care = service.care_for("cookware", utcnow().date())
    assert care["services_due"] == 0
    assert care["due_in_days"] > 0


def test_a_passed_interval_is_counted_as_a_service_that_was_due():
    months, _ = CARE_INTERVALS["cookware"]
    owned_since = utcnow().date() - timedelta(days=int(months * 30.44) + 1)
    care = service.care_for("cookware", owned_since)
    assert care["services_due"] == 1
    assert 0 < care["due_in_days"] <= round(months * 30.44)


def test_an_unknown_category_still_gets_a_schedule_rather_than_raising():
    care = service.care_for("not-a-category", date(2020, 1, 1))
    assert care["months"] > 0
    assert care["task"]


async def test_the_warranty_is_kept_as_it_stood_on_the_day_of_sale(bought):
    client, _ = bought
    response = await client.get("/shelf")
    assert "Lifetime against manufacturing defects" in response.text


async def test_the_shelf_shows_when_the_next_care_is_due(bought):
    client, _ = bought
    response = await client.get("/shelf")
    assert "Next in" in response.text
    assert "every 6 months" in response.text
    assert "Re-season the surface" in response.text


async def test_an_owner_can_record_how_a_thing_is_holding_up(bought):
    client, product_id = bought
    await client.post(
        "/shelf/report",
        data={"product_id": product_id, "verdict": Wear.WORN, "note": "enamel chipped"},
    )
    response = await client.get("/shelf")
    assert "You said: Wearing, but working" in response.text
    assert "enamel chipped" in response.text


async def test_the_latest_report_is_the_one_that_stands(bought):
    client, product_id = bought
    for verdict in (Wear.HOLDING, Wear.FAILED):
        await client.post("/shelf/report", data={"product_id": product_id, "verdict": verdict})
    async with session_factory() as session:
        latest = await service.reports_for(session, 1)
    assert latest[product_id].verdict == Wear.FAILED


async def test_someone_who_does_not_own_it_cannot_report_on_it(bought):
    _, product_id = bought
    async with _client() as stranger:
        await stranger.post("/signup", data={"email": "stranger@hardy.test", "password": PASSWORD})
        response = await stranger.post(
            "/shelf/report", data={"product_id": product_id, "verdict": Wear.FAILED}
        )
    assert response.status_code == 403


async def test_a_verdict_outside_the_vocabulary_is_refused(bought):
    client, product_id = bought
    response = await client.post(
        "/shelf/report", data={"product_id": product_id, "verdict": "brilliant"}
    )
    assert response.status_code == 422
