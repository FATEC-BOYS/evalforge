import json
import time

from core.prompt_loader import load_prompt
from core.schemas import EvalRequest, ExecutorOutput
from infra.exceptions import AgentException
from infra.logger import get_logger
from providers.factory import ProviderFactory

_CLAUDE_INPUT_COST = 3.00 / 1_000_000
_CLAUDE_OUTPUT_COST = 15.00 / 1_000_000
_GPT4O_INPUT_COST = 2.50 / 1_000_000
_GPT4O_OUTPUT_COST = 10.00 / 1_000_000


class ExecutorAgent:
    """Sends the evaluation task to the configured LLM provider and returns its raw response."""

    async def run(self, request: EvalRequest) -> ExecutorOutput:
        """Run the task against the LLM and return the response with latency and cost metrics."""
        logger = get_logger(__name__)

        using_custom_prompt = request.system_prompt is not None
        system_prompt = request.system_prompt if using_custom_prompt else load_prompt("executor")
        user_message = request.input if using_custom_prompt else f"Task: {request.task}\n\nInput: {request.input}"

        logger.info("executor_started", task=request.task, model=request.model, custom_prompt=using_custom_prompt)

        start_time = time.monotonic()

        provider = ProviderFactory.get_provider(request.model)
        output = await provider.complete(
            system_prompt=system_prompt,
            user_message=user_message,
            model=request.model,
        )

        latency_ms = (time.monotonic() - start_time) * 1000
        raw_text = output.text

        if using_custom_prompt:
            parsed_response = raw_text
        else:
            try:
                parsed = json.loads(raw_text)
                parsed_response = parsed["response"]
            except (json.JSONDecodeError, KeyError):
                raise AgentException(
                    message="Executor failed to parse LLM output",
                    context={"raw_output": raw_text, "model": request.model},
                )

        if request.model.startswith("claude-"):
            cost_usd = (
                output.input_tokens * _CLAUDE_INPUT_COST
                + output.output_tokens * _CLAUDE_OUTPUT_COST
            )
        elif request.model.startswith("gpt-4o"):
            cost_usd = (
                output.input_tokens * _GPT4O_INPUT_COST
                + output.output_tokens * _GPT4O_OUTPUT_COST
            )
        else:
            cost_usd = 0.0

        logger.info("executor_completed", latency_ms=latency_ms, cost_usd=cost_usd)

        return ExecutorOutput(
            response=parsed_response,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )
