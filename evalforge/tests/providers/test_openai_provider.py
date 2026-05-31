import json

import httpx
import pytest
import respx

from infra.config import settings
from infra.exceptions import ProviderException
from providers.base import ProviderOutput
from providers.openai_provider import OpenAIProvider

_OPENAI_URL = "https://api.openai.com/v1/chat/completions"

_DEFAULT_MODEL = "gpt-4o"


def _full_response(content: str, prompt_tokens: int = 100, completion_tokens: int = 50) -> dict:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "choices": [{"message": {"content": content, "role": "assistant"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": prompt_tokens + completion_tokens},
    }


@pytest.mark.asyncio
async def test_complete_returns_provider_output(
    sample_system_prompt, sample_user_message, mock_openai_provider_response
):
    settings.OPENAI_API_KEY = "sk-test-openai"
    with respx.mock:
        respx.post(_OPENAI_URL).mock(
            return_value=httpx.Response(200, json=_full_response('{"response": "A fox summary."}'))
        )
        result = await OpenAIProvider().complete(
            system_prompt=sample_system_prompt,
            user_message=sample_user_message,
            model=_DEFAULT_MODEL,
        )

    assert isinstance(result, ProviderOutput)
    assert result.text == '{"response": "A fox summary."}'
    assert result.input_tokens == 100
    assert result.output_tokens == 50


@pytest.mark.asyncio
async def test_complete_raises_when_api_key_not_configured(
    sample_system_prompt, sample_user_message
):
    settings.OPENAI_API_KEY = None
    with pytest.raises(ProviderException) as exc_info:
        await OpenAIProvider().complete(
            system_prompt=sample_system_prompt,
            user_message=sample_user_message,
            model=_DEFAULT_MODEL,
        )

    assert exc_info.value.provider == "openai"
    assert "not configured" in exc_info.value.message


@pytest.mark.asyncio
async def test_complete_raises_provider_exception_on_api_error(
    sample_system_prompt, sample_user_message
):
    settings.OPENAI_API_KEY = "sk-test-openai"
    with respx.mock:
        respx.post(_OPENAI_URL).mock(
            return_value=httpx.Response(
                500, json={"error": {"message": "Internal server error", "type": "server_error"}}
            )
        )
        with pytest.raises(ProviderException) as exc_info:
            await OpenAIProvider().complete(
                system_prompt=sample_system_prompt,
                user_message=sample_user_message,
                model=_DEFAULT_MODEL,
            )

    assert exc_info.value.provider == "openai"


@pytest.mark.asyncio
async def test_complete_passes_correct_model(sample_system_prompt, sample_user_message):
    settings.OPENAI_API_KEY = "sk-test-openai"
    captured = {}

    def _capture(request, route):
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_full_response('{"response": "ok"}'))

    with respx.mock:
        respx.post(_OPENAI_URL).mock(side_effect=_capture)
        await OpenAIProvider().complete(
            system_prompt=sample_system_prompt,
            user_message=sample_user_message,
            model=_DEFAULT_MODEL,
        )

    assert captured["body"]["model"] == _DEFAULT_MODEL


@pytest.mark.asyncio
async def test_complete_maps_usage_fields_correctly(sample_system_prompt, sample_user_message):
    settings.OPENAI_API_KEY = "sk-test-openai"
    with respx.mock:
        respx.post(_OPENAI_URL).mock(
            return_value=httpx.Response(200, json=_full_response('{"response": "ok"}', prompt_tokens=200, completion_tokens=75))
        )
        result = await OpenAIProvider().complete(
            system_prompt=sample_system_prompt,
            user_message=sample_user_message,
            model=_DEFAULT_MODEL,
        )

    assert result.input_tokens == 200
    assert result.output_tokens == 75
