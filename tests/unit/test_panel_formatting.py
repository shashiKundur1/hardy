from datetime import datetime

from src.debug.service import batches
from src.events.models import Event
from src.rendering import compact


def _event(batch: str, minute: int) -> Event:
    return Event(batch=batch, type="product_view", created_at=datetime(2026, 8, 6, 12, minute))


def test_values_under_a_thousand_stay_exact():
    assert compact(0) == "0"
    assert compact(842) == "842"
    assert compact(999) == "999"


def test_thousands_carry_one_decimal():
    assert compact(1_000) == "1.0K"
    assert compact(12_400) == "12.4K"


def test_millions_carry_one_decimal():
    assert compact(1_200_000) == "1.2M"


def test_a_missing_number_is_a_dash_not_a_zero():
    assert compact(None) == "—"


def test_consecutive_events_of_one_batch_group_together():
    rows = [_event("aaa", 3), _event("aaa", 2), _event("bbb", 1)]
    grouped = batches(rows)
    assert [group["batch"] for group in grouped] == ["aaa", "bbb"]
    assert [len(group["events"]) for group in grouped] == [2, 1]


def test_a_batch_that_reappears_later_opens_a_new_group():
    rows = [_event("aaa", 4), _event("bbb", 3), _event("aaa", 2)]
    assert [group["batch"] for group in batches(rows)] == ["aaa", "bbb", "aaa"]


def test_no_events_means_no_groups():
    assert batches([]) == []
