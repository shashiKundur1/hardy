from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.constants import Role
from src.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(60))
    role: Mapped[str] = mapped_column(String(16), default=Role.USER)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
