from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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


templates = Jinja2Templates(directory=TEMPLATE_DIR)
templates.env.globals["asset_version"] = asset_version
templates.env.globals["tracking"] = {
    "endpoint": "/api/events",
    "batch_size": EVENT_BATCH_SIZE,
    "flush_ms": EVENT_FLUSH_MS,
    "debounce_ms": SEARCH_DEBOUNCE_MS,
}


def page(request: Request, name: str, status_code: int = 200, **context: Any) -> HTMLResponse:
    return templates.TemplateResponse(request, name, context, status_code=status_code)
