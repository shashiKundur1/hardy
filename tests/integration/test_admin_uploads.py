from httpx import ASGITransport, AsyncClient

from src.auth.models import User
from src.auth.service import hash_password
from src.catalog.constants import MAX_UPLOAD_BYTES
from src.config import settings
from src.constants import Role
from src.database import session_factory
from src.main import app

PASSWORD = "upload-test-password"

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 64
SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://hardy.test")


async def _admin(email: str = "uploader@hardy.test") -> User:
    async with session_factory() as session:
        person = User(email=email, password_hash=hash_password(PASSWORD), role=Role.ADMIN)
        session.add(person)
        await session.commit()
        await session.refresh(person)
        return person


async def _signed_in(client: AsyncClient, email: str) -> None:
    await client.post("/login", data={"email": email, "password": PASSWORD})


async def test_a_png_upload_is_stored_and_addressable():
    person = await _admin()
    async with _client() as client:
        await _signed_in(client, person.email)
        response = await client.post(
            "/api/admin/uploads", files={"file": ("shot.png", PNG, "image/png")}
        )
    assert response.status_code == 201
    address = response.json()["image_url"]
    assert address.startswith("/media/")
    assert address.endswith(".png")
    assert (settings.media_dir / address.removeprefix("/media/")).read_bytes() == PNG


async def test_the_stored_name_never_comes_from_the_client():
    person = await _admin("renamer@hardy.test")
    async with _client() as client:
        await _signed_in(client, person.email)
        response = await client.post(
            "/api/admin/uploads",
            files={"file": ("../../etc/passwd.png", PNG, "image/png")},
        )
    assert response.status_code == 201
    address = response.json()["image_url"]
    assert "passwd" not in address
    assert ".." not in address
    assert address.count("/") == 2


async def test_a_disguised_script_is_refused_whatever_it_claims_to_be():
    person = await _admin("liar@hardy.test")
    async with _client() as client:
        await _signed_in(client, person.email)
        response = await client.post(
            "/api/admin/uploads", files={"file": ("harmless.png", SVG, "image/png")}
        )
    assert response.status_code == 415
    assert not list(settings.media_dir.glob("*.svg"))


async def test_an_oversized_image_is_refused_and_leaves_nothing_behind():
    person = await _admin("hoarder@hardy.test")
    before = set(settings.media_dir.glob("*"))
    async with _client() as client:
        await _signed_in(client, person.email)
        response = await client.post(
            "/api/admin/uploads",
            files={"file": ("huge.png", PNG + b"\x00" * MAX_UPLOAD_BYTES, "image/png")},
        )
    assert response.status_code == 413
    assert set(settings.media_dir.glob("*")) == before


async def test_jpeg_and_webp_are_both_accepted():
    person = await _admin("formats@hardy.test")
    async with _client() as client:
        await _signed_in(client, person.email)
        jpeg = await client.post(
            "/api/admin/uploads", files={"file": ("a.bin", JPEG, "application/octet-stream")}
        )
        webp = await client.post(
            "/api/admin/uploads", files={"file": ("b.bin", WEBP, "application/octet-stream")}
        )
    assert jpeg.json()["image_url"].endswith(".jpg")
    assert webp.json()["image_url"].endswith(".webp")


async def test_a_shopper_cannot_upload():
    async with session_factory() as session:
        session.add(User(email="shopper@hardy.test", password_hash=hash_password(PASSWORD)))
        await session.commit()

    async with _client() as client:
        await _signed_in(client, "shopper@hardy.test")
        response = await client.post(
            "/api/admin/uploads", files={"file": ("shot.png", PNG, "image/png")}
        )
    assert response.status_code in (401, 403)
