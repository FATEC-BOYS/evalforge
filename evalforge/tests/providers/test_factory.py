import pytest

from infra.exceptions import ProviderException
from providers.anthropic_provider import AnthropicProvider
from providers.factory import ProviderFactory
from providers.openai_provider import OpenAIProvider


def test_claude_model_returns_anthropic_provider():
    result = ProviderFactory.get_provider("claude-sonnet-4-20250514")
    assert isinstance(result, AnthropicProvider)


def test_claude_opus_returns_anthropic_provider():
    result = ProviderFactory.get_provider("claude-opus-4-20250514")
    assert isinstance(result, AnthropicProvider)


def test_gpt4o_returns_openai_provider():
    result = ProviderFactory.get_provider("gpt-4o")
    assert isinstance(result, OpenAIProvider)


def test_gpt4o_mini_returns_openai_provider():
    result = ProviderFactory.get_provider("gpt-4o-mini")
    assert isinstance(result, OpenAIProvider)


def test_o1_returns_openai_provider():
    result = ProviderFactory.get_provider("o1-preview")
    assert isinstance(result, OpenAIProvider)


def test_unknown_model_raises_provider_exception():
    with pytest.raises(ProviderException) as exc_info:
        ProviderFactory.get_provider("unknown-model-xyz")

    assert "unknown-model-xyz" in exc_info.value.context.get("model", "")


def test_empty_model_raises_provider_exception():
    with pytest.raises(ProviderException):
        ProviderFactory.get_provider("")
