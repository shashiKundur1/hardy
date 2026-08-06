from src.constants import EventType

MAX_BATCH = 50
MAX_QUERY_LENGTH = 200
RECENT_LIMIT = 20
FOOTPRINT_LIMIT = 60

MEANINGFUL_TYPES = frozenset(
    {EventType.PRODUCT_VIEW, EventType.SEARCH, EventType.CLICK, EventType.DWELL}
)
