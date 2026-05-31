from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import BaseEntity


class EvaluationEntity(BaseEntity):
    __tablename__ = "evaluations"

    task: Mapped[str] = mapped_column(Text, nullable=False)
    input: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)

    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_justification: Mapped[str] = mapped_column(Text, nullable=False)

    reasoning_score: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning_justification: Mapped[str] = mapped_column(Text, nullable=False)

    safety_score: Mapped[float] = mapped_column(Float, nullable=False)
    safety_justification: Mapped[str] = mapped_column(Text, nullable=False)

    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    verdict: Mapped[str] = mapped_column(String(4), nullable=False)
