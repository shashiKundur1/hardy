from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (Index("idx_events_user_time", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    batch: Mapped[str] = mapped_column(String(32), index=True)
    type: Mapped[str] = mapped_column(String(20))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    category: Mapped[str | None] = mapped_column(String(40))
    query: Mapped[str | None] = mapped_column(String(200))
    dwell_ms: Mapped[int | None]
    payload: Mapped[str | None] = mapped_column("metadata", Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
