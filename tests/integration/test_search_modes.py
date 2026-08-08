from decimal import Decimal

import pytest

from src.catalog import service as catalog
from src.catalog.constants import MEANING_READ_TOP
from src.catalog.schemas import ProductWrite
from src.database import session_factory


def _product(index: int, category: str, title: str) -> ProductWrite:
    return ProductWrite(
        title=title,
        brand="Testworks",
        description="A durable thing kept around so search has something to find.",
        category=category,
        price=Decimal(f"{index}000.00"),
        expected_life_years=index * 5,
    )


@pytest.fixture(autouse=True)
def _offline(offline_mesh):
    offline_mesh()


async def _seeded() -> None:
    async with session_factory() as session:
        await catalog.create(session, _product(1, "cookware", "Cast iron skillet"))
        await catalog.create(session, _product(2, "cookware", "Enamelled dutch oven"))
        await catalog.create(session, _product(3, "tools", "Ratchet set"))


async def test_word_search_matches_what_was_typed():
    await _seeded()
    async with session_factory() as session:
        found = await catalog.search(session, "skillet", 20)
    assert [product.title for product in found] == ["Cast iron skillet"]


async def test_word_search_finds_nothing_for_a_description_of_the_job():
    await _seeded()
    async with session_factory() as session:
        found = await catalog.search(session, "something to fry in", 20)
    assert found == []


async def test_meaning_search_returns_hits_with_their_scores():
    await _seeded()
    async with session_factory() as session:
        reading = await catalog.semantic_search(session, "something to fry in", 10)
    assert reading["available"] is True
    assert reading["hits"]
    first = reading["hits"][0]
    assert {"product", "meaning", "durability", "score"} == set(first)
    assert 0 <= first["durability"] <= 1


async def test_meaning_search_only_reports_the_categories_it_actually_leaned_on():
    await _seeded()
    async with session_factory() as session:
        reading = await catalog.semantic_search(session, "a pan for life", 10)
    assert len(reading["categories"]) <= MEANING_READ_TOP


async def test_meaning_search_degrades_to_words_when_the_vector_store_is_down(monkeypatch):
    await _seeded()

    async def refuse(*args, **kwargs):
        raise ConnectionError("all connection attempts failed")

    monkeypatch.setattr(catalog, "hybrid", refuse)
    async with session_factory() as session:
        reading = await catalog.semantic_search(session, "anything", 10)
    assert reading["available"] is False
    assert reading["hits"] == []


async def test_the_page_offers_both_buttons(shopper):
    response = await shopper.get("/search")
    assert 'value="words"' in response.text
    assert 'value="meaning"' in response.text
    assert "AI search" in response.text


async def test_the_page_says_which_mode_it_used(shopper):
    await _seeded()
    words = await shopper.get("/search?q=skillet&mode=words")
    meaning = await shopper.get("/search?q=skillet&mode=meaning")
    assert "Matching the words" in words.text
    assert "Reading what you meant" in meaning.text


async def test_meaning_results_show_why_each_one_was_returned(shopper):
    await _seeded()
    response = await shopper.get("/search?q=a+pan+for+life&mode=meaning")
    assert "found__why" in response.text
    for label in ("Meaning", "Durability", "Ranked"):
        assert f"<dt>{label}</dt>" in response.text


async def test_an_unknown_mode_is_refused_rather_than_guessed(shopper):
    response = await shopper.get("/search?q=pan&mode=telepathy")
    assert response.status_code == 422


async def test_an_empty_query_asks_for_one_instead_of_searching(shopper):
    response = await shopper.get("/search?mode=meaning")
    assert response.status_code == 200
    assert "found__why" not in response.text
