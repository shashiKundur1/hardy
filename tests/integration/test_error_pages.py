import pytest
from httpx import ASGITransport, AsyncClient

from src.constants import MAX_SQLITE_INTEGER
from src.exceptions import FAULTS, fault_for
from src.main import app

BLAME_WORDS = ("invalid", "illegal", "incorrect", "oops", "sorry", "whoops")


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


@pytest.mark.parametrize("status_code", sorted(FAULTS))
def test_every_fault_says_what_happened_and_offers_a_way_on(status_code):
    fault = fault_for(status_code)
    assert fault["headline"]
    assert len(fault["explanation"]) > 40
    assert fault["actions"], "an error page with no way out is a dead end"
    assert all("label" in action and "href" in action for action in fault["actions"])


@pytest.mark.parametrize("status_code", sorted(FAULTS))
def test_no_fault_blames_the_reader_or_makes_a_joke(status_code):
    fault = fault_for(status_code)
    prose = f"{fault['headline']} {fault['explanation']}".lower()
    found = [word for word in BLAME_WORDS if word in prose]
    assert not found, f"{status_code} uses {found}"


def test_an_unmapped_status_still_gets_a_real_page():
    fault = fault_for(418)
    assert fault["headline"]
    assert fault["actions"]


async def test_a_missing_page_returns_404_and_not_a_soft_200():
    async with _client() as client:
        response = await client.get("/no-such-page")
    assert response.status_code == 404


async def test_a_missing_product_renders_the_designed_page():
    async with _client() as client:
        response = await client.get("/product/999999")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")
    assert "Nothing lives at this address" in response.text
    assert "Back to the storefront" in response.text


async def test_an_unreadable_product_id_renders_the_designed_page():
    async with _client() as client:
        response = await client.get(f"/product/{MAX_SQLITE_INTEGER + 1}")
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("text/html")
    assert "could not be read" in response.text


async def test_an_unauthenticated_api_call_gets_json_not_a_redirect_to_a_page():
    async with _client() as client:
        response = await client.get("/api/admin/consistency")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/json")


async def test_a_missing_category_renders_the_designed_page():
    async with _client() as client:
        response = await client.get("/category/not-a-category")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")
