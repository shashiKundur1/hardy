from decimal import Decimal

import pytest

from src.constants import Stance
from src.recommendations import comparison


class Fake:
    def __init__(self, **fields):
        defaults = {
            "id": 1,
            "title": "A pan",
            "category": "cookware",
            "brand": "Testworks",
            "price": Decimal("10000.00"),
            "expected_life_years": 20,
            "repairability_score": 6.0,
            "ownership_type": "public",
            "evidence_source": None,
        }
        self.__dict__.update(defaults | fields)

    @property
    def cost_per_year(self) -> Decimal:
        return self.price / self.expected_life_years


PICK = Fake(id=1, title="The pick")


def test_the_pick_itself_is_recognised_rather_than_compared():
    reading = comparison.reading_for(PICK, PICK, seen_here=3)
    assert reading["stance"] is Stance.THE_PICK
    assert reading["lines"] == []
    assert "argued for" in reading["headline"]


def test_a_longer_lived_cheaper_thing_is_called_the_better_bet():
    viewed = Fake(id=2, expected_life_years=40, price=Decimal("12000.00"), repairability_score=9.0)
    reading = comparison.reading_for(viewed, PICK, seen_here=2)
    assert reading["stance"] is Stance.STRONGER
    assert "better bet" in reading["headline"]


def test_a_near_identical_thing_is_called_line_ball():
    viewed = Fake(id=2)
    reading = comparison.reading_for(viewed, PICK, seen_here=1)
    assert reading["stance"] is Stance.LEVEL
    assert "line-ball" in reading["headline"]


def test_a_shorter_lived_dearer_thing_keeps_hardy_on_its_pick():
    viewed = Fake(id=2, expected_life_years=5, price=Decimal("18000.00"), repairability_score=2.0)
    reading = comparison.reading_for(viewed, PICK, seen_here=4)
    assert reading["stance"] is Stance.WEAKER
    assert "still take mine" in reading["headline"]
    assert "The pick" in reading["body"]


def test_a_different_category_is_called_a_step_away():
    viewed = Fake(id=2, category="footwear")
    reading = comparison.reading_for(viewed, PICK, seen_here=1)
    assert reading["stance"] is Stance.ADRIFT
    assert reading["lines"] == []


@pytest.mark.parametrize(
    ("field", "value", "label", "favours"),
    [
        ("expected_life_years", 40, "Expected life", "viewed"),
        ("expected_life_years", 5, "Expected life", "pick"),
        ("repairability_score", 9.0, "Repairability", "viewed"),
        ("repairability_score", None, "Repairability", "pick"),
        ("evidence_source", "https://example.test/record", "Ownership", "viewed"),
    ],
)
def test_each_line_says_which_way_it_goes(field, value, label, favours):
    viewed = Fake(id=2, **{field: value})
    row = next(r for r in comparison.lines_for(viewed, PICK) if r["label"] == label)
    assert row["favours"] == favours


def test_a_cheaper_yearly_cost_favours_the_thing_being_looked_at():
    viewed = Fake(id=2, price=Decimal("4000.00"))
    row = next(r for r in comparison.lines_for(viewed, PICK) if r["label"] == "Cost per year")
    assert row["favours"] == "viewed"
    assert row["viewed"] == "₹200"
    assert row["pick"] == "₹500"


def test_an_unstated_repairability_is_said_not_invented():
    viewed = Fake(id=2, repairability_score=None)
    row = next(r for r in comparison.lines_for(viewed, PICK) if r["label"] == "Repairability")
    assert row["viewed"] == "not stated"


def test_every_stance_has_copy_so_none_can_render_blank():
    for stance in Stance:
        assert comparison.HEADLINES[stance]
        assert comparison.BODIES[stance]


def test_the_body_counts_only_the_lines_the_viewed_product_wins():
    viewed = Fake(id=2, expected_life_years=40, price=Decimal("12000.00"), repairability_score=9.0)
    reading = comparison.reading_for(viewed, PICK, seen_here=2)
    wins = sum(1 for row in reading["lines"] if row["favours"] == "viewed")
    assert f"on {wins} of the four" in reading["body"]
