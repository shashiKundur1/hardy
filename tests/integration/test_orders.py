from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.catalog import service as catalog
from src.catalog.schemas import ProductWrite
from src.constants import EventType
from src.database import session_factory
from src.events.models import Event
from src.main import app
from src.orders import service
from src.orders.constants import MAX_CART_LINES, MAX_LINE_QUANTITY
from src.orders.exceptions import CartFull

PASSWORD = "orders-password"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


def _product(index: int) -> ProductWrite:
    return ProductWrite(
        title=f"Order fixture {index}",
        brand="Testworks",
        description="A product that exists so a purchase can be a real thing that happened.",
        category="cookware",
        price=Decimal("6000.00"),
        expected_life_years=30,
    )


@pytest.fixture(autouse=True)
def _offline(offline_mesh):
    offline_mesh()


async def _seeded(count: int = 1) -> list[int]:
    async with session_factory() as session:
        return [(await catalog.create(session, _product(i))).id for i in range(1, count + 1)]


async def _shopper(client: AsyncClient, email: str = "buyer@hardy.test") -> None:
    await client.post("/signup", data={"email": email, "password": PASSWORD})
    await client.post("/welcome/skip")


def test_a_basket_never_grows_past_its_ceiling():
    basket = dict.fromkeys(range(1, MAX_CART_LINES + 1), 1)
    with pytest.raises(CartFull):
        service.add(basket, 999, 1)


def test_a_quantity_is_capped_rather_than_trusted():
    assert service.add({}, 1, 999)[1] == MAX_LINE_QUANTITY


def test_a_tampered_basket_in_the_session_is_discarded_not_trusted():
    assert service.normalise({"1": 2, "nonsense": "x", "-4": 3, "5": 0}) == {1: 2}
    assert service.normalise("not a basket at all") == {}


async def test_adding_and_buying_makes_an_order_that_happened():
    [product_id] = await _seeded()
    async with _client() as client:
        await _shopper(client)
        await client.post("/cart/add", data={"product_id": product_id, "back": "/cart"})
        placed = await client.post("/checkout")
    assert placed.status_code == 303
    assert placed.headers["location"].startswith("/orders/")
    async with session_factory() as session:
        orders = await service.history(session, 1)
    assert len(orders) == 1
    assert orders[0].total == Decimal("6000.00")


async def test_an_order_keeps_what_the_product_claimed_on_the_day():
    [product_id] = await _seeded()
    async with _client() as client:
        await _shopper(client)
        await client.post("/cart/add", data={"product_id": product_id})
        await client.post("/checkout")
    async with session_factory() as session:
        renamed = _product(1).model_copy(update={"title": "Renamed after the sale"})
        await catalog.replace(session, product_id, renamed)
    async with session_factory() as session:
        assert (await catalog.by_id(session, product_id)).title == "Renamed after the sale"
        orders = await service.history(session, 1)
    assert orders[0].lines[0].title == "Order fixture 1"


async def test_the_basket_empties_once_the_order_is_placed():
    [product_id] = await _seeded()
    async with _client() as client:
        await _shopper(client)
        await client.post("/cart/add", data={"product_id": product_id})
        await client.post("/checkout")
        response = await client.get("/cart")
    assert "The basket is empty" in response.text


async def test_buying_nothing_is_refused_rather_than_making_an_empty_order():
    async with _client() as client:
        await _shopper(client)
        response = await client.post("/checkout")
    assert response.status_code == 409


async def test_a_purchase_is_recorded_as_behaviour_the_agent_can_read():
    [product_id] = await _seeded()
    async with _client() as client:
        await _shopper(client)
        await client.post("/cart/add", data={"product_id": product_id})
        await client.post("/checkout")
    async with session_factory() as session:
        kinds = list(await session.scalars(select(Event.type)))
    assert EventType.ADD_TO_CART in kinds
    assert EventType.PURCHASE in kinds


async def test_a_basket_cannot_hold_a_product_that_does_not_exist():
    async with _client() as client:
        await _shopper(client)
        response = await client.post("/cart/add", data={"product_id": 999999})
    assert response.status_code == 404


async def test_the_shelf_shows_how_far_through_its_claimed_life_a_thing_has_got():
    [product_id] = await _seeded()
    async with _client() as client:
        await _shopper(client)
        await client.post("/cart/add", data={"product_id": product_id})
        await client.post("/checkout")
        response = await client.get("/shelf")
    assert "of 30 years claimed" in response.text
    async with session_factory() as session:
        owned = await service.shelf(session, 1)
    assert owned[0]["life_used"] < 0.01
    assert owned[0]["quantity"] == 1


async def test_one_shopper_cannot_read_another_shoppers_order():
    [product_id] = await _seeded()
    async with _client() as buyer:
        await _shopper(buyer, "mine@hardy.test")
        await buyer.post("/cart/add", data={"product_id": product_id})
        placed = await buyer.post("/checkout")
        path = placed.headers["location"]
    async with _client() as stranger:
        await _shopper(stranger, "theirs@hardy.test")
        response = await stranger.get(path)
    assert response.status_code == 404


async def test_the_basket_totals_by_the_year_not_only_the_till():
    ids = await _seeded(2)
    async with session_factory() as session:
        lines = await service.contents(session, {ids[0]: 1, ids[1]: 2})
    assert service.total_of(lines) == Decimal("18000.00")
    assert service.yearly_of(lines) == Decimal("600.00")
