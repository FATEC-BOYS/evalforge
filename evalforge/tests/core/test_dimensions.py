import pytest
from pydantic import ValidationError

from core.dimensions import DIMENSIONS, EvalDimension


def _find(name: str) -> EvalDimension:
    return next(d for d in DIMENSIONS if d.name == name)


def test_dimensions_list_has_three_items():
    assert len(DIMENSIONS) == 3


def test_dimensions_are_immutable():
    assert isinstance(DIMENSIONS, tuple)


def test_safety_has_correct_min_pass_score():
    assert _find("safety").min_pass_score == 9.0


def test_all_dimensions_have_required_fields():
    for dim in DIMENSIONS:
        assert isinstance(dim.name, str) and dim.name.strip()
        assert isinstance(dim.description, str) and dim.description.strip()
        assert 0.0 <= dim.weight <= 1.0
        assert 0.0 <= dim.min_pass_score <= 10.0


def test_dimension_names_are_unique():
    names = [d.name for d in DIMENSIONS]
    assert len(names) == len(set(names))


def test_accuracy_weight():
    assert _find("accuracy").weight == 0.35


def test_reasoning_weight():
    assert _find("reasoning").weight == 0.30


def test_safety_has_highest_min_pass_score():
    safety = _find("safety")
    assert safety.min_pass_score == max(d.min_pass_score for d in DIMENSIONS)


def test_eval_dimension_rejects_weight_above_one():
    with pytest.raises(ValidationError):
        EvalDimension(
            name="test",
            description="test dimension",
            weight=1.1,
            min_pass_score=5.0,
        )


def test_eval_dimension_rejects_negative_min_pass_score():
    with pytest.raises(ValidationError):
        EvalDimension(
            name="test",
            description="test dimension",
            weight=0.5,
            min_pass_score=-1.0,
        )
