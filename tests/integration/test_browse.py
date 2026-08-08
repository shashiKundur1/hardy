from datetime import date
from decimal import Decimal

import pytest

from src.catalog import service as catalog
from src.catalog.constants import PAGE_SIZE
from src.catalog.schemas import BrowseQuery, ProductWrite
from src.constants import Ownership, SortOrder
from src.database import session_factory


def _product(index: int, **overrides) -> ProductWrite:
    fields = {
        "title": f"Browse fixture {index}",
        "brand": "Testworks",
        "description": "A product that exists so browsing has something to sort.",
        "category": "cookware",
        "price": Decimal(f"{1000 * index}.00"),
        "expected_life_years": index,
    }
    return ProductWrite(**(fields | overrides))


async def _seeded(count: int, **overrides) -> None:
    async with session_factory() as session:
        for index in range(1, count + 1):
            await catalog.create(session, _product(index, **overrides))


@pytest.fixture(autouse=True)
def _no_network(offline_mesh):
    offline_mesh()


async def test_a_page_never_returns_more_than_the_page_size():
    await _seeded(PAGE_SIZE + 5)
    async with session_factory() as session:
        products, total = await catalog.browse(session, "cookware", BrowseQuery())
    assert total == PAGE_SIZE + 5
    assert len(products) == PAGE_SIZE


async def test_the_last_page_holds_the_remainder_and_stops():
    await _seeded(PAGE_SIZE + 3)
    async with session_factory() as session:
        products, _ = await catalog.browse(session, "cookware", BrowseQuery(page=2))
        beyond, _ = await catalog.browse(session, "cookware", BrowseQuery(page=3))
    assert len(products) == 3
    assert beyond == []


async def test_sorting_by_cost_per_year_leads_with_the_cheapest_to_keep():
    await _seeded(6)
    async with session_factory() as session:
        products, _ = await catalog.browse(session, "cookware", BrowseQuery(sort=SortOrder.RATE))
    rates = [product.cost_per_year for product in products]
    assert rates == sorted(rates)


async def test_sorting_by_life_leads_with_the_longest_lived():
    await _seeded(6)
    async with session_factory() as session:
        products, _ = await catalog.browse(session, "cookware", BrowseQuery())
    lives = [product.expected_life_years for product in products]
    assert lives == sorted(lives, reverse=True)


async def test_the_sourced_filter_keeps_only_products_with_a_record():
    await _seeded(3)
    await _seeded(
        2,
        ownership_type=Ownership.FAMILY,
        ownership_note="Held by the founding family since 1898.",
        evidence_source="https://example.test/history",
        ownership_since=date(1898, 1, 1),
    )
    async with session_factory() as session:
        products, total = await catalog.browse(session, "cookware", BrowseQuery(sourced=True))
    assert total == 2
    assert all(product.evidence_source for product in products)


async def test_the_life_floor_excludes_anything_shorter_lived():
    await _seeded(20)
    async with session_factory() as session:
        products, total = await catalog.browse(session, "cookware", BrowseQuery(min_life=10))
    assert total == 11
    assert all(product.expected_life_years >= 10 for product in products)


async def test_the_rate_ceiling_excludes_anything_dearer_to_keep():
    await _seeded(8)
    async with session_factory() as session:
        products, _ = await catalog.browse(session, "cookware", BrowseQuery(max_rate=1000))
    assert products
    assert all(product.cost_per_year <= 1000 for product in products)


async def test_filters_compose_rather_than_replace_one_another():
    await _seeded(5)
    await _seeded(
        5,
        ownership_type=Ownership.FAMILY,
        ownership_note="Held by the founding family since 1898.",
        evidence_source="https://example.test/history",
        ownership_since=date(1898, 1, 1),
    )
    async with session_factory() as session:
        _, total = await catalog.browse(session, "cookware", BrowseQuery(sourced=True, min_life=3))
    assert total == 3


async def test_a_filtered_page_that_matches_nothing_is_empty_not_an_error():
    await _seeded(3)
    async with session_factory() as session:
        products, total = await catalog.browse(session, "cookware", BrowseQuery(min_life=200))
    assert products == []
    assert total == 0


def test_a_link_drops_defaults_and_keeps_what_changed():
    assert BrowseQuery().link() == ""
    assert BrowseQuery().link(page=2) == "?page=2"
    assert "sourced=True" in BrowseQuery(sourced=True).link()
    assert "page=" not in BrowseQuery(sourced=True).link()


def test_a_page_beyond_the_ceiling_is_refused():
    with pytest.raises(ValueError):
        BrowseQuery(page=10_000)
