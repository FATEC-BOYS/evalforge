from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import BaseEntity


class UserEntity(BaseEntity):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, server_default="false", default=False, nullable=False)
