import asyncio
import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from src.catalog.models import Product
from src.constants import CATEGORIES, Ownership
from src.database import create_schema, session_factory
from src.integrations import mesh

SEED_FILE = Path(__file__).parent / "seed_products.json"
IMAGE_DIR = Path(__file__).parent.parent / "src/static/img/products"
PER_CATEGORY = 17

INSTRUCTION = """You are compiling a product catalog for a storefront that argues for durable goods
from evidence. Return {count} real, currently-purchasable products in the "{category}" category.

Rules that matter more than completeness:
- Use real brands and real product lines. No invented brands, no invented model names.
- price_inr is the approximate Indian retail price in whole rupees.
- expected_life_years is a realistic service life for a well-maintained example.
- repairability_score is 0-10. Use null unless you have a genuine basis for the number.
- parts_until is the year spare parts are plausibly available. Use null if you do not know.
- ownership_type is one of: family, employee, trust, public, conglomerate, private_equity, unknown.
- ownership_note and evidence_source: ONLY fill these when you are confident of a real, checkable
  public fact and can name the source as a URL or a named publication. If you are not confident,
  set ownership_type to "unknown" and leave both null. A wrong ownership claim is worse than no
  claim. Do not guess. Do not invent URLs.

Return JSON only, shaped as {{"products": [...]}}, where each product has:
title, brand, description, price_inr, expected_life_years, repairability_score, parts_until,
warranty, ownership_type, ownership_note, evidence_source."""


def cleaned(raw: dict, category: str) -> dict | None:
    title = (raw.get("title") or "").strip()
    brand = (raw.get("brand") or "").strip()
    price = raw.get("price_inr")
    life = raw.get("expected_life_years")
    if not title or not brand or not price or not life:
        return None

    ownership = str(raw.get("ownership_type") or Ownership.UNKNOWN).strip().lower()
    if ownership not in set(Ownership):
        ownership = Ownership.UNKNOWN
    note = (raw.get("ownership_note") or "").strip() or None
    source = (raw.get("evidence_source") or "").strip() or None
    if not source or not note:
        note = source = None
        if ownership != Ownership.UNKNOWN:
            ownership = Ownership.UNKNOWN

    return {
        "title": title,
        "brand": brand,
        "description": (raw.get("description") or "").strip(),
        "category": category,
        "price": float(price),
        "expected_life_years": int(life),
        "repairability_score": raw.get("repairability_score"),
        "parts_until": raw.get("parts_until"),
        "warranty": (raw.get("warranty") or "").strip() or None,
        "ownership_type": ownership,
        "ownership_note": note,
        "evidence_source": source,
    }


async def generate() -> list[dict]:
    products: list[dict] = []
    for category in CATEGORIES:
        completion = await mesh.chat(
            [
                {
                    "role": "user",
                    "content": INSTRUCTION.format(count=PER_CATEGORY, category=category),
                }
            ],
            response_format={"type": "json_object"},
        )
        batch = json.loads(completion.content).get("products", [])
        kept = [item for item in (cleaned(raw, category) for raw in batch) if item]
        products.extend(kept)
        print(f"{category:20} {len(kept):3} products  ({completion.usage.total_tokens} tokens)")
    return products


async def load(products: list[dict]) -> tuple[int, int]:
    await create_schema()
    created = updated = 0
    async with session_factory() as session:
        for item in products:
            existing = await session.scalar(
                select(Product).where(
                    Product.title == item["title"], Product.brand == item["brand"]
                )
            )
            target = existing or Product()
            for field, value in item.items():
                setattr(target, field, Decimal(str(value)) if field == "price" else value)
            if existing is None:
                session.add(target)
                created += 1
            else:
                updated += 1
        await session.commit()
    return created, updated


async def link_images() -> int:
    linked = 0
    async with session_factory() as session:
        for product in await session.scalars(select(Product)):
            if (IMAGE_DIR / f"{product.id}.webp").exists():
                product.image_url = f"/static/img/products/{product.id}.webp"
                linked += 1
        await session.commit()
    return linked


async def main() -> None:
    if SEED_FILE.exists():
        products = json.loads(SEED_FILE.read_text())
        print(f"loaded {len(products)} products from {SEED_FILE.name}")
    else:
        products = await generate()
        SEED_FILE.write_text(json.dumps(products, indent=2, ensure_ascii=False))
        print(f"wrote {len(products)} products to {SEED_FILE.name}")

    created, updated = await load(products)
    sourced = sum(1 for item in products if item["evidence_source"])
    print(f"{created} created, {updated} updated, {sourced} with sourced ownership")
    print(f"{await link_images()} products linked to an image")


if __name__ == "__main__":
    asyncio.run(main())
