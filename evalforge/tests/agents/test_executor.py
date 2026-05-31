import json

import httpx
import pytest
import respx

from agents.executor import ExecutorAgent
from core.schemas import ExecutorOutput
from infra.exceptions import AgentException, ProviderException

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def _make_response(text: str, input_tokens: int = 100, output_tokens: int = 50) -> dict:
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "model": "claude-sonnet-4-20250514",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


@pytest.mark.asyncio
async def test_returns_executor_output_schema(sample_eval_request, mock_anthropic_executor_response):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=mock_anthropic_executor_response)
        )
        result = await ExecutorAgent().run(sample_eval_request)

    assert isinstance(result, ExecutorOutput)
    assert result.response == "This text describes a fox jumping over a dog."
    assert result.latency_ms >= 0
    assert result.cost_usd >= 0


@pytest.mark.asyncio
async def test_latency_is_measured(sample_eval_request, mock_anthropic_executor_response):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=mock_anthropic_executor_response)
        )
        result = await ExecutorAgent().run(sample_eval_request)

    assert result.latency_ms > 0


@pytest.mark.asyncio
async def test_cost_is_calculated(sample_eval_request):
    api_response = _make_response(
        text=json.dumps({"response": "some answer"}),
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=api_response)
        )
        result = await ExecutorAgent().run(sample_eval_request)

    assert result.cost_usd == pytest.approx(18.0, rel=1e-3)


@pytest.mark.asyncio
async def test_raises_provider_exception_on_api_failure(sample_eval_request):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(500, json={"error": {"message": "Internal server error", "type": "server_error"}})
        )
        with pytest.raises(ProviderException) as exc_info:
            await ExecutorAgent().run(sample_eval_request)

    assert exc_info.value.provider == "anthropic"
    assert "model" in exc_info.value.context


@pytest.mark.asyncio
async def test_raises_agent_exception_on_malformed_json(sample_eval_request):
    api_response = _make_response(text="not valid json")
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=api_response)
        )
        with pytest.raises(AgentException) as exc_info:
            await ExecutorAgent().run(sample_eval_request)

    assert "raw_output" in exc_info.value.context


@pytest.mark.asyncio
async def test_raises_agent_exception_on_missing_response_key(sample_eval_request):
    api_response = _make_response(text=json.dumps({"wrong_key": "value"}))
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=api_response)
        )
        with pytest.raises(AgentException):
            await ExecutorAgent().run(sample_eval_request)
