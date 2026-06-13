import pytest
from pydantic import ValidationError

from core.schemas import (
    DimensionScore,
    EvalRequest,
    EvalResponse,
    EvaluationResult,
)


def _valid_dimension_score(**kwargs):
    defaults = {"score": 8.0, "justification": "Looks good."}
    return DimensionScore(**{**defaults, **kwargs})


def _valid_evaluation_result(**kwargs):
    defaults = {
        "scores": {
            "accuracy": _valid_dimension_score(),
            "reasoning": _valid_dimension_score(),
            "safety": _valid_dimension_score(),
        },
        "latency_ms": 200.0,
        "verdict": "PASS",
        "model": "claude-sonnet-4-20250514",
    }
    return EvaluationResult(**{**defaults, **kwargs})


def test_eval_request_default_model():
    request = EvalRequest(task="Summarize", input="Some text")
    assert request.model == "claude-sonnet-4-20250514"


def test_eval_request_rejects_empty_task():
    with pytest.raises(ValidationError):
        EvalRequest(task="", input="Some text")


def test_eval_request_rejects_empty_input():
    with pytest.raises(ValidationError):
        EvalRequest(task="Summarize", input="")


def test_dimension_score_rejects_below_zero():
    with pytest.raises(ValidationError):
        DimensionScore(score=-0.1, justification="test")


def test_dimension_score_rejects_above_ten():
    with pytest.raises(ValidationError):
        DimensionScore(score=10.1, justification="test")


def test_dimension_score_accepts_boundary_values():
    low = DimensionScore(score=0.0, justification="test")
    high = DimensionScore(score=10.0, justification="test")
    assert low.score == 0.0
    assert high.score == 10.0


def test_evaluation_result_rejects_invalid_verdict():
    with pytest.raises(ValidationError):
        _valid_evaluation_result(verdict="UNKNOWN")


def test_evaluation_result_accepts_pass_verdict():
    result = _valid_evaluation_result(verdict="PASS")
    assert result.verdict == "PASS"


def test_evaluation_result_accepts_fail_verdict():
    result = _valid_evaluation_result(verdict="FAIL")
    assert result.verdict == "FAIL"


def test_eval_response_composes_request_and_result():
    request = EvalRequest(task="Summarize", input="Some text")
    result = _valid_evaluation_result()
    response = EvalResponse(request=request, result=result)
    assert response.request.task == "Summarize"
    assert response.result.verdict == "PASS"


def test_evaluation_result_scores_accessible_by_name():
    result = _valid_evaluation_result()
    assert result.scores["accuracy"].score == 8.0
    assert result.scores["reasoning"].justification == "Looks good."


def test_eval_request_accepts_custom_dimensions():
    from core.dimensions import EvalDimension

    dims = [EvalDimension(name="compliance", description="Compliant?", weight=1.0, min_pass_score=8.0)]
    request = EvalRequest(task="Task", input="Input", dimensions=dims)
    assert request.dimensions is not None
    assert request.dimensions[0].name == "compliance"


def test_eval_request_dimensions_default_is_none():
    request = EvalRequest(task="Task", input="Input")
    assert request.dimensions is None
