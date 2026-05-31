import json
from unittest.mock import AsyncMock, patch

import pytest

from agents.executor import ExecutorAgent
from core.schemas import EvalRequest, ExecutorOutput
from providers.base import ProviderOutput


def _make_request(model: str = "claude-sonnet-4-20250514") -> EvalRequest:
    return EvalRequest(
        task="Summarize this text",
        input="The quick brown fox jumps over the lazy dog",
        model=model,
    )


def _make_provider_output(
    text: str = json.dumps({"response": "summary"}),
    input_tokens: int = 100,
    output_tokens: int = 50,
) -> ProviderOutput:
    return ProviderOutput(text=text, input_tokens=input_tokens, output_tokens=output_tokens)


@pytest.mark.asyncio
async def test_executor_uses_provider_factory():
    request = _make_request()
    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(return_value=_make_provider_output())

    with patch("agents.executor.ProviderFactory.get_provider", return_value=mock_provider) as mock_factory:
        result = await ExecutorAgent().run(request)

    mock_factory.assert_called_once_with(request.model)
    mock_provider.complete.assert_called_once()
    assert isinstance(result, ExecutorOutput)


@pytest.mark.asyncio
async def test_executor_calculates_cost_for_claude():
    request = _make_request(model="claude-sonnet-4-20250514")
    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(
        return_value=_make_provider_output(input_tokens=1_000_000, output_tokens=1_000_000)
    )

    with patch("agents.executor.ProviderFactory.get_provider", return_value=mock_provider):
        result = await ExecutorAgent().run(request)

    assert result.cost_usd == pytest.approx(18.0, rel=1e-3)


@pytest.mark.asyncio
async def test_executor_calculates_cost_for_gpt4o():
    request = _make_request(model="gpt-4o")
    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(
        return_value=_make_provider_output(input_tokens=1_000_000, output_tokens=1_000_000)
    )

    with patch("agents.executor.ProviderFactory.get_provider", return_value=mock_provider):
        result = await ExecutorAgent().run(request)

    assert result.cost_usd == pytest.approx(12.5, rel=1e-3)


@pytest.mark.asyncio
async def test_executor_returns_zero_cost_for_unknown_model():
    request = _make_request(model="some-other-model-v1")
    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(
        return_value=_make_provider_output(input_tokens=500_000, output_tokens=500_000)
    )

    with patch("agents.executor.ProviderFactory.get_provider", return_value=mock_provider):
        result = await ExecutorAgent().run(request)

    assert result.cost_usd == 0.0
