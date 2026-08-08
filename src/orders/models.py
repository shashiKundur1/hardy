from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (Index("idx_orders_user", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    lines: Mapped[list["OrderLine"]] = relationship(
        back_populates="order", lazy="selectin", cascade="all, delete-orphan"
    )

    @property
    def cost_per_year(self) -> Decimal:
        return sum((line.cost_per_year * line.quantity for line in self.lines), Decimal(0))


class OrderLine(Base):
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    title: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(40))
    image_url: Mapped[str | None] = mapped_column(String(300))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    expected_life_years: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    order: Mapped[Order] = relationship(back_populates="lines")

    @property
    def cost_per_year(self) -> Decimal:
        return self.price / self.expected_life_years
