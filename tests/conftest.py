import os
import tempfile
from pathlib import Path

WORKSPACE = Path(tempfile.mkdtemp(prefix="hardy-tests-"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{WORKSPACE}/hardy.db"
os.environ["QDRANT_PATH"] = str(WORKSPACE / "qdrant")
os.environ["QDRANT_URL"] = ""
os.environ.setdefault("SESSION_SECRET", "hardy-test-secret")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from src.database import Base, create_schema, engine, session_factory
from src.integrations import mesh, vectorstore
from src.main import app
from tests.fakes import OfflineMesh

LAYERS = ("unit", "integration", "regression", "contract", "live")
SHOPPER_EMAIL = "shopper@hardy.test"
SHOPPER_PASSWORD = "keep-it-long-1"


def pytest_collection_modifyitems(items):
    for item in items:
        layer = item.path.parent.name
        if layer in LAYERS:
            item.add_marker(getattr(pytest.mark, layer))


@pytest.fixture(autouse=True)
async def clean_state(request):
    if request.node.path.parent.name == "unit":
        yield
        return
    await create_schema()
    async with session_factory() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(delete(table))
        await session.commit()
    await vectorstore.reset()
    mesh.reset_call_log()
    yield
    await engine.dispose()


@pytest.fixture
async def shopper():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://hardy.test"
    ) as client:
        await client.post("/signup", data={"email": SHOPPER_EMAIL, "password": SHOPPER_PASSWORD})
        yield client


@pytest.fixture
def offline_mesh(monkeypatch):
    def install(replies: list[str] | None = None) -> OfflineMesh:
        fake = OfflineMesh(replies)
        monkeypatch.setattr(mesh, "chat", fake.chat)
        monkeypatch.setattr(mesh, "embed", fake.embed)
        monkeypatch.setattr(mesh, "embed_many", fake.embed_many)
        return fake

    return install
