from db.base import BaseEntity
from db.entities.evaluation import EvaluationEntity


def _column_names():
    return {col.name for col in EvaluationEntity.__table__.columns}


def _make_entity(**kwargs):
    defaults = dict(
        task="t",
        input="i",
        model="m",
        response="r",
        scores_json={"accuracy": {"score": 9.0, "justification": "ok"}},
        latency_ms=100.0,
        verdict="PASS",
    )
    return EvaluationEntity(**{**defaults, **kwargs})


def test_base_entity_has_id_field():
    assert "id" in _column_names()


def test_base_entity_has_public_id_field():
    assert "public_id" in _column_names()


def test_base_entity_has_created_at_field():
    assert "created_at" in _column_names()


def test_base_entity_has_updated_at_field():
    assert "updated_at" in _column_names()


def test_public_id_is_generated_automatically():
    entity = _make_entity()
    assert entity.public_id is not None
    assert len(entity.public_id) > 0


def test_id_is_bytes():
    entity = _make_entity()
    assert isinstance(entity.id, bytes)
    assert len(entity.id) == 16


def test_public_id_is_string():
    entity = _make_entity()
    assert isinstance(entity.public_id, str)
