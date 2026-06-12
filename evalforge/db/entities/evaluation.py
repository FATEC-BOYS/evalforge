from sqlalchemy import Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import BaseEntity


class EvaluationEntity(BaseEntity):
    __tablename__ = "evaluations"

    task: Mapped[str] = mapped_column(Text, nullable=False)
    input: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    scores_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    verdict: Mapped[str] = mapped_column(String(4), nullable=False)
