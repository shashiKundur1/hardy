import json
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from src.auth import service as accounts
from src.auth.dependencies import CurrentUser, OptionalUser
from src.catalog import service as catalog
from src.catalog.constants import (
    CATEGORY_BLURBS,
    CATEGORY_LABELS,
    FEATURED_LIMIT,
    LIFE_FLOORS,
    PAGE_SIZE,
    RATE_CEILINGS,
    RELATED_LIMIT,
    SEARCH_LIMIT,
    SORT_LABELS,
)
from src.catalog.schemas import BrowseQuery, ProductId
from src.database import SessionDep
from src.debug import service as debug
from src.events import service as events
from src.events.constants import FOOTPRINT_LIMIT
from src.recommendations import service as recommendations
from src.recommendations.constants import DISMISSED_KEY, NUDGE_PICKS, TRIGGER_PHRASES
from src.redirects import safe_path
from src.rendering import page

router = APIRouter(tags=["storefront"])

NEEDS_SIGN_IN = {
    status.HTTP_303_SEE_OTHER: {
        "description": "Signed-out visitors are sent to sign in and returned here after",
        "content": {"text/html": {}},
    },
}

AS_A_PAGE = NEEDS_SIGN_IN | {
    status.HTTP_404_NOT_FOUND: {
        "description": "Nothing lives at this address",
        "content": {"text/html": {}},
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "description": "Part of that request could not be read",
        "content": {"text/html": {}},
    },
}

BrowseParams = Depends(BrowseQuery)


async def in_context(request: Request, session, user) -> dict:
    active = await recommendations.active_for(session, user.id)
    if active is None or request.session.get(DISMISSED_KEY) == active.id:
        return {"nudge": None, "nudge_picks": [], "nudge_because": ""}
    picks = await recommendations.products_for(session, active)
    return {
        "nudge": active,
        "nudge_picks": picks[:NUDGE_PICKS],
        "nudge_because": TRIGGER_PHRASES.get(active.trigger_reason, "what you have been reading"),
    }


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request, session: SessionDep, user: OptionalUser) -> HTMLResponse:
    return page(
        request,
        "landing.html",
        user=user,
        catalog_size=await catalog.count(session),
        sourced=await catalog.sourced_count(session),
        labels=CATEGORY_LABELS,
    )


@router.get("/shop", response_class=HTMLResponse, responses=NEEDS_SIGN_IN)
async def shop(request: Request, session: SessionDep, user: CurrentUser) -> HTMLResponse:
    active = await recommendations.active_for(session, user.id)
    return page(
        request,
        "shop.html",
        user=user,
        categories=await catalog.navigation(session),
        featured=await catalog.featured(session, FEATURED_LIMIT),
        catalog_size=await catalog.count(session),
        sourced=await catalog.sourced_count(session),
        interests=accounts.declared_interests(user),
        labels=CATEGORY_LABELS,
        recommendation=active,
        chosen=await recommendations.products_for(session, active) if active else [],
    )


@router.get("/category/{slug}", response_class=HTMLResponse, responses=AS_A_PAGE)
async def category(
    request: Request,
    session: SessionDep,
    user: CurrentUser,
    slug: str,
    query: BrowseQuery = BrowseParams,
) -> HTMLResponse:
    if slug not in CATEGORY_LABELS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such category")
    products, total = await catalog.browse(session, slug, query)
    return page(
        request,
        "category.html",
        user=user,
        categories=await catalog.navigation(session),
        slug=slug,
        label=CATEGORY_LABELS[slug],
        blurb=CATEGORY_BLURBS[slug],
        products=products,
        total=total,
        query=query,
        pages=max(1, -(-total // PAGE_SIZE)),
        sort_labels=SORT_LABELS,
        life_floors=LIFE_FLOORS,
        rate_ceilings=RATE_CEILINGS,
        **await in_context(request, session, user),
    )


@router.get("/product/{product_id}", response_class=HTMLResponse, responses=AS_A_PAGE)
async def product(
    request: Request, session: SessionDep, user: CurrentUser, product_id: ProductId
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
        **await in_context(request, session, user),
    )


@router.get("/search", response_class=HTMLResponse, responses=NEEDS_SIGN_IN)
async def search(
    request: Request, session: SessionDep, user: CurrentUser, q: str = ""
) -> HTMLResponse:
    query = q.strip()
    return page(
        request,
        "search.html",
        user=user,
        categories=await catalog.navigation(session),
        query=query,
        results=await catalog.search(session, query, SEARCH_LIMIT) if query else [],
        **await in_context(request, session, user),
    )


@router.get("/recommendations", response_class=HTMLResponse, responses=NEEDS_SIGN_IN)
async def advice(request: Request, session: SessionDep, user: CurrentUser) -> HTMLResponse:
    active = await recommendations.active_for(session, user.id)
    return page(
        request,
        "recommendations.html",
        user=user,
        categories=await catalog.navigation(session),
        recommendation=active,
        chosen=await recommendations.products_for(session, active) if active else [],
        reasons=recommendations.reasons_for(active) if active else {},
    )


@router.get("/profile", response_class=HTMLResponse, responses=NEEDS_SIGN_IN)
async def profile(request: Request, session: SessionDep, user: CurrentUser) -> HTMLResponse:
    return page(
        request,
        "profile.html",
        user=user,
        categories=await catalog.navigation(session),
        interests=accounts.declared_interests(user),
        labels=CATEGORY_LABELS,
        events_recorded=await events.count_for(session, user.id),
        recommendation=await recommendations.active_for(session, user.id),
    )


@router.get("/footprint", response_class=HTMLResponse, responses=NEEDS_SIGN_IN)
async def footprint(request: Request, session: SessionDep, user: CurrentUser) -> HTMLResponse:
    active = await recommendations.active_for(session, user.id)
    return page(
        request,
        "footprint.html",
        user=user,
        categories=await catalog.navigation(session),
        summary=await events.summary_for(session, user.id),
        batches=debug.batches(await events.recent_for(session, user.id, FOOTPRINT_LIMIT)),
        total=await events.count_for(session, user.id),
        recommendation=active,
        intent=json.loads(active.interest_profile) if active else {},
    )


@router.post("/footprint/forget")
async def forget(session: SessionDep, user: CurrentUser) -> RedirectResponse:
    await events.forget(session, user.id)
    await recommendations.forget(session, user.id)
    return RedirectResponse("/footprint", status.HTTP_303_SEE_OTHER)


@router.post("/recommendations/dismiss")
async def dismiss(
    request: Request,
    session: SessionDep,
    user: CurrentUser,
    back: Annotated[str, Form()] = "",
) -> RedirectResponse:
    active = await recommendations.active_for(session, user.id)
    if active is not None:
        request.session[DISMISSED_KEY] = active.id
    return RedirectResponse(safe_path(back), status.HTTP_303_SEE_OTHER)
