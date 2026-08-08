DEFAULT_PATH = "/shop"


def safe_path(target: str | None, fallback: str = DEFAULT_PATH) -> str:
    if not target or not target.startswith("/"):
        return fallback
    if len(target) > 1 and target[1] in "/\\":
        return fallback
    return target
