HOME = {"label": "Back to the storefront", "href": "/"}
SEARCH = {"label": "Search the catalog", "href": "/search"}
SIGN_IN = {"label": "Sign in", "href": "/login"}
GLASS_BOX = {"label": "Open the glass box", "href": "/debug"}

FALLBACK = {
    "headline": "Something went wrong",
    "explanation": (
        "The request did not complete, and Hardy cannot say more than that with confidence. "
        "The storefront itself is still up."
    ),
    "actions": [HOME, SEARCH],
}

FAULTS = {
    401: {
        "headline": "This page needs an account",
        "explanation": (
            "Recommendations are built from your own browsing, so there is nothing to show "
            "until Hardy knows whose browsing it is."
        ),
        "actions": [SIGN_IN, HOME],
    },
    403: {
        "headline": "This page is for administrators",
        "explanation": (
            "The account is signed in and working normally; it just does not carry admin "
            "rights. If it should, the account that created it can grant them."
        ),
        "actions": [HOME, SEARCH],
    },
    404: {
        "headline": "Nothing lives at this address",
        "explanation": (
            "The page may have been renamed, or the address may have a character out of place. "
            "The catalog is unaffected and still fully browsable."
        ),
        "actions": [HOME, SEARCH],
    },
    405: {
        "headline": "That address does not take this kind of request",
        "explanation": (
            "The page exists, but not for this method. This usually means a form was submitted "
            "twice, or an action was bookmarked and opened directly."
        ),
        "actions": [HOME, SEARCH],
    },
    409: {
        "headline": "That email already has an account",
        "explanation": "Sign in with it instead, or create the account under a different address.",
        "actions": [SIGN_IN, HOME],
    },
    422: {
        "headline": "Part of that request could not be read",
        "explanation": (
            "One of the values sent was outside the range Hardy accepts, so it was refused "
            "rather than stored. Nothing was changed."
        ),
        "actions": [HOME, SEARCH],
    },
    500: {
        "headline": "Hardy failed on its own side",
        "explanation": (
            "This is a fault in the application, not in anything you did. It has been logged "
            "with its stack trace. The same page is worth trying again in a moment."
        ),
        "actions": [HOME, GLASS_BOX],
    },
}


def fault_for(status_code: int) -> dict:
    return FAULTS.get(status_code, FALLBACK)
