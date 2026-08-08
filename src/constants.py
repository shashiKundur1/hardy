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
    ADD_TO_CART = "add_to_cart"
    PURCHASE = "purchase"


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


class SearchMode(StrEnum):
    WORDS = "words"
    MEANING = "meaning"


class Stance(StrEnum):
    THE_PICK = "the_pick"
    STRONGER = "stronger"
    LEVEL = "level"
    WEAKER = "weaker"
    ADRIFT = "adrift"


class Wear(StrEnum):
    HOLDING = "holding_up"
    WORN = "worn"
    FAILED = "failed"


class SortOrder(StrEnum):
    LIFE = "life"
    RATE = "rate"
    PRICE = "price"
    NEWEST = "newest"


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

MAX_SQLITE_INTEGER = 2**63 - 1

MIN_SOURCED_CANDIDATES = 2

DURABILITY_TIE = 0.05
RATE_TOLERANCE_LOW = 0.8
RATE_TOLERANCE_HIGH = 1.25

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
