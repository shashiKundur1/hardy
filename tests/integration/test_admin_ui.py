from decimal import Decimal

from httpx import ASGITransport, AsyncClient

from src.auth.models import User
from src.auth.service import hash_password
from src.catalog import service as catalog
from src.catalog.schemas import ProductWrite
from src.constants import Ownership, Role
from src.database import session_factory
from src.integrations import vectorstore
from src.main import app

PASSWORD = "admin-test-password"

SAMPLE = ProductWrite(
    title="Admin test skillet",
    brand="Testworks",
    description="A pan that exists to prove the admin interface writes both stores.",
    category="cookware",
    price=Decimal("4200.00"),
    expected_life_years=40,
)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


async def _admin(session) -> User:
    person = User(email="boss@hardy.test", password_hash=hash_password(PASSWORD), role=Role.ADMIN)
    session.add(person)
    await session.commit()
    await session.refresh(person)
    return person


async def _signed_in(client: AsyncClient, email: str) -> None:
    await client.post("/login", data={"email": email, "password": PASSWORD})


def _form(product) -> dict:
    return {
        "title": product.title,
        "brand": product.brand,
        "description": product.description,
        "category": product.category,
        "price": str(product.price),
        "expected_life_years": str(product.expected_life_years),
        "ownership_type": str(product.ownership_type),
        "ownership_note": "",
        "evidence_source": "",
        "repairability_score": "",
        "parts_until": "",
        "warranty": "",
        "image_url": "",
    }


async def test_the_catalog_table_lists_products_for_an_admin(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        person = await _admin(session)
        await catalog.create(session, SAMPLE)

    async with _client() as client:
        await _signed_in(client, person.email)
        body = (await client.get("/admin")).text
    assert "Admin test skillet" in body
    assert "In sync" in body
    assert "synced" in body


async def test_a_non_admin_never_reaches_the_catalog_table(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        person = User(email="nobody@hardy.test", password_hash=hash_password(PASSWORD))
        session.add(person)
        await session.commit()

    async with _client() as client:
        await _signed_in(client, "nobody@hardy.test")
        response = await client.get("/admin")
    assert response.status_code in (303, 403)
    assert "Admin test skillet" not in response.text


async def test_saving_the_form_rewrites_the_row_and_the_vector(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        person = await _admin(session)
        product = await catalog.create(session, SAMPLE)
        product_id = product.id
        payload = _form(product)

    payload["title"] = "Renamed by the admin form"
    payload["expected_life_years"] = "12"

    async with _client() as client:
        await _signed_in(client, person.email)
        response = await client.post(f"/admin/products/{product_id}", data=payload)
    assert response.status_code == 303

    async with session_factory() as session:
        saved = await catalog.by_id(session, product_id)
        assert saved.title == "Renamed by the admin form"
        assert saved.expected_life_years == 12
        assert (await catalog.consistency(session))["in_sync"] is True
    payload_in_qdrant = await vectorstore.payload_of(product_id)
    assert payload_in_qdrant["title"] == "Renamed by the admin form"
    assert payload_in_qdrant["expected_life_years"] == 12


async def test_the_form_refuses_an_ownership_claim_with_no_source(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        person = await _admin(session)
        product = await catalog.create(session, SAMPLE)
        product_id = product.id
        payload = _form(product)

    payload["ownership_type"] = Ownership.FAMILY.value

    async with _client() as client:
        await _signed_in(client, person.email)
        response = await client.post(f"/admin/products/{product_id}", data=payload)
    assert response.status_code == 422

    async with session_factory() as session:
        assert (await catalog.by_id(session, product_id)).ownership_type == Ownership.UNKNOWN


async def test_deleting_from_the_table_clears_both_stores(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        person = await _admin(session)
        product = await catalog.create(session, SAMPLE)
        product_id = product.id

    async with _client() as client:
        await _signed_in(client, person.email)
        response = await client.post(f"/admin/products/{product_id}/delete")
    assert response.status_code == 303

    async with session_factory() as session:
        assert await catalog.by_id(session, product_id) is None
        assert (await catalog.consistency(session))["in_sync"] is True
    assert await vectorstore.payload_of(product_id) is None
