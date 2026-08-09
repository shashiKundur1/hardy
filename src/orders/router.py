from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from src.auth.dependencies import CurrentUser
from src.catalog import service as catalog
from src.catalog.constants import CATEGORY_LABELS
from src.catalog.schemas import ProductId
from src.constants import EventType, TriggerReason, Wear
from src.database import SessionDep
from src.events import service as events
from src.events.schemas import IncomingEvent
from src.orders import service
from src.orders.constants import CART_KEY, MAX_REPORT_NOTE, WEAR_LABELS
from src.orders.schemas import CartLine
from src.recommendations import service as recommendations
from src.redirects import safe_path
from src.rendering import page

router = APIRouter(tags=["orders"])

AS_A_PAGE = {
    status.HTTP_303_SEE_OTHER: {
        "description": "Signed-out visitors are sent to sign in",
        "content": {"text/html": {}},
    },
    status.HTTP_404_NOT_FOUND: {
        "description": "Nothing lives at this address",
        "content": {"text/html": {}},
    },
}


def basket_of(request: Request) -> dict[int, int]:
    return service.normalise(request.session.get(CART_KEY))


def keep(request: Request, basket: dict[int, int]) -> None:
    request.session[CART_KEY] = {str(key): value for key, value in basket.items()}


@router.get("/cart", response_class=HTMLResponse, responses=AS_A_PAGE)
async def cart(request: Request, session: SessionDep, user: CurrentUser) -> HTMLResponse:
    lines = await service.contents(session, basket_of(request))
    return page(
        request,
        "cart.html",
        user=user,
        categories=await catalog.navigation(session),
        lines=lines,
        total=service.total_of(lines),
        yearly=service.yearly_of(lines),
    )


@router.post("/cart/add")
async def add_to_cart(
    request: Request,
    session: SessionDep,
    user: CurrentUser,
    product_id: Annotated[int, Form()],
    quantity: Annotated[int, Form()] = 1,
    back: Annotated[str, Form()] = "",
) -> RedirectResponse:
    line = CartLine(product_id=product_id, quantity=quantity)
    found = await catalog.by_id(session, line.product_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such product")
    keep(request, service.add(basket_of(request), line.product_id, line.quantity))
    await events.record(
        user.id,
        [
            IncomingEvent(
                type=EventType.ADD_TO_CART,
                product_id=found.id,
                category=found.category,
            )
        ],
    )
    target = safe_path(back, "/cart")
    joiner = "&" if "?" in target else "?"
    return RedirectResponse(f"{target}{joiner}added={found.id}", status.HTTP_303_SEE_OTHER)


@router.post("/cart/remove")
async def remove_from_cart(
    request: Request, user: CurrentUser, product_id: Annotated[int, Form()]
) -> RedirectResponse:
    keep(request, service.remove(basket_of(request), product_id))
    return RedirectResponse("/cart", status.HTTP_303_SEE_OTHER)


@router.post("/checkout")
async def checkout(request: Request, session: SessionDep, user: CurrentUser) -> RedirectResponse:
    order = await service.place(session, user.id, basket_of(request))
    request.session.pop(CART_KEY, None)
    await events.record(
        user.id,
        [
            IncomingEvent(
                type=EventType.PURCHASE, product_id=line.product_id, category=line.category
            )
            for line in order.lines
        ],
    )
    await recommendations.refresh(user.id, TriggerReason.INTEREST_SHIFT)
    return RedirectResponse(f"/orders/{order.id}", status.HTTP_303_SEE_OTHER)


@router.get("/orders", response_class=HTMLResponse, responses=AS_A_PAGE)
async def orders(request: Request, session: SessionDep, user: CurrentUser) -> HTMLResponse:
    return page(
        request,
        "orders.html",
        user=user,
        categories=await catalog.navigation(session),
        orders=await service.history(session, user.id),
    )


@router.get("/orders/{order_id}", response_class=HTMLResponse, responses=AS_A_PAGE)
async def order_detail(
    request: Request, session: SessionDep, user: CurrentUser, order_id: ProductId
) -> HTMLResponse:
    found = await service.by_id(session, user.id, order_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such order")
    return page(
        request,
        "order.html",
        user=user,
        categories=await catalog.navigation(session),
        order=found,
        labels=CATEGORY_LABELS,
    )


@router.get("/shelf", response_class=HTMLResponse, responses=AS_A_PAGE)
async def shelf(request: Request, session: SessionDep, user: CurrentUser) -> HTMLResponse:
    return page(
        request,
        "shelf.html",
        user=user,
        categories=await catalog.navigation(session),
        owned=await service.shelf(session, user.id),
        labels=CATEGORY_LABELS,
        wear_labels=WEAR_LABELS,
    )


@router.post("/shelf/report")
async def report(
    session: SessionDep,
    user: CurrentUser,
    product_id: Annotated[int, Form()],
    verdict: Annotated[Wear, Form()],
    note: Annotated[str, Form()] = "",
) -> RedirectResponse:
    if not await service.owns(session, user.id, product_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only an owner can report on how a thing is holding up"
        )
    await service.report(session, user.id, product_id, verdict, note.strip()[:MAX_REPORT_NOTE])
    return RedirectResponse("/shelf", status.HTTP_303_SEE_OTHER)
