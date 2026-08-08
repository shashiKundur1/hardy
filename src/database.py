from collections.abc import AsyncIterator
from datetime import UTC, datetime
from importlib import import_module
from typing import Annotated

from fastapi import Depends
from sqlalchemy import event, inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.schema import CreateColumn

from src.config import settings

engine = create_async_engine(settings.database_url)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

BUSY_TIMEOUT_MS = 5000


@event.listens_for(engine.sync_engine, "connect")
def apply_sqlite_pragmas(connection, _record) -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    cursor = connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def add_missing_columns(connection) -> None:
    inspector = inspect(connection)
    for table in Base.metadata.sorted_tables:
        present = {column["name"] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in present:
                continue
            spec = CreateColumn(column).compile(dialect=connection.dialect)
            connection.exec_driver_sql(f"ALTER TABLE {table.name} ADD COLUMN {spec}")


async def create_schema() -> None:
    import_module("src.models")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.run_sync(add_missing_columns)
