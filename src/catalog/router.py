from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse

from src.auth.dependencies import AdminUser
from src.catalog import service
from src.catalog.schemas import Consistency, ProductRead, ProductWrite
from src.database import SessionDep
from src.rendering import page

router = APIRouter(prefix="/admin", tags=["admin"])
api_router = APIRouter(prefix="/api/admin", tags=["admin"])


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


@api_router.get("/consistency")
async def consistency(session: SessionDep, user: AdminUser) -> Consistency:
    return Consistency(**await service.consistency(session))


@api_router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product(
    session: SessionDep, user: AdminUser, data: ProductWrite
) -> ProductRead:
    return ProductRead.model_validate(await service.create(session, data))


@api_router.put("/products/{product_id}")
async def replace_product(
    session: SessionDep, user: AdminUser, product_id: int, data: ProductWrite
) -> ProductRead:
    product = await service.replace(session, product_id, data)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such product")
    return ProductRead.model_validate(product)


@api_router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product(
    session: SessionDep, user: AdminUser, product_id: int
) -> Response:
    if not await service.remove(session, product_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such product")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_router.post("/resync")
async def resync(session: SessionDep, user: AdminUser) -> Consistency:
    await service.resync_all(session)
    return Consistency(**await service.consistency(session))
