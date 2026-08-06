from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.auth.dependencies import OptionalUser
from src.catalog import service as catalog
from src.database import SessionDep
from src.debug import service
from src.debug.constants import REFRESH_SECONDS
from src.rendering import page

router = APIRouter(tags=["debug"])


@router.get("/debug", response_class=HTMLResponse)
async def glass_box(request: Request, session: SessionDep, user: OptionalUser) -> HTMLResponse:
    return page(
        request,
        "debug.html",
        page_id="debug",
        categories=await catalog.navigation(session),
        refresh_seconds=REFRESH_SECONDS,
        **await service.snapshot(session, user),
    )
