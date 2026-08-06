from hypothesis import given
from hypothesis import strategies as st

from src.agent.retrieval import durability_of
from src.constants import Ownership

TOLERANCE = 1e-9

payloads = st.builds(
    lambda life, repair, owner, evidence: {
        "expected_life_years": life,
        "repairability_score": repair,
        "ownership_type": owner,
        "has_evidence": evidence,
    },
    life=st.integers(min_value=0, max_value=200),
    repair=st.one_of(st.none(), st.floats(min_value=0, max_value=10)),
    owner=st.sampled_from([option.value for option in Ownership]),
    evidence=st.booleans(),
)


@given(payloads)
def test_durability_stays_inside_the_unit_interval(payload):
    score = durability_of(payload)
    assert 0.0 <= score <= 1.0, (payload, score)


@given(
    payloads,
    st.integers(min_value=0, max_value=200),
    st.integers(min_value=0, max_value=200),
)
def test_a_longer_life_never_scores_lower(payload, first, second):
    shorter, longer = sorted((first, second))
    low = durability_of({**payload, "expected_life_years": shorter})
    high = durability_of({**payload, "expected_life_years": longer})
    assert low <= high + TOLERANCE, (payload, shorter, longer, low, high)


@given(payloads)
def test_a_source_never_lowers_the_score(payload):
    without = durability_of({**payload, "has_evidence": False})
    with_source = durability_of({**payload, "has_evidence": True})
    assert without <= with_source + TOLERANCE, (payload, without, with_source)


@given(payloads)
def test_missing_repairability_is_treated_as_absent_not_as_an_error(payload):
    assert durability_of({**payload, "repairability_score": None}) >= 0.0
