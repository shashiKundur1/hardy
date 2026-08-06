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
from src.database import SessionDep
from src.recommendations import service as recommendations
from src.rendering import page

router = APIRouter(tags=["storefront"])


@router.get("/")
async def home(request: Request, session: SessionDep, user: OptionalUser) -> HTMLResponse:
    return page(
        request,
        "home.html",
        user=user,
        categories=await catalog.navigation(session),
        featured=await catalog.featured(session, FEATURED_LIMIT),
        catalog_size=await catalog.count(session),
        sourced=await catalog.sourced_count(session),
        recommendation=await recommendations.active_for(session, user.id) if user else None,
    )


@router.get("/category/{slug}")
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


@router.get("/product/{product_id}")
async def product(
    request: Request, session: SessionDep, user: OptionalUser, product_id: int
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


@router.get("/search")
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


@router.get("/recommendations")
async def advice(request: Request, session: SessionDep, user: OptionalUser) -> HTMLResponse:
    return page(
        request,
        "recommendations.html",
        user=user,
        categories=await catalog.navigation(session),
        recommendation=await recommendations.active_for(session, user.id) if user else None,
    )
