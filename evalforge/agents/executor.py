import json
import time

import anthropic

from core.prompt_loader import load_prompt
from core.schemas import EvalRequest, ExecutorOutput
from infra.config import settings
from infra.exceptions import AgentException, ProviderException
from infra.logger import get_logger

_INPUT_COST_PER_TOKEN = 3.00 / 1_000_000
_OUTPUT_COST_PER_TOKEN = 15.00 / 1_000_000


class ExecutorAgent:
    async def run(self, request: EvalRequest) -> ExecutorOutput:
        logger = get_logger(__name__)
        system_prompt = load_prompt("executor")

        logger.info("executor_started", task=request.task, model=request.model)

        start_time = time.monotonic()

        try:
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = await client.messages.create(
                model=request.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Task: {request.task}\n\nInput: {request.input}",
                    }
                ],
            )
        except Exception as e:
            raise ProviderException(
                message="Anthropic API call failed",
                context={
                    "error": str(e),
                    "model": request.model,
                    "request_task": request.task,
                },
                provider="anthropic",
            )

        latency_ms = (time.monotonic() - start_time) * 1000
        raw_text = response.content[0].text

        try:
            parsed = json.loads(raw_text)
            parsed_response = parsed["response"]
        except (json.JSONDecodeError, KeyError):
            raise AgentException(
                message="Executor failed to parse LLM output",
                context={"raw_output": raw_text, "model": request.model},
            )

        cost_usd = (
            response.usage.input_tokens * _INPUT_COST_PER_TOKEN
            + response.usage.output_tokens * _OUTPUT_COST_PER_TOKEN
        )

        logger.info("executor_completed", latency_ms=latency_ms, cost_usd=cost_usd)

        return ExecutorOutput(
            response=parsed_response,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )
