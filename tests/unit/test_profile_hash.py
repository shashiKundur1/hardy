from src.recommendations.triggers import profile_hash

ROWS = [
    {"type": "product_view", "product_id": 3, "category": "cookware", "query": None},
    {"type": "search", "product_id": None, "category": None, "query": "cast iron"},
]
VERSION = "12@2026-08-06T09:00:00"


def test_the_same_behaviour_hashes_the_same_way():
    assert profile_hash(ROWS, VERSION) == profile_hash(list(ROWS), VERSION)


def test_the_order_events_arrived_in_does_not_change_the_hash():
    assert profile_hash(ROWS, VERSION) == profile_hash(list(reversed(ROWS)), VERSION)


def test_a_new_category_changes_the_hash():
    extra = [*ROWS, {"type": "product_view", "product_id": 9, "category": "tools", "query": None}]
    assert profile_hash(extra, VERSION) != profile_hash(ROWS, VERSION)


def test_a_new_query_changes_the_hash():
    extra = [*ROWS, {"type": "search", "product_id": None, "category": None, "query": "boots"}]
    assert profile_hash(extra, VERSION) != profile_hash(ROWS, VERSION)


def test_a_new_product_changes_the_hash():
    extra = [
        *ROWS,
        {"type": "product_view", "product_id": 4, "category": "cookware", "query": None},
    ]
    assert profile_hash(extra, VERSION) != profile_hash(ROWS, VERSION)


def test_a_catalog_change_invalidates_the_hash():
    assert profile_hash(ROWS, VERSION) != profile_hash(ROWS, "13@2026-08-06T09:30:00")


def test_repeating_an_event_does_not_change_the_hash():
    assert profile_hash([*ROWS, ROWS[0]], VERSION) == profile_hash(ROWS, VERSION)
