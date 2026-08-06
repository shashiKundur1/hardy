from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    Range,
    ScoredPoint,
    VectorParams,
)

from src.config import settings

SCROLL_PAGE = 256

_client: AsyncQdrantClient | None = None


def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = (
            AsyncQdrantClient(url=settings.qdrant_url)
            if settings.qdrant_url
            else AsyncQdrantClient(path=settings.qdrant_path)
        )
    return _client


async def ensure_collection() -> None:
    client = get_client()
    if await client.collection_exists(settings.qdrant_collection):
        return
    await client.create_collection(
        settings.qdrant_collection,
        vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
    )


async def upsert(point_id: int, vector: list[float], payload: dict) -> None:
    await get_client().upsert(
        settings.qdrant_collection,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
    )


async def delete(point_id: int) -> None:
    await get_client().delete(settings.qdrant_collection, points_selector=[point_id])


async def search(
    vector: list[float],
    limit: int,
    category: str | None = None,
    minimum_life: int | None = None,
) -> list[ScoredPoint]:
    conditions = []
    if category:
        conditions.append(FieldCondition(key="category", match=MatchValue(value=category)))
    if minimum_life:
        conditions.append(FieldCondition(key="expected_life_years", range=Range(gte=minimum_life)))
    response = await get_client().query_points(
        settings.qdrant_collection,
        query=vector,
        limit=limit,
        query_filter=Filter(must=conditions) if conditions else None,
    )
    return response.points


async def payload_of(point_id: int) -> dict | None:
    points = await get_client().retrieve(
        settings.qdrant_collection, ids=[point_id], with_payload=True
    )
    return points[0].payload if points else None


async def count() -> int:
    info = await get_client().get_collection(settings.qdrant_collection)
    return info.points_count or 0


async def point_ids() -> set[int]:
    client = get_client()
    found: set[int] = set()
    offset = None
    while True:
        points, offset = await client.scroll(
            settings.qdrant_collection,
            limit=SCROLL_PAGE,
            offset=offset,
            with_payload=False,
            with_vectors=False,
        )
        found.update(int(point.id) for point in points)
        if offset is None:
            return found


async def reset() -> None:
    client = get_client()
    if await client.collection_exists(settings.qdrant_collection):
        await client.delete_collection(settings.qdrant_collection)
    await ensure_collection()
