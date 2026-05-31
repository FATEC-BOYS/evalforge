import json

import httpx
import pytest
import respx

from infra.exceptions import ProviderException
from providers.anthropic_provider import AnthropicProvider
from providers.base import ProviderOutput

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

_DEFAULT_MODEL = "claude-sonnet-4-20250514"


def _full_response(text: str, input_tokens: int = 100, output_tokens: int = 50) -> dict:
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "model": _DEFAULT_MODEL,
        "stop_reason": "end_turn",
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


@pytest.mark.asyncio
async def test_complete_returns_provider_output(
    sample_system_prompt, sample_user_message, mock_anthropic_provider_response
):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=_full_response('{"response": "A fox summary."}'))
        )
        result = await AnthropicProvider().complete(
            system_prompt=sample_system_prompt,
            user_message=sample_user_message,
            model=_DEFAULT_MODEL,
        )

    assert isinstance(result, ProviderOutput)
    assert result.text == '{"response": "A fox summary."}'
    assert result.input_tokens == 100
    assert result.output_tokens == 50


@pytest.mark.asyncio
async def test_complete_raises_provider_exception_on_api_error(
    sample_system_prompt, sample_user_message
):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(
                500, json={"error": {"message": "Internal server error", "type": "server_error"}}
            )
        )
        with pytest.raises(ProviderException) as exc_info:
            await AnthropicProvider().complete(
                system_prompt=sample_system_prompt,
                user_message=sample_user_message,
                model=_DEFAULT_MODEL,
            )

    assert exc_info.value.provider == "anthropic"
    assert "model" in exc_info.value.context


@pytest.mark.asyncio
async def test_complete_raises_provider_exception_on_network_error(
    sample_system_prompt, sample_user_message
):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(side_effect=httpx.ConnectError("connection refused"))
        with pytest.raises(ProviderException) as exc_info:
            await AnthropicProvider().complete(
                system_prompt=sample_system_prompt,
                user_message=sample_user_message,
                model=_DEFAULT_MODEL,
            )

    assert exc_info.value.provider == "anthropic"


@pytest.mark.asyncio
async def test_complete_passes_correct_model(sample_system_prompt, sample_user_message):
    captured = {}

    def _capture(request, route):
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_full_response('{"response": "ok"}'))

    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(side_effect=_capture)
        await AnthropicProvider().complete(
            system_prompt=sample_system_prompt,
            user_message=sample_user_message,
            model=_DEFAULT_MODEL,
        )

    assert captured["body"]["model"] == _DEFAULT_MODEL


@pytest.mark.asyncio
async def test_complete_passes_system_prompt(sample_system_prompt, sample_user_message):
    captured = {}

    def _capture(request, route):
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_full_response('{"response": "ok"}'))

    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(side_effect=_capture)
        await AnthropicProvider().complete(
            system_prompt=sample_system_prompt,
            user_message=sample_user_message,
            model=_DEFAULT_MODEL,
        )

    assert captured["body"]["system"] == sample_system_prompt
