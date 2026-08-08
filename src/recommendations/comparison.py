from src.agent.retrieval import durability_of
from src.catalog.models import Product
from src.catalog.service import vector_payload
from src.constants import (
    DURABILITY_TIE,
    RATE_TOLERANCE_HIGH,
    RATE_TOLERANCE_LOW,
    Stance,
)

HEADLINES = {
    Stance.THE_PICK: "This is the one I argued for",
    Stance.STRONGER: "This is a better bet than the one I picked",
    Stance.LEVEL: "Not a bad choice — it is line-ball with my pick",
    Stance.WEAKER: "Reasonable direction, but I would still take mine",
    Stance.ADRIFT: "This is a step away from what your browsing pointed at",
}

BODIES = {
    Stance.THE_PICK: (
        "Everything I hold on it is below, and the case for it is on your recommendations page."
    ),
    Stance.STRONGER: (
        "It beats {pick} on {wins} of the four things I judge on. If you were weighing the two, "
        "take this one."
    ),
    Stance.LEVEL: (
        "It wins {wins} of the four and loses the rest, so there is nothing in it. Pick the one "
        "you would rather own."
    ),
    Stance.WEAKER: (
        "{pick} still comes out ahead on the numbers below. Worth a look, but I would not switch "
        "on what I can see."
    ),
    Stance.ADRIFT: (
        "I read your last few minutes as pointing at {pick}. This is a different category, so "
        "there is nothing to compare — browse a little and I will catch up."
    ),
}


def rupees(amount) -> str:
    return f"₹{amount:,.0f}"


def as_score(value: float | None) -> str:
    return f"{value:g} of 10" if value is not None else "not stated"


def as_record(sourced: bool) -> str:
    return "on record" if sourced else "not recorded"


def stance_for(viewed: Product, pick: Product) -> Stance:
    if viewed.id == pick.id:
        return Stance.THE_PICK
    if viewed.category != pick.category:
        return Stance.ADRIFT
    gap = durability_of(vector_payload(viewed)) - durability_of(vector_payload(pick))
    ratio = float(viewed.cost_per_year) / float(pick.cost_per_year)
    if gap >= DURABILITY_TIE and ratio <= RATE_TOLERANCE_HIGH:
        return Stance.STRONGER
    if abs(gap) < DURABILITY_TIE and RATE_TOLERANCE_LOW <= ratio <= RATE_TOLERANCE_HIGH:
        return Stance.LEVEL
    return Stance.WEAKER


def line(label: str, here: str, there: str, favours: str) -> dict:
    return {"label": label, "viewed": here, "pick": there, "favours": favours}


def better(here, there, higher_wins: bool) -> str:
    if here == there:
        return "level"
    if here is None:
        return "pick"
    if there is None:
        return "viewed"
    ahead = here > there if higher_wins else here < there
    return "viewed" if ahead else "pick"


def lines_for(viewed: Product, pick: Product) -> list[dict]:
    return [
        line(
            "Cost per year",
            rupees(viewed.cost_per_year),
            rupees(pick.cost_per_year),
            better(viewed.cost_per_year, pick.cost_per_year, higher_wins=False),
        ),
        line(
            "Expected life",
            f"{viewed.expected_life_years} years",
            f"{pick.expected_life_years} years",
            better(viewed.expected_life_years, pick.expected_life_years, higher_wins=True),
        ),
        line(
            "Repairability",
            as_score(viewed.repairability_score),
            as_score(pick.repairability_score),
            better(viewed.repairability_score, pick.repairability_score, higher_wins=True),
        ),
        line(
            "Ownership",
            as_record(bool(viewed.evidence_source)),
            as_record(bool(pick.evidence_source)),
            better(bool(viewed.evidence_source), bool(pick.evidence_source), higher_wins=True),
        ),
    ]


def reading_for(viewed: Product, pick: Product, seen_here: int) -> dict:
    stance = stance_for(viewed, pick)
    comparable = stance not in (Stance.THE_PICK, Stance.ADRIFT)
    lines = lines_for(viewed, pick) if comparable else []
    wins = sum(1 for entry in lines if entry["favours"] == "viewed")
    return {
        "stance": stance,
        "headline": HEADLINES[stance],
        "body": BODIES[stance].format(pick=pick.title, wins=wins, seen=seen_here),
        "lines": lines,
        "pick": pick,
        "seen_here": seen_here,
    }
