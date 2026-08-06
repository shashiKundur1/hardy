from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.catalog.constants import CATEGORY_BLURBS, CATEGORY_LABELS
from src.catalog.models import Product
from src.catalog.schemas import ProductWrite
from src.constants import CATEGORIES
from src.database import session_factory, utcnow
from src.integrations import mesh, vectorstore

EMBED_BATCH = 32


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


async def version(session: AsyncSession) -> str:
    total, latest = (
        await session.execute(select(func.count(Product.id), func.max(Product.updated_at)))
    ).one()
    return f"{total}@{latest.isoformat(timespec='seconds') if latest else 'empty'}"


async def counts_by_category(session: AsyncSession) -> dict[str, int]:
    statement = select(Product.category, func.count()).group_by(Product.category)
    return dict((await session.execute(statement)).all())


async def sourced_count(session: AsyncSession) -> int:
    statement = select(func.count()).select_from(Product).where(Product.evidence_source.isnot(None))
    return await session.scalar(statement) or 0


def embedding_text(product: Product) -> str:
    return " · ".join(
        (
            product.title,
            product.brand,
            CATEGORY_LABELS[product.category],
            f"{product.expected_life_years} year expected life",
            product.description,
        )
    )


def vector_payload(product: Product) -> dict:
    return {
        "title": product.title,
        "brand": product.brand,
        "category": product.category,
        "price": float(product.price),
        "expected_life_years": product.expected_life_years,
        "ownership_type": str(product.ownership_type),
        "repairability_score": product.repairability_score,
        "has_evidence": product.evidence_source is not None,
    }


async def _write_vector(product: Product) -> None:
    embedding = await mesh.embed(embedding_text(product))
    await vectorstore.upsert(product.id, embedding.vector, vector_payload(product))


async def _restore_vector(product_id: int) -> None:
    async with session_factory() as session:
        product = await session.get(Product, product_id)
        if product is None:
            await vectorstore.delete(product_id)
            return
        await _write_vector(product)
        product.vector_synced_at = utcnow()
        await session.commit()


async def _commit_or_restore(session: AsyncSession, product_id: int) -> None:
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        await _restore_vector(product_id)
        raise


async def create(session: AsyncSession, data: ProductWrite) -> Product:
    product = Product(**data.model_dump())
    session.add(product)
    await session.flush()
    try:
        await _write_vector(product)
    except Exception:
        await session.rollback()
        raise
    product.vector_synced_at = utcnow()
    await _commit_or_restore(session, product.id)
    return product


async def replace(session: AsyncSession, product_id: int, data: ProductWrite) -> Product | None:
    product = await session.get(Product, product_id)
    if product is None:
        return None
    for field, value in data.model_dump().items():
        setattr(product, field, value)
    await session.flush()
    try:
        await _write_vector(product)
    except Exception:
        await session.rollback()
        raise
    product.vector_synced_at = utcnow()
    await _commit_or_restore(session, product_id)
    return product


async def remove(session: AsyncSession, product_id: int) -> bool:
    product = await session.get(Product, product_id)
    if product is None:
        return False
    await session.delete(product)
    await session.flush()
    try:
        await vectorstore.delete(product_id)
    except Exception:
        await session.rollback()
        raise
    await _commit_or_restore(session, product_id)
    return True


async def consistency(session: AsyncSession) -> dict:
    await vectorstore.ensure_collection()
    stored = set(await session.scalars(select(Product.id)))
    vectors = await vectorstore.point_ids()
    never_synced = (
        await session.scalar(
            select(func.count()).select_from(Product).where(Product.vector_synced_at.is_(None))
        )
        or 0
    )
    missing = sorted(stored - vectors)
    orphaned = sorted(vectors - stored)
    return {
        "sqlite_count": len(stored),
        "qdrant_count": len(vectors),
        "missing_from_qdrant": missing,
        "orphaned_in_qdrant": orphaned,
        "never_synced": never_synced,
        "in_sync": not missing and not orphaned and never_synced == 0,
    }


async def resync_all(session: AsyncSession) -> int:
    await vectorstore.ensure_collection()
    products = list(await session.scalars(select(Product).order_by(Product.id)))
    stamped = utcnow()
    for start in range(0, len(products), EMBED_BATCH):
        window = products[start : start + EMBED_BATCH]
        embeddings = await mesh.embed_many([embedding_text(item) for item in window])
        for product, embedding in zip(window, embeddings, strict=True):
            await vectorstore.upsert(product.id, embedding.vector, vector_payload(product))
            product.vector_synced_at = stamped
    await session.commit()
    return len(products)


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
