from decimal import Decimal

import pytest

from src.catalog import service
from src.catalog.schemas import ProductWrite
from src.database import session_factory
from src.integrations import vectorstore

SAMPLE = ProductWrite(
    title="Test cast iron skillet",
    brand="Testworks",
    description="A heavy pan that exists only to prove the dual write.",
    category="cookware",
    price=Decimal("4200.00"),
    expected_life_years=40,
)


async def test_a_create_lands_in_both_stores(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        product = await service.create(session, SAMPLE)
        assert product.vector_synced_at is not None
        state = await service.consistency(session)
        assert state == {
            **state,
            "sqlite_count": 1,
            "qdrant_count": 1,
            "in_sync": True,
            "never_synced": 0,
        }
        assert (await vectorstore.payload_of(product.id))["title"] == SAMPLE.title


async def test_an_update_restamps_and_rewrites_the_vector(offline_mesh):
    offline_mesh()
    changed = SAMPLE.model_copy(update={"title": "Renamed skillet", "expected_life_years": 12})
    async with session_factory() as session:
        created = await service.create(session, SAMPLE)
        before = created.vector_synced_at
        product = await service.replace(session, created.id, changed)
        assert product.title == "Renamed skillet"
        assert product.vector_synced_at >= before
        assert (await service.consistency(session))["in_sync"] is True
        payload = await vectorstore.payload_of(created.id)
        assert payload["title"] == "Renamed skillet"
        assert payload["expected_life_years"] == 12


async def test_a_delete_clears_both_stores(offline_mesh):
    offline_mesh()
    async with session_factory() as session:
        created = await service.create(session, SAMPLE)
        assert await service.remove(session, created.id) is True
        state = await service.consistency(session)
        assert state["sqlite_count"] == 0
        assert state["qdrant_count"] == 0
        assert state["in_sync"] is True
        assert await vectorstore.payload_of(created.id) is None


async def test_a_vector_failure_leaves_no_row_behind(offline_mesh, monkeypatch):
    offline_mesh()

    async def refuse(*_args, **_kwargs):
        raise RuntimeError("vector store is down")

    monkeypatch.setattr(vectorstore, "upsert", refuse)
    async with session_factory() as session:
        with pytest.raises(RuntimeError):
            await service.create(session, SAMPLE)

    monkeypatch.undo()
    async with session_factory() as session:
        state = await service.consistency(session)
        assert state["sqlite_count"] == 0, "SQLite kept a row the vector store rejected"
        assert state["qdrant_count"] == 0
        assert state["in_sync"] is True
