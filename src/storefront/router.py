from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from src.auth.dependencies import OptionalUser
from src.catalog import service as catalog
from src.catalog.constants import (
    CATEGORY_BLURBS,
    CATEGORY_LABELS,
    FEATURED_LIMIT,
    PAGE_SIZE,
    RELATED_LIMIT,
    SEARCH_LIMIT,
)
from src.catalog.schemas import ProductId
from src.database import SessionDep
from src.recommendations import service as recommendations
from src.rendering import page

router = APIRouter(tags=["storefront"])

AS_A_PAGE = {
    status.HTTP_404_NOT_FOUND: {
        "description": "Nothing lives at this address",
        "content": {"text/html": {}},
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "description": "Part of that request could not be read",
        "content": {"text/html": {}},
    },
}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, session: SessionDep, user: OptionalUser) -> HTMLResponse:
    active = await recommendations.active_for(session, user.id) if user else None
    return page(
        request,
        "home.html",
        user=user,
        categories=await catalog.navigation(session),
        featured=await catalog.featured(session, FEATURED_LIMIT),
        catalog_size=await catalog.count(session),
        sourced=await catalog.sourced_count(session),
        recommendation=active,
        chosen=await recommendations.products_for(session, active) if active else [],
    )


@router.get("/category/{slug}", response_class=HTMLResponse, responses=AS_A_PAGE)
async def category(
    request: Request, session: SessionDep, user: OptionalUser, slug: str
) -> HTMLResponse:
    if slug not in CATEGORY_LABELS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such category")
    return page(
        request,
        "category.html",
        user=user,
        categories=await catalog.navigation(session),
        slug=slug,
        label=CATEGORY_LABELS[slug],
        blurb=CATEGORY_BLURBS[slug],
        products=await catalog.by_category(session, slug, PAGE_SIZE),
    )


@router.get("/product/{product_id}", response_class=HTMLResponse, responses=AS_A_PAGE)
async def product(
    request: Request, session: SessionDep, user: OptionalUser, product_id: ProductId
) -> HTMLResponse:
    found = await catalog.by_id(session, product_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such product")
    return page(
        request,
        "product.html",
        user=user,
        categories=await catalog.navigation(session),
        product=found,
        label=CATEGORY_LABELS[found.category],
        related=await catalog.related(session, found, RELATED_LIMIT),
    )


@router.get("/search", response_class=HTMLResponse)
async def search(
    request: Request, session: SessionDep, user: OptionalUser, q: str = ""
) -> HTMLResponse:
    query = q.strip()
    return page(
        request,
        "search.html",
        user=user,
        categories=await catalog.navigation(session),
        query=query,
        results=await catalog.search(session, query, SEARCH_LIMIT) if query else [],
    )


@router.get("/recommendations", response_class=HTMLResponse)
async def advice(request: Request, session: SessionDep, user: OptionalUser) -> HTMLResponse:
    active = await recommendations.active_for(session, user.id) if user else None
    return page(
        request,
        "recommendations.html",
        user=user,
        categories=await catalog.navigation(session),
        recommendation=active,
        chosen=await recommendations.products_for(session, active) if active else [],
        reasons=recommendations.reasons_for(active) if active else {},
    )
