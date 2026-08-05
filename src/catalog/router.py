from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.auth.dependencies import AdminUser
from src.catalog import service
from src.database import SessionDep
from src.rendering import page

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("")
async def overview(request: Request, session: SessionDep, user: AdminUser) -> HTMLResponse:
    return page(
        request,
        "admin.html",
        user=user,
        categories=await service.navigation(session),
        product_count=await service.count(session),
        sourced=await service.sourced_count(session),
    )
