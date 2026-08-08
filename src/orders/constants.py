CART_KEY = "cart"
MAX_CART_LINES = 20
MAX_LINE_QUANTITY = 10
ORDER_HISTORY = 50
MAX_REPORT_NOTE = 300

CARE_INTERVALS = {
    "cookware": (6, "Re-season the surface, and check the handle rivets for movement"),
    "tools": (12, "Clean and oil the moving parts, and check the cord or battery contacts"),
    "kitchen-appliances": (12, "Descale, and check the gearbox and seals for play"),
    "footwear": (6, "Condition the leather, and look at the welt before the sole goes"),
    "bags-luggage": (12, "Wax the fabric, and check the stitching where the strap meets the body"),
    "outdoor-gear": (6, "Re-proof the shell, and check the zips and seam tape"),
    "electronics": (
        24,
        "Replace the battery if it holds less than it did, and back the storage up",
    ),
    "home-basics": (24, "Check the joints and fixings, and tighten anything that has worked loose"),
}

WEAR_LABELS = {
    "holding_up": "Holding up",
    "worn": "Wearing, but working",
    "failed": "Failed early",
}

DAYS_PER_MONTH = 30.44
DEFAULT_CARE = (12, "Look it over, and tighten or replace whatever has worked loose")
