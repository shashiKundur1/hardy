from typing import Annotated, TypedDict

from src.constants import Stage


class Intent(TypedDict):
    categories: list[str]
    budget_hint: str
    priorities: list[str]
    stage: Stage
    evidence: str


class Candidate(TypedDict):
    product_id: int
    title: str
    brand: str
    category: str
    price: float
    cost_per_year: float
    expected_life_years: int
    ownership_type: str
    ownership_note: str | None
    evidence_source: str | None
    repairability_score: float | None
    semantic_score: float
    ranked_score: float


def replace(_current: list, incoming: list) -> list:
    return incoming


class AgentState(TypedDict):
    user_id: int
    trigger_reason: str
    events: Annotated[list[dict], replace]
    behaviour_summary: str
    intent: Intent
    query: str
    candidates_raw: Annotated[list[Candidate], replace]
    candidates: Annotated[list[Candidate], replace]
    evidence_ok: bool
    refine_count: int
    narrative: str
    product_ids: list[int]
    nodes_visited: Annotated[list[str], replace]
