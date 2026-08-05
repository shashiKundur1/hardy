from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.catalog.constants import CATEGORY_BLURBS, CATEGORY_LABELS
from src.catalog.models import Product
from src.constants import CATEGORIES


async def featured(session: AsyncSession, limit: int) -> list[Product]:
    statement = select(Product).order_by(Product.expected_life_years.desc()).limit(limit)
    return list(await session.scalars(statement))


async def by_category(session: AsyncSession, category: str, limit: int) -> list[Product]:
    statement = (
        select(Product)
        .where(Product.category == category)
        .order_by(Product.expected_life_years.desc())
        .limit(limit)
    )
    return list(await session.scalars(statement))


async def by_id(session: AsyncSession, product_id: int) -> Product | None:
    return await session.get(Product, product_id)


async def related(session: AsyncSession, product: Product, limit: int) -> list[Product]:
    statement = (
        select(Product)
        .where(Product.category == product.category, Product.id != product.id)
        .order_by(Product.expected_life_years.desc())
        .limit(limit)
    )
    return list(await session.scalars(statement))


async def search(session: AsyncSession, query: str, limit: int) -> list[Product]:
    pattern = f"%{query.strip()}%"
    statement = (
        select(Product)
        .where(
            or_(
                Product.title.ilike(pattern),
                Product.brand.ilike(pattern),
                Product.description.ilike(pattern),
            )
        )
        .order_by(Product.expected_life_years.desc())
        .limit(limit)
    )
    return list(await session.scalars(statement))


async def count(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(Product)) or 0


async def counts_by_category(session: AsyncSession) -> dict[str, int]:
    statement = select(Product.category, func.count()).group_by(Product.category)
    return {category: total for category, total in await session.execute(statement)}


async def sourced_count(session: AsyncSession) -> int:
    statement = select(func.count()).select_from(Product).where(Product.evidence_source.isnot(None))
    return await session.scalar(statement) or 0


async def navigation(session: AsyncSession) -> list[dict]:
    totals = await counts_by_category(session)
    return [
        {
            "slug": slug,
            "label": CATEGORY_LABELS[slug],
            "blurb": CATEGORY_BLURBS[slug],
            "total": totals.get(slug, 0),
        }
        for slug in CATEGORIES
    ]
