from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.constants import Ownership
from src.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (Index("idx_products_category", "category"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(40))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    expected_life_years: Mapped[int] = mapped_column(Integer)
    ownership_type: Mapped[str] = mapped_column(String(20), default=Ownership.UNKNOWN)
    ownership_since: Mapped[date | None] = mapped_column(Date)
    ownership_note: Mapped[str | None] = mapped_column(Text)
    evidence_source: Mapped[str | None] = mapped_column(Text)
    repairability_score: Mapped[float | None]
    parts_until: Mapped[int | None]
    warranty: Mapped[str | None] = mapped_column(String(120))
    image_url: Mapped[str | None] = mapped_column(Text)
    vector_synced_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    @property
    def cost_per_year(self) -> Decimal:
        return self.price / self.expected_life_years
