import pytest
import schemathesis
from httpx import ASGITransport, AsyncClient

from src.main import app

schema = schemathesis.openapi.from_asgi("/openapi.json", app)

BEHIND_SIGN_IN = (
    "/shop",
    "/search",
    "/profile",
    "/footprint",
    "/recommendations",
    "/welcome",
    "/category/cookware",
    "/product/1",
    "/cart",
    "/orders",
    "/orders/1",
    "/shelf",
)

public = (
    schema.include(method="GET")
    .exclude(path_regex=r"^/(admin|api)")
    .exclude(path_regex=r"^/(signup|login|logout)$")
    .exclude(
        path_regex=(
            r"^/(shop|search|profile|footprint|recommendations|welcome|category|product"
            r"|cart|orders|shelf)"
        )
    )
)


@public.parametrize()
def test_public_routes_match_their_contract(case):
    case.call_and_validate()


@pytest.mark.parametrize("path", BEHIND_SIGN_IN)
async def test_a_guarded_route_sends_a_signed_out_visitor_to_sign_in(path):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://hardy.test"
    ) as client:
        response = await client.get(path)
    assert response.status_code == 303
    assert response.headers["location"] == f"/login?next={path}"


@pytest.mark.parametrize("path", BEHIND_SIGN_IN)
async def test_a_guarded_route_serves_html_once_signed_in(shopper, path):
    response = await shopper.get(path, follow_redirects=True)
    assert response.status_code in (200, 404)
    assert response.headers["content-type"].startswith("text/html")
