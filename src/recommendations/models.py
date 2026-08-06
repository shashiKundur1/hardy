from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class TriggerDecision(Base):
    __tablename__ = "trigger_decisions"
    __table_args__ = (Index("idx_decisions_user", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    fired: Mapped[bool] = mapped_column(Boolean)
    trigger_reason: Mapped[str | None] = mapped_column(String(20))
    suppression_reason: Mapped[str | None] = mapped_column(String(20))
    profile_hash: Mapped[str] = mapped_column(String(64))
    catalog_version: Mapped[str] = mapped_column(String(64))
    events_considered: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (Index("idx_recs_user", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    narrative: Mapped[str] = mapped_column(Text)
    product_ids: Mapped[str] = mapped_column(Text)
    interest_profile: Mapped[str] = mapped_column(Text)
    trigger_reason: Mapped[str] = mapped_column(String(20))
    profile_hash: Mapped[str] = mapped_column(String(64))
    events_covered: Mapped[int]
    model_used: Mapped[str] = mapped_column(String(80))
    tokens_used: Mapped[int | None]
    latency_ms: Mapped[int | None]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
