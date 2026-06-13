import anthropic
from langsmith import traceable
from langsmith.wrappers import wrap_anthropic

from infra.config import settings
from infra.exceptions import ProviderException
from providers.base import BaseProvider, ProviderOutput


class AnthropicProvider(BaseProvider):
    @traceable(run_type="llm", name="anthropic_complete")
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
        max_tokens: int = 1024,
    ) -> ProviderOutput:
        try:
            client = wrap_anthropic(anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY))
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
        except Exception as e:
            raise ProviderException(
                message="Anthropic API call failed",
                context={"error": str(e), "model": model},
                provider="anthropic",
            )

        return ProviderOutput(
            text=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
