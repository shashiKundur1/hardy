from collections.abc import AsyncIterator
from datetime import UTC, datetime
from importlib import import_module
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

engine = create_async_engine(settings.database_url)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def create_schema() -> None:
    import_module("src.models")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
