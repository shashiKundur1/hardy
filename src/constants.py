from enum import StrEnum


class Ownership(StrEnum):
    FAMILY = "family"
    EMPLOYEE = "employee"
    TRUST = "trust"
    PUBLIC = "public"
    CONGLOMERATE = "conglomerate"
    PRIVATE_EQUITY = "private_equity"
    UNKNOWN = "unknown"


CONTINUITY_OWNERSHIP = frozenset({Ownership.FAMILY, Ownership.EMPLOYEE, Ownership.TRUST})


class EventType(StrEnum):
    PAGE_VIEW = "page_view"
    PRODUCT_VIEW = "product_view"
    SEARCH = "search"
    CLICK = "click"
    DWELL = "dwell"


class TriggerReason(StrEnum):
    EVENT_THRESHOLD = "event_threshold"
    INTEREST_SHIFT = "interest_shift"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class SuppressionReason(StrEnum):
    TOO_FEW_EVENTS = "too_few_events"
    RATE_FLOOR = "rate_floor"
    CACHE_HIT = "cache_hit"
    THIN_SIGNAL = "thin_signal"


class Stage(StrEnum):
    BROWSING = "browsing"
    COMPARING = "comparing"
    DECIDING = "deciding"


class Role(StrEnum):
    USER = "user"
    ADMIN = "admin"


CATEGORIES = (
    "cookware",
    "tools",
    "kitchen-appliances",
    "footwear",
    "bags-luggage",
    "outdoor-gear",
    "electronics",
    "home-basics",
)

MIN_EVENTS_TO_REASON = 5
EVENT_THRESHOLD = 12
RATE_FLOOR_MINUTES = 10
INTEREST_SHIFT_WINDOW = 10
RETRIEVAL_K = 5
RETRIEVAL_OVERFETCH = 4
MAX_REFINE_LOOPS = 2

MIN_SOURCED_CANDIDATES = 2

DURABILITY_WEIGHT = 0.4
LIFE_CEILING_YEARS = 30
REPAIRABILITY_CEILING = 10.0
WEIGHT_LIFE = 0.4
WEIGHT_REPAIRABILITY = 0.3
WEIGHT_CONTINUITY = 0.2
WEIGHT_EVIDENCE = 0.1

EVENT_BATCH_SIZE = 20
EVENT_FLUSH_MS = 5000
SEARCH_DEBOUNCE_MS = 800
