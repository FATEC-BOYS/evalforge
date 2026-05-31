from abc import ABC, abstractmethod

from pydantic import BaseModel, field_validator


class ProviderOutput(BaseModel):
    text: str
    input_tokens: int
    output_tokens: int

    @field_validator("text")
    @classmethod
    def text_must_be_non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("text must be non-empty")
        return v

    @field_validator("input_tokens", "output_tokens")
    @classmethod
    def tokens_must_be_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("token counts must be >= 0")
        return v


class BaseProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
        max_tokens: int = 1024,
    ) -> ProviderOutput: ...
