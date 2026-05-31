import openai

from infra.config import settings
from infra.exceptions import ProviderException
from providers.base import BaseProvider, ProviderOutput


class OpenAIProvider(BaseProvider):
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
        max_tokens: int = 1024,
    ) -> ProviderOutput:
        if settings.OPENAI_API_KEY is None:
            raise ProviderException(
                message="OpenAI API key not configured",
                context={"model": model},
                provider="openai",
            )

        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
        except Exception as e:
            raise ProviderException(
                message="OpenAI API call failed",
                context={"error": str(e), "model": model},
                provider="openai",
            )

        return ProviderOutput(
            text=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )
