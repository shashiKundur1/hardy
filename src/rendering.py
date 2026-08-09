from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from src.auth import avatar as avatars
from src.catalog.constants import CATEGORY_LABELS
from src.constants import EVENT_BATCH_SIZE, EVENT_FLUSH_MS, SEARCH_DEBOUNCE_MS

TEMPLATE_DIR = Path(__file__).parent / "templates"
ASSET_DIRS = (Path(__file__).parent / "static", Path(__file__).parent.parent / "brand")


def asset_version() -> int:
    return max(
        int(path.stat().st_mtime)
        for directory in ASSET_DIRS
        for path in directory.rglob("*")
        if path.suffix in {".css", ".js"}
    )


def compact(value: float | int | None) -> str:
    if value is None:
        return "—"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def avatar(user, size: int = 48) -> Markup:
    return Markup(avatars.for_user(user, size))


def full_path(request: Request) -> str:
    return f"{request.url.path}?{request.url.query}" if request.url.query else request.url.path


templates = Jinja2Templates(directory=TEMPLATE_DIR)
templates.env.globals["asset_version"] = asset_version
templates.env.globals["avatar"] = avatar
templates.env.globals["full_path"] = full_path
templates.env.globals["all_categories"] = [
    {"slug": slug, "label": label} for slug, label in CATEGORY_LABELS.items()
]
templates.env.filters["compact"] = compact
templates.env.globals["tracking"] = {
    "endpoint": "/api/events",
    "batch_size": EVENT_BATCH_SIZE,
    "flush_ms": EVENT_FLUSH_MS,
    "debounce_ms": SEARCH_DEBOUNCE_MS,
}


def page(request: Request, name: str, status_code: int = 200, **context: Any) -> HTMLResponse:
    return templates.TemplateResponse(request, name, context, status_code=status_code)
