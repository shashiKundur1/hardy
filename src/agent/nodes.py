import hashlib
import json
from collections import Counter

from sqlalchemy import update

from src.agent import prompts, retrieval
from src.agent.state import AgentState, Candidate
from src.catalog.constants import CATEGORY_LABELS
from src.config import settings
from src.constants import (
    MAX_REFINE_LOOPS,
    MIN_EVENTS_TO_REASON,
    MIN_SOURCED_CANDIDATES,
    RETRIEVAL_K,
    EventType,
    Stage,
)
from src.database import session_factory
from src.events import service as events
from src.events.constants import RECENT_LIMIT
from src.integrations import mesh
from src.recommendations.models import Recommendation


def _summarise(rows: list[dict]) -> str:
    if not rows:
        return "No behaviour on record."
    kinds = Counter(row["type"] for row in rows)
    categories = Counter(row["category"] for row in rows if row["category"])
    queries = [row["query"] for row in rows if row["query"]]
    parts = [
        f"{len(rows)} events",
        f"{kinds.get(EventType.PRODUCT_VIEW, 0)} product views",
        f"{kinds.get(EventType.SEARCH, 0)} searches",
    ]
    if categories:
        leading = ", ".join(
            f"{CATEGORY_LABELS.get(slug, slug)} ({total})"
            for slug, total in categories.most_common(3)
        )
        parts.append(f"categories: {leading}")
    if queries:
        parts.append("searched for: " + "; ".join(queries[:3]))
    return ". ".join(parts) + "."


def _profile_hash(rows: list[dict]) -> str:
    signature = json.dumps(
        [[row["type"], row["product_id"], row["category"], row["query"]] for row in rows],
        sort_keys=True,
    )
    return hashlib.sha256(signature.encode()).hexdigest()


def _as_candidate(item: retrieval.Retrieved) -> Candidate:
    product = item.product
    return Candidate(
        product_id=product.id,
        title=product.title,
        brand=product.brand,
        category=product.category,
        price=float(product.price),
        cost_per_year=float(product.cost_per_year),
        expected_life_years=product.expected_life_years,
        ownership_type=str(product.ownership_type),
        ownership_note=product.ownership_note,
        evidence_source=product.evidence_source,
        repairability_score=product.repairability_score,
        semantic_score=round(item.semantic, 4),
        ranked_score=round(item.score, 4),
    )


def _render(candidates: list[Candidate]) -> str:
    if not candidates:
        return "Nothing was retrieved."
    lines = []
    for item in candidates:
        ownership = (
            item["ownership_type"] if item["ownership_type"] != "unknown" else "not on record"
        )
        source = item["evidence_source"] or "no source on file"
        lines.append(
            f"- {item['title']} by {item['brand']} ({item['category']}). "
            f"Price {item['price']:.0f}, expected life {item['expected_life_years']} years, "
            f"cost per year {item['cost_per_year']:.0f}. "
            f"Ownership: {ownership}. Repairability: {item['repairability_score']}. "
            f"Source: {source}."
        )
    return "\n".join(lines)


async def load_behaviour(state: AgentState) -> dict:
    async with session_factory() as session:
        recent = await events.recent_for(session, state["user_id"], RECENT_LIMIT)
    rows = [
        {
            "type": str(event.type),
            "product_id": event.product_id,
            "category": event.category,
            "query": event.query,
            "dwell_ms": event.dwell_ms,
        }
        for event in recent
    ]
    return {
        "events": rows,
        "behaviour_summary": _summarise(rows),
        "nodes_visited": [*state.get("nodes_visited", []), "load_behaviour"],
    }


