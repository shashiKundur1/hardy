from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.catalog.models import Product
from src.database import utcnow
from src.orders.constants import (
    CARE_INTERVALS,
    DAYS_PER_MONTH,
    DEFAULT_CARE,
    MAX_CART_LINES,
    MAX_LINE_QUANTITY,
    ORDER_HISTORY,
)
from src.orders.exceptions import CartFull, NothingToBuy
from src.orders.models import Order, OrderLine, OwnerReport


def normalise(raw: object) -> dict[int, int]:
    if not isinstance(raw, dict):
        return {}
    kept: dict[int, int] = {}
    for key, value in raw.items():
        try:
            product_id, quantity = int(key), int(value)
        except (TypeError, ValueError):
            continue
        if product_id >= 1 and quantity >= 1:
            kept[product_id] = min(quantity, MAX_LINE_QUANTITY)
    return kept


def add(basket: dict[int, int], product_id: int, quantity: int) -> dict[int, int]:
    if product_id not in basket and len(basket) >= MAX_CART_LINES:
        raise CartFull()
    held = basket.get(product_id, 0)
    return basket | {product_id: min(held + quantity, MAX_LINE_QUANTITY)}


def remove(basket: dict[int, int], product_id: int) -> dict[int, int]:
    return {key: value for key, value in basket.items() if key != product_id}


def set_quantity(basket: dict[int, int], product_id: int, quantity: int) -> dict[int, int]:
    if product_id not in basket:
        return basket
    if quantity < 1:
        return remove(basket, product_id)
    return basket | {product_id: min(quantity, MAX_LINE_QUANTITY)}


async def contents(session: AsyncSession, basket: dict[int, int]) -> list[dict]:
    if not basket:
        return []
    found = await session.scalars(select(Product).where(Product.id.in_(basket)))
    return [
        {"product": product, "quantity": basket[product.id]}
        for product in sorted(found, key=lambda item: item.title)
    ]


def total_of(lines: list[dict]) -> Decimal:
    return sum((line["product"].price * line["quantity"] for line in lines), Decimal(0))


def yearly_of(lines: list[dict]) -> Decimal:
    return sum((line["product"].cost_per_year * line["quantity"] for line in lines), Decimal(0))


async def place(session: AsyncSession, user_id: int, basket: dict[int, int]) -> Order:
    lines = await contents(session, basket)
    if not lines:
        raise NothingToBuy()
    order = Order(user_id=user_id, total=total_of(lines))
    order.lines = [
        OrderLine(
            product_id=line["product"].id,
            title=line["product"].title,
            brand=line["product"].brand,
            category=line["product"].category,
            image_url=line["product"].image_url,
            price=line["product"].price,
            expected_life_years=line["product"].expected_life_years,
            warranty=line["product"].warranty,
            quantity=line["quantity"],
        )
        for line in lines
    ]
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def history(session: AsyncSession, user_id: int) -> list[Order]:
    statement = (
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .limit(ORDER_HISTORY)
    )
    return list(await session.scalars(statement))


async def by_id(session: AsyncSession, user_id: int, order_id: int) -> Order | None:
    return await session.scalar(select(Order).where(Order.id == order_id, Order.user_id == user_id))


def years_owned(bought_on: date | None) -> float:
    if bought_on is None:
        return 0.0
    return round((utcnow().date() - bought_on).days / 365.25, 1)


async def shelf(session: AsyncSession, user_id: int) -> list[dict]:
    owned: dict[int, dict] = {}
    for order in await history(session, user_id):
        for line in order.lines:
            held = owned.get(line.product_id)
            if held is None:
                owned[line.product_id] = {
                    "line": line,
                    "quantity": line.quantity,
                    "bought_on": order.created_at.date(),
                }
                continue
            held["quantity"] += line.quantity
            held["bought_on"] = min(held["bought_on"], order.created_at.date())
    verdicts = await reports_for(session, user_id)
    for product_id, entry in owned.items():
        entry["years_owned"] = years_owned(entry["bought_on"])
        entry["life_used"] = min(1.0, entry["years_owned"] / entry["line"].expected_life_years)
        entry["care"] = care_for(entry["line"].category, entry["bought_on"])
        entry["report"] = verdicts.get(product_id)
    return sorted(owned.values(), key=lambda entry: entry["bought_on"], reverse=True)


def care_for(category: str, bought_on: date) -> dict:
    months, task = CARE_INTERVALS.get(category, DEFAULT_CARE)
    span = months * DAYS_PER_MONTH
    elapsed = max(0, (utcnow().date() - bought_on).days)
    return {
        "months": months,
        "task": task,
        "due_in_days": round(span - (elapsed % span)),
        "services_due": int(elapsed // span),
    }


async def reports_for(session: AsyncSession, user_id: int) -> dict[int, OwnerReport]:
    rows = await session.scalars(
        select(OwnerReport)
        .where(OwnerReport.user_id == user_id)
        .order_by(OwnerReport.created_at.desc(), OwnerReport.id.desc())
    )
    latest: dict[int, OwnerReport] = {}
    for row in rows:
        latest.setdefault(row.product_id, row)
    return latest


async def owns(session: AsyncSession, user_id: int, product_id: int) -> bool:
    for order in await history(session, user_id):
        if any(line.product_id == product_id for line in order.lines):
            return True
    return False


async def report(
    session: AsyncSession, user_id: int, product_id: int, verdict: str, note: str
) -> OwnerReport:
    row = OwnerReport(user_id=user_id, product_id=product_id, verdict=verdict, note=note or None)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row
