from infra.exceptions import ProviderException
from providers.anthropic_provider import AnthropicProvider
from providers.base import BaseProvider
from providers.openai_provider import OpenAIProvider


class ProviderFactory:
    ANTHROPIC_MODELS: frozenset[str] = frozenset({"claude-"})
    OPENAI_MODELS: frozenset[str] = frozenset({"gpt-", "o1-", "o3-"})

    @staticmethod
    def get_provider(model: str) -> BaseProvider:
        if any(model.startswith(prefix) for prefix in ProviderFactory.ANTHROPIC_MODELS):
            return AnthropicProvider()
        if any(model.startswith(prefix) for prefix in ProviderFactory.OPENAI_MODELS):
            return OpenAIProvider()
        raise ProviderException(
            message="Unknown model — cannot determine provider",
            context={"model": model},
            provider="unknown",
        )
