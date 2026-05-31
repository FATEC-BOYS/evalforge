from datetime import datetime

from sqlalchemy import BINARY, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid7 import uuid7


class BaseEntity(DeclarativeBase):
    __abstract__ = True

    id: Mapped[bytes] = mapped_column(
        BINARY(16),
        primary_key=True,
        default=lambda: uuid7().bytes,
    )
    public_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid7()),
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
