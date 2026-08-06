import asyncio
import os
import tempfile
from decimal import Decimal

_WORKSPACE = tempfile.mkdtemp(prefix="hardy-dual-write-")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_WORKSPACE}/hardy.db"
os.environ["QDRANT_PATH"] = f"{_WORKSPACE}/qdrant"
os.environ["QDRANT_URL"] = ""

from src.catalog import service
from src.catalog.schemas import ProductWrite
from src.database import create_schema, session_factory
from src.integrations import vectorstore

SAMPLE = ProductWrite(
    title="Test cast iron skillet",
    brand="Testworks",
    description="A heavy pan that exists only to prove the dual write.",
    category="cookware",
    price=Decimal("4200.00"),
    expected_life_years=40,
)


async def _create() -> int:
    async with session_factory() as session:
        product = await service.create(session, SAMPLE)
        assert product.vector_synced_at is not None, "create did not stamp vector_synced_at"
        state = await service.consistency(session)
        assert state["sqlite_count"] == 1, state
        assert state["qdrant_count"] == 1, state
        assert state["in_sync"] is True, state
        payload = await vectorstore.payload_of(product.id)
        assert payload["title"] == SAMPLE.title, payload
        return product.id


async def _update(product_id: int) -> None:
    changed = SAMPLE.model_copy(update={"title": "Renamed skillet", "expected_life_years": 12})
    async with session_factory() as session:
        before = (await service.by_id(session, product_id)).vector_synced_at
        product = await service.replace(session, product_id, changed)
        assert product.title == "Renamed skillet"
        assert product.vector_synced_at >= before, "update did not restamp vector_synced_at"
        state = await service.consistency(session)
        assert state["in_sync"] is True, state
        payload = await vectorstore.payload_of(product_id)
        assert payload["title"] == "Renamed skillet", payload
        assert payload["expected_life_years"] == 12, payload


async def _delete(product_id: int) -> None:
    async with session_factory() as session:
        assert await service.remove(session, product_id) is True
        state = await service.consistency(session)
        assert state["sqlite_count"] == 0, state
        assert state["qdrant_count"] == 0, state
        assert state["in_sync"] is True, state
        assert await vectorstore.payload_of(product_id) is None


async def _neither_store_on_vector_failure() -> None:
    working = vectorstore.upsert

    async def refuse(*args, **kwargs):
        raise RuntimeError("vector store is down")

    vectorstore.upsert = refuse
    try:
        async with session_factory() as session:
            try:
                await service.create(session, SAMPLE)
            except RuntimeError:
                pass
            else:
                raise AssertionError("create should have propagated the vector failure")
    finally:
        vectorstore.upsert = working

    async with session_factory() as session:
        state = await service.consistency(session)
        assert state["sqlite_count"] == 0, f"SQLite kept a row the vector store rejected: {state}"
        assert state["qdrant_count"] == 0, state
        assert state["in_sync"] is True, state


def test_dual_write_covers_create_update_and_delete():
    async def run():
        await create_schema()
        await vectorstore.ensure_collection()
        product_id = await _create()
        await _update(product_id)
        await _delete(product_id)
        await _neither_store_on_vector_failure()

    asyncio.run(run())


if __name__ == "__main__":
    test_dual_write_covers_create_update_and_delete()
    print("PASS: create, update and delete each land in SQLite and Qdrant, or in neither")
