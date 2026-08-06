from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.catalog.models import Product
from src.constants import (
    CONTINUITY_OWNERSHIP,
    DURABILITY_WEIGHT,
    LIFE_CEILING_YEARS,
    REPAIRABILITY_CEILING,
    RETRIEVAL_K,
    RETRIEVAL_OVERFETCH,
    WEIGHT_CONTINUITY,
    WEIGHT_EVIDENCE,
    WEIGHT_LIFE,
    WEIGHT_REPAIRABILITY,
)
from src.integrations import mesh, vectorstore


@dataclass(frozen=True)
class Retrieved:
    product: Product
    semantic: float
    durability: float
    score: float


def durability_of(payload: dict) -> float:
    life = min(payload.get("expected_life_years") or 0, LIFE_CEILING_YEARS)
    repairability = payload.get("repairability_score") or 0.0
    continuity = payload.get("ownership_type") in CONTINUITY_OWNERSHIP
    return (
        WEIGHT_LIFE * (life / LIFE_CEILING_YEARS)
        + WEIGHT_REPAIRABILITY * (repairability / REPAIRABILITY_CEILING)
        + WEIGHT_CONTINUITY * float(continuity)
        + WEIGHT_EVIDENCE * float(bool(payload.get("has_evidence")))
    )


async def hybrid(
    session: AsyncSession,
    query: str,
    category: str | None = None,
    minimum_life: int | None = None,
    limit: int = RETRIEVAL_K,
) -> list[Retrieved]:
    await vectorstore.ensure_collection()
    embedding = await mesh.embed(query)
    hits = await vectorstore.search(
        embedding.vector,
        limit=limit * RETRIEVAL_OVERFETCH,
        category=category,
        minimum_life=minimum_life,
    )
    if not hits:
        return []

    products = {
        product.id: product
        for product in await session.scalars(
            select(Product).where(Product.id.in_([int(hit.id) for hit in hits]))
        )
    }

    ranked = []
    for hit in hits:
        product = products.get(int(hit.id))
        if product is None:
            continue
        durability = durability_of(hit.payload or {})
        ranked.append(
            Retrieved(
                product=product,
                semantic=hit.score,
                durability=durability,
                score=(1 - DURABILITY_WEIGHT) * hit.score + DURABILITY_WEIGHT * durability,
            )
        )

    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:limit]
