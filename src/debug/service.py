import json

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.catalog import service as catalog
from src.database import utcnow
from src.debug.constants import MESH_LIMIT, STREAM_LIMIT
from src.events import service as events
from src.events.models import Event
from src.integrations import mesh
from src.recommendations import service as recommendations


def _loads(raw: str | None) -> dict:
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}


def batches(rows: list[Event]) -> list[dict]:
    grouped: list[dict] = []
    for event in rows:
        if not grouped or grouped[-1]["batch"] != event.batch:
            grouped.append({"batch": event.batch, "at": event.created_at, "events": []})
        grouped[-1]["events"].append(event)
    return grouped


async def snapshot(session: AsyncSession, user: User | None) -> dict:
    view = {
        "taken_at": utcnow(),
        "consistency": await catalog.consistency(session),
        "catalog_version": await catalog.version(session),
        "mesh_calls": mesh.recent_calls(MESH_LIMIT),
        "mesh_total": mesh.call_count(),
        "user": user,
    }
    if user is None:
        return {**view, "efficiency": None, "batches": [], "decisions": [], "active": None}

    active = await recommendations.active_for(session, user.id)
    return {
        **view,
        "efficiency": await recommendations.efficiency(session, user.id),
        "batches": batches(await events.recent_for(session, user.id, STREAM_LIMIT)),
        "decisions": await recommendations.decisions_for(session, user.id),
        "active": active,
        "intent": _loads(active.interest_profile) if active else {},
        "retrieval": _loads(active.retrieval_trace) if active else {},
        "path": _loads(active.agent_path) if active else {},
        "products": await recommendations.products_for(session, active) if active else [],
    }
