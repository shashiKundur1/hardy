import json
from decimal import Decimal

import pytest

from src.catalog import service as catalog
from src.catalog.constants import CATEGORY_ANGLES
from src.catalog.schemas import ProductWrite
from src.constants import CATEGORIES
from src.database import session_factory


def _product(category: str = "cookware") -> ProductWrite:
    return ProductWrite(
        title="Gallery fixture pan",
        brand="Testworks",
        description="A pan that exists so its angles can be inspected.",
        category=category,
        price=Decimal("4000.00"),
        expected_life_years=20,
    )


@pytest.fixture(autouse=True)
def _offline(offline_mesh):
    offline_mesh()


@pytest.mark.parametrize("category", CATEGORIES)
def test_every_category_names_the_angles_that_matter_for_it(category):
    angles = CATEGORY_ANGLES[category]
    assert len(angles) >= 4
    assert all(len(angle) > 8 for angle in angles)


async def test_a_product_with_one_image_still_has_a_hero():
    async with session_factory() as session:
        product = await catalog.create(session, _product())
        product.image_url = "/static/img/products/1.webp"
        shots = catalog.gallery_for(product)
    assert len(shots) == 1
    assert shots[0]["hero"] is True


async def test_a_product_with_no_image_gets_an_empty_gallery_not_a_broken_one():
    async with session_factory() as session:
        product = await catalog.create(session, _product())
        assert catalog.gallery_for(product) == []


async def test_angles_carry_alt_text_that_says_what_the_angle_shows():
    async with session_factory() as session:
        product = await catalog.create(session, _product())
        product.images = json.dumps([f"/static/img/products/1-{n}.webp" for n in range(4)])
        shots = catalog.gallery_for(product)
    assert len(shots) == 4
    assert all(shot["alt"].startswith("Gallery fixture pan — ") for shot in shots)
    assert "the handle join and its rivets" in shots[2]["alt"]
    assert len({shot["alt"] for shot in shots}) == 4


async def test_alt_text_is_never_the_words_product_image():
    async with session_factory() as session:
        product = await catalog.create(session, _product("footwear"))
        product.images = json.dumps(["/a.webp", "/b.webp"])
        shots = catalog.gallery_for(product)
    assert all("product image" not in shot["alt"].lower() for shot in shots)
    assert "the welt, where the sole is joined" in shots[1]["alt"]


async def test_a_corrupt_images_column_falls_back_rather_than_raising():
    async with session_factory() as session:
        product = await catalog.create(session, _product())
        product.images = "{not json at all"
        product.image_url = "/static/img/products/9.webp"
        shots = catalog.gallery_for(product)
    assert [shot["url"] for shot in shots] == ["/static/img/products/9.webp"]


async def test_the_strip_only_appears_when_there_is_more_than_one_angle(shopper):
    async with session_factory() as session:
        product = await catalog.create(session, _product())
        product.image_url = "/static/img/products/1.webp"
        await session.commit()
        product_id = product.id
    single = await shopper.get(f"/product/{product_id}")
    assert "gallery__strip" not in single.text
    assert "gallery__hero" in single.text

    async with session_factory() as session:
        stored = await catalog.by_id(session, product_id)
        stored.images = json.dumps(["/a.webp", "/b.webp", "/c.webp"])
        await session.commit()
    several = await shopper.get(f"/product/{product_id}")
    assert several.text.count("gallery__thumb") >= 3
    assert 'aria-pressed="true"' in several.text
