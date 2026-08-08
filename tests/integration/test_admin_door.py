from httpx import ASGITransport, AsyncClient

from src.auth.models import User
from src.auth.service import hash_password
from src.constants import Role
from src.database import session_factory
from src.main import app

PASSWORD = "admin-door-password"


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


async def _person(email: str, role: Role) -> None:
    async with session_factory() as session:
        session.add(User(email=email, password_hash=hash_password(PASSWORD), role=role))
        await session.commit()


async def test_the_admin_door_is_its_own_route():
    async with _client() as client:
        response = await client.get("/admin/login")
    assert response.status_code == 200
    assert "Administrator sign in" in response.text


async def test_a_signed_out_visitor_to_admin_is_sent_to_the_admin_door():
    async with _client() as client:
        response = await client.get("/admin")
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


async def test_an_admin_signing_in_at_the_admin_door_reaches_the_catalog():
    await _person("boss@hardy.test", Role.ADMIN)
    async with _client() as client:
        response = await client.post(
            "/admin/login", data={"email": "boss@hardy.test", "password": PASSWORD}
        )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin"


async def test_a_shopper_at_the_admin_door_is_refused_with_a_page_not_a_loop():
    await _person("shopper@hardy.test", Role.USER)
    async with _client() as client:
        response = await client.post(
            "/admin/login", data={"email": "shopper@hardy.test", "password": PASSWORD}
        )
    assert response.status_code == 403
    assert response.headers["content-type"].startswith("text/html")
    assert "administrators" in response.text.lower()


async def test_a_signed_in_shopper_reaching_admin_gets_the_designed_403():
    await _person("browser@hardy.test", Role.USER)
    async with _client() as client:
        await client.post("/login", data={"email": "browser@hardy.test", "password": PASSWORD})
        response = await client.get("/admin")
    assert response.status_code == 403
    assert response.headers["content-type"].startswith("text/html")


async def test_the_ordinary_door_does_not_hand_out_admin_rights():
    await _person("boss2@hardy.test", Role.ADMIN)
    async with _client() as client:
        response = await client.post(
            "/login", data={"email": "boss2@hardy.test", "password": PASSWORD}
        )
    assert response.headers["location"] == "/welcome"


async def test_an_admin_session_is_named_on_the_page():
    await _person("boss3@hardy.test", Role.ADMIN)
    async with _client() as client:
        await client.post("/admin/login", data={"email": "boss3@hardy.test", "password": PASSWORD})
        response = await client.get("/admin")
    assert "Administrator" in response.text
