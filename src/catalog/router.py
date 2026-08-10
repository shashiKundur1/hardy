from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse

from src.auth.dependencies import AdminUser
from src.catalog import service, uploads
from src.catalog.constants import ADMIN_PAGE_SIZE
from src.catalog.models import Product
from src.catalog.schemas import Consistency, ProductId, ProductRead, ProductWrite, Upload
from src.constants import CATEGORIES, Ownership
from src.database import SessionDep
from src.rendering import page

router = APIRouter(prefix="/admin", tags=["admin"])
api_router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("", response_class=HTMLResponse)
async def overview(
    request: Request, session: SessionDep, user: AdminUser, page_number: int = 1
) -> HTMLResponse:
    offset = max(page_number - 1, 0) * ADMIN_PAGE_SIZE
    total = await service.count(session)
    return page(
        request,
        "admin.html",
        user=user,
        categories=await service.navigation(session),
        product_count=total,
        sourced=await service.sourced_count(session),
        consistency=await service.consistency(session),
        products=await service.page_of(session, offset, ADMIN_PAGE_SIZE),
        page_number=max(page_number, 1),
        page_count=max((total + ADMIN_PAGE_SIZE - 1) // ADMIN_PAGE_SIZE, 1),
    )


@router.get("/products/new", response_class=HTMLResponse)
async def new_form(request: Request, session: SessionDep, user: AdminUser) -> HTMLResponse:
    return page(
        request,
        "admin_product.html",
        user=user,
        categories=await service.navigation(session),
        product=Product(ownership_type=Ownership.UNKNOWN),
        ownerships=[option.value for option in Ownership],
        slugs=CATEGORIES,
    )


@router.post("/products")
async def create_from_form(
    session: SessionDep, user: AdminUser, form: Annotated[ProductWrite, Form()]
) -> RedirectResponse:
    await service.create(session, form)
    return RedirectResponse("/admin", status.HTTP_303_SEE_OTHER)


@router.get("/products/{product_id}", response_class=HTMLResponse)
async def edit_form(
    request: Request, session: SessionDep, user: AdminUser, product_id: ProductId
) -> HTMLResponse:
    product = await service.by_id(session, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such product")
    return page(
        request,
        "admin_product.html",
        user=user,
        categories=await service.navigation(session),
        product=product,
        ownerships=[option.value for option in Ownership],
        slugs=CATEGORIES,
    )


@router.post("/products/{product_id}")
async def save_product(
    session: SessionDep,
    user: AdminUser,
    product_id: ProductId,
    form: Annotated[ProductWrite, Form()],
) -> RedirectResponse:
    if await service.replace(session, product_id, form) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such product")
    return RedirectResponse("/admin", status.HTTP_303_SEE_OTHER)


@router.post("/products/{product_id}/delete")
async def delete_product(
    session: SessionDep, user: AdminUser, product_id: ProductId
) -> RedirectResponse:
    if not await service.remove(session, product_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such product")
    return RedirectResponse("/admin", status.HTTP_303_SEE_OTHER)


@router.post("/resync")
async def resync_from_form(session: SessionDep, user: AdminUser) -> RedirectResponse:
    await service.resync_all(session)
    return RedirectResponse("/admin", status.HTTP_303_SEE_OTHER)


@api_router.get("/consistency")
async def consistency(session: SessionDep, user: AdminUser) -> Consistency:
    return Consistency(**await service.consistency(session))


@api_router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product(session: SessionDep, user: AdminUser, data: ProductWrite) -> ProductRead:
    return ProductRead.model_validate(await service.create(session, data))


@api_router.put("/products/{product_id}")
async def replace_product(
    session: SessionDep, user: AdminUser, product_id: ProductId, data: ProductWrite
) -> ProductRead:
    product = await service.replace(session, product_id, data)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such product")
    return ProductRead.model_validate(product)


@api_router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product(session: SessionDep, user: AdminUser, product_id: ProductId) -> Response:
    if not await service.remove(session, product_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such product")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_router.post("/uploads", status_code=status.HTTP_201_CREATED)
async def upload_image(user: AdminUser, file: Annotated[UploadFile, File()]) -> Upload:
    return Upload(image_url=await uploads.store(file))


@api_router.post("/resync")
async def resync(session: SessionDep, user: AdminUser) -> Consistency:
    await service.resync_all(session)
    return Consistency(**await service.consistency(session))
