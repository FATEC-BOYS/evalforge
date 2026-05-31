import json

from core.prompt_loader import load_prompt
from core.schemas import DimensionScore, EvalRequest
from infra.exceptions import AgentException
from infra.logger import get_logger
from providers.factory import ProviderFactory


class SecurityEvaluatorAgent:
    async def run(self, request: EvalRequest) -> DimensionScore:
        logger = get_logger(__name__)
        system_prompt = load_prompt("security")

        logger.info("security_evaluator_started", task=request.task, model=request.model)

        provider = ProviderFactory.get_provider(request.model)
        output = await provider.complete(
            system_prompt=system_prompt,
            user_message=f"Task: {request.task}\n\nInput: {request.input}",
            model=request.model,
        )

        raw_text = output.text

        try:
            parsed = json.loads(raw_text)
            score = DimensionScore(
                score=parsed["security"]["score"],
                justification=parsed["security"]["justification"],
            )
        except (json.JSONDecodeError, KeyError):
            raise AgentException(
                message="SecurityEvaluator failed to parse LLM output",
                context={"raw_output": raw_text, "model": request.model},
            )

        logger.info("security_evaluator_completed", score=score.score)

        return score
