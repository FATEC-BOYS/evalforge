from sqlalchemy import String

from db.base import BaseEntity
from db.entities.evaluation import EvaluationEntity

_REQUIRED_COLUMNS = [
    "task",
    "input",
    "model",
    "response",
    "accuracy_score",
    "accuracy_justification",
    "reasoning_score",
    "reasoning_justification",
    "safety_score",
    "safety_justification",
    "latency_ms",
    "verdict",
]


def test_evaluation_entity_table_name():
    assert EvaluationEntity.__tablename__ == "evaluations"


def test_evaluation_entity_has_required_columns():
    column_names = {col.name for col in EvaluationEntity.__table__.columns}
    for col in _REQUIRED_COLUMNS:
        assert col in column_names, f"Missing column: {col}"


def test_verdict_column_length():
    verdict_col = EvaluationEntity.__table__.columns["verdict"]
    assert isinstance(verdict_col.type, String)
    assert verdict_col.type.length == 4


def test_evaluation_entity_inherits_base():
    assert issubclass(EvaluationEntity, BaseEntity)
