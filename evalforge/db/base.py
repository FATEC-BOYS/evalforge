import uuid as _uuid
from datetime import datetime

from sqlalchemy import BINARY, String, event, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseEntity(DeclarativeBase):
    __abstract__ = True

    id: Mapped[bytes] = mapped_column(
        BINARY(16),
        primary_key=True,
        default=lambda: _uuid.uuid4().bytes,
    )
    public_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(_uuid.uuid4()),
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


@event.listens_for(BaseEntity, "init", propagate=True)
def _set_pk_defaults(target, args, kwargs):
    if "id" not in kwargs:
        kwargs["id"] = _uuid.uuid4().bytes
    if "public_id" not in kwargs:
        kwargs["public_id"] = str(_uuid.uuid4())
