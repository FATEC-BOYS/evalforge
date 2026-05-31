from sqlalchemy import Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import BaseEntity
from infra.exceptions import EvalException

_IMMUTABLE_ERROR = EvalException(
    message="Audit log is immutable — records cannot be modified or deleted",
    context={"table": "audit_logs"},
)


class AuditLogEntity(BaseEntity):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_user_public_id", "user_public_id"),)

    user_public_id: Mapped[str] = mapped_column(String(255), nullable=False)
    request_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    security_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def update(self, *args, **kwargs):
        raise _IMMUTABLE_ERROR

    def delete(self, *args, **kwargs):
        raise _IMMUTABLE_ERROR