async def infer_intent(state: AgentState) -> dict:
    rows = state["events"]
    if len(rows) < MIN_EVENTS_TO_REASON:
        return {
            "intent": None,
            "query": "",
            "nodes_visited": [*state["nodes_visited"], "infer_intent"],
        }

    kinds = Counter(row["type"] for row in rows)
    categories = sorted({row["category"] for row in rows if row["category"]})
    completion = await mesh.chat(
        [
            {"role": "system", "content": prompts.INTENT_SYSTEM},
            {
                "role": "user",
                "content": prompts.INTENT_USER.format(
                    events=json.dumps(rows, indent=2),
                    event_count=len(rows),
                    product_views=kinds.get(EventType.PRODUCT_VIEW, 0),
                    searches=kinds.get(EventType.SEARCH, 0),
                    categories=", ".join(categories) or "none",
                ),
            },
        ],
        response_format={"type": "json_object"},
    )

    try:
        parsed = json.loads(completion.content)
    except json.JSONDecodeError:
        parsed = {}

    intent = {
        "categories": [slug for slug in parsed.get("categories", []) if slug in CATEGORY_LABELS],
        "budget_hint": parsed.get("budget_hint", "unknown"),
        "priorities": parsed.get("priorities", []),
        "stage": parsed.get("stage", Stage.BROWSING),
        "evidence": parsed.get("evidence", ""),
    }
    terms = [*intent["priorities"], *(CATEGORY_LABELS[s] for s in intent["categories"])]
    return {
        "intent": intent,
        "query": " ".join(terms).strip(),
        "nodes_visited": [*state["nodes_visited"], "infer_intent"],
    }


async def retrieve(state: AgentState) -> dict:
    intent = state["intent"]
    category = intent["categories"][0] if len(intent["categories"]) == 1 else None
    async with session_factory() as session:
        found = await retrieval.hybrid(
            session, state["query"], category=category, limit=RETRIEVAL_K
        )
    ranked = [_as_candidate(item) for item in found]
    by_semantic = sorted(ranked, key=lambda item: item["semantic_score"], reverse=True)
    return {
        "candidates_raw": by_semantic,
        "candidates": ranked,
        "nodes_visited": [*state["nodes_visited"], "retrieve"],
    }


async def refine_query(state: AgentState) -> dict:
    sourced = sum(1 for item in state["candidates"] if item["evidence_source"])
    reason = (
        "nothing came back at all"
        if not state["candidates"]
        else f"only {sourced} of {len(state['candidates'])} candidates carry a source"
    )
    completion = await mesh.chat(
        [
            {"role": "system", "content": prompts.REFINE_SYSTEM},
            {
                "role": "user",
                "content": prompts.REFINE_USER.format(
                    query=state["query"],
                    candidates=_render(state["candidates"]),
                    reason=reason,
                ),
            },
        ]
    )
    return {
        "query": completion.content.strip() or state["query"],
        "refine_count": state["refine_count"] + 1,
        "nodes_visited": [*state["nodes_visited"], "refine_query"],
    }


async def generate(state: AgentState) -> dict:
    completion = await mesh.chat(
        [
            {"role": "system", "content": prompts.NARRATIVE_SYSTEM},
            {
                "role": "user",
                "content": prompts.NARRATIVE_USER.format(
                    behaviour_summary=state["behaviour_summary"],
                    intent=json.dumps(state["intent"]),
                    candidates=_render(state["candidates"]),
                ),
            },
        ]
    )
    return {
        "narrative": completion.content.strip(),
        "product_ids": [item["product_id"] for item in state["candidates"]],
        "nodes_visited": [*state["nodes_visited"], "generate"],
    }


async def store(state: AgentState) -> dict:
    usage = mesh.recent_calls(1)
    async with session_factory() as session:
        await session.execute(
            update(Recommendation)
            .where(
                Recommendation.user_id == state["user_id"],
                Recommendation.is_active.is_(True),
            )
            .values(is_active=False)
        )
        session.add(
            Recommendation(
                user_id=state["user_id"],
                narrative=state["narrative"],
                product_ids=json.dumps(state["product_ids"]),
                interest_profile=json.dumps(state["intent"]),
                trigger_reason=state["trigger_reason"],
                profile_hash=_profile_hash(state["events"]),
                events_covered=len(state["events"]),
                model_used=settings.mesh_chat_model,
                tokens_used=sum(call.total_tokens for call in mesh.recent_calls(20)),
                latency_ms=usage[0].latency_ms if usage else None,
                is_active=True,
            )
        )
        await session.commit()
    return {"nodes_visited": [*state["nodes_visited"], "store"]}


def should_retrieve(state: AgentState) -> str:
    if len(state["events"]) < MIN_EVENTS_TO_REASON:
        return "halt"
    if not state["intent"] or not state["intent"]["categories"]:
        return "halt"
    return "retrieve"


def grade_evidence(state: AgentState) -> str:
    candidates = state["candidates"]
    sourced = sum(1 for item in candidates if item["evidence_source"])
    if sourced >= MIN_SOURCED_CANDIDATES:
        return "generate"
    if state["refine_count"] < MAX_REFINE_LOOPS:
        return "refine"
    return "generate" if candidates else "halt"
