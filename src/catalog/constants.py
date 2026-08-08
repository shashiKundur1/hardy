from src.constants import SortOrder

FEATURED_LIMIT = 8
PAGE_SIZE = 24
SEARCH_LIMIT = 40
RELATED_LIMIT = 4
ADMIN_PAGE_SIZE = 25
MAX_PAGE = 500

SORT_LABELS = {
    SortOrder.LIFE: "Longest life",
    SortOrder.RATE: "Lowest cost per year",
    SortOrder.PRICE: "Lowest price",
    SortOrder.NEWEST: "Recently added",
}

LIFE_FLOORS = (10, 20, 30)
RATE_CEILINGS = (250, 500, 1000)

CATEGORY_LABELS = {
    "cookware": "Cookware",
    "tools": "Tools",
    "kitchen-appliances": "Kitchen appliances",
    "footwear": "Footwear",
    "bags-luggage": "Bags and luggage",
    "outdoor-gear": "Outdoor gear",
    "electronics": "Electronics",
    "home-basics": "Home basics",
}

CATEGORY_BLURBS = {
    "cookware": "Pans and pots that outlive the kitchen they were bought for.",
    "tools": "Hand and power tools judged on whether the parts still exist.",
    "kitchen-appliances": "Motors and gearboxes, rated on how long they stay serviceable.",
    "footwear": "Resolable construction, and who still resoles it.",
    "bags-luggage": "Hardware, stitching, and the warranty standing behind them.",
    "outdoor-gear": "Field-repairable kit, with the repair record attached.",
    "electronics": "Devices scored on spare parts and published documentation.",
    "home-basics": "The dull things you replace least often.",
}

CATEGORY_ANGLES = {
    "cookware": (
        "the whole pan",
        "the base, where the heat spreads",
        "the handle join and its rivets",
        "the rim and the pour edge",
    ),
    "tools": (
        "the whole tool",
        "the drive and the gearing",
        "the grip and the trigger",
        "the cord entry or battery seat",
    ),
    "kitchen-appliances": (
        "the whole machine",
        "the motor housing and vents",
        "the gearbox and drive coupling",
        "the seals and the parts that come off to clean",
    ),
    "footwear": (
        "the whole boot",
        "the welt, where the sole is joined",
        "the heel and the counter",
        "the eyelets and the lacing",
    ),
    "bags-luggage": (
        "the whole bag",
        "the hardware and the buckles",
        "the stitching where the strap meets the body",
        "the base and its corners",
    ),
    "outdoor-gear": (
        "the whole piece",
        "the seams and their taping",
        "the zips and the storm flap",
        "the anchor points that take the load",
    ),
    "electronics": (
        "the whole device",
        "the ports and the connectors",
        "the back, and how it opens",
        "the screen and its bezel",
    ),
    "home-basics": (
        "the whole thing",
        "the joints and the fixings",
        "the surface and its finish",
        "the underside, where the wear shows",
    ),
}

DEFAULT_ANGLES = (
    "the whole thing",
    "a closer look at the construction",
    "the join that takes the load",
    "the underside, where the wear shows",
)
