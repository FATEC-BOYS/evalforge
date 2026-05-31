import pytest

from core.prompt_loader import load_prompt
from infra.exceptions import EvalException


def test_loads_executor_prompt():
    content = load_prompt("executor")
    assert isinstance(content, str)
    assert len(content) > 0
    assert "response" in content


def test_loads_evaluator_prompt():
    content = load_prompt("evaluator")
    assert isinstance(content, str)
    assert len(content) > 0
    assert "accuracy" in content


def test_raises_eval_exception_on_missing_prompt():
    with pytest.raises(EvalException) as exc_info:
        load_prompt("nonexistent_prompt_xyz")
    assert "prompt_name" in exc_info.value.context
    assert exc_info.value.context["prompt_name"] == "nonexistent_prompt_xyz"


def test_raises_with_expected_path_in_context():
    with pytest.raises(EvalException) as exc_info:
        load_prompt("missing")
    assert "expected_path" in exc_info.value.context
