import json
from unittest.mock import AsyncMock, patch

import pytest

from agents.evaluator import EvaluatorAgent
from core.schemas import EvalRequest, EvaluationResult, ExecutorOutput
from providers.base import ProviderOutput


def _make_eval_json(accuracy: float = 9.0, reasoning: float = 8.0, safety: float = 9.5) -> str:
    return json.dumps({
        "accuracy": {"score": accuracy, "justification": "ok"},
        "reasoning": {"score": reasoning, "justification": "ok"},
        "safety": {"score": safety, "justification": "ok"},
    })


@pytest.fixture
def sample_eval_request():
    return EvalRequest(
        task="Summarize this text",
        input="The quick brown fox jumps over the lazy dog",
        model="claude-sonnet-4-20250514",
    )


@pytest.fixture
def sample_executor_output():
    return ExecutorOutput(
        response="This text describes a fox jumping over a dog.",
        latency_ms=320.0,
        cost_usd=0.0005,
    )


@pytest.mark.asyncio
async def test_evaluator_uses_provider_factory(sample_eval_request, sample_executor_output):
    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(
        return_value=ProviderOutput(text=_make_eval_json(), input_tokens=80, output_tokens=120)
    )

    with patch("agents.evaluator.ProviderFactory.get_provider", return_value=mock_provider) as mock_factory:
        result = await EvaluatorAgent().run(sample_eval_request, sample_executor_output)

    mock_factory.assert_called_once_with(sample_eval_request.model)
    mock_provider.complete.assert_called_once()
    assert isinstance(result, EvaluationResult)


@pytest.mark.asyncio
async def test_evaluator_extracts_text_from_provider_output(sample_eval_request, sample_executor_output):
    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(
        return_value=ProviderOutput(text=_make_eval_json(accuracy=8.5), input_tokens=80, output_tokens=120)
    )

    with patch("agents.evaluator.ProviderFactory.get_provider", return_value=mock_provider):
        result = await EvaluatorAgent().run(sample_eval_request, sample_executor_output)

    assert isinstance(result, EvaluationResult)
    assert 0 <= result.accuracy.score <= 10
