from collections.abc import AsyncIterator
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


async def create_schema() -> None:
    from src.auth.models import User
    from src.catalog.models import Product
    from src.events.models import Event
    from src.recommendations.models import Recommendation

    tables = [model.__table__ for model in (User, Product, Event, Recommendation)]
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=tables)
