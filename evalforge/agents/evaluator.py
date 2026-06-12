import json

from core.dimensions import DIMENSIONS, EvalDimension
from core.prompt_loader import load_prompt
from core.schemas import DimensionScore, EvalRequest, EvaluationResult, ExecutorOutput
from infra.config import settings
from infra.exceptions import AgentException
from infra.logger import get_logger
from providers.factory import ProviderFactory

_PASS_AVERAGE_THRESHOLD = 7.0


def _build_dimensions_section(dimensions: tuple[EvalDimension, ...]) -> str:
    lines = []
    for dim in dimensions:
        lines.append(f"### {dim.name}")
        lines.append(dim.description)
        lines.append("")
    return "\n".join(lines).rstrip()


def _build_output_schema(dimensions: tuple[EvalDimension, ...]) -> str:
    schema: dict[str, dict] = {
        dim.name: {"score": "<float 0.0-10.0>", "justification": "<string>"}
        for dim in dimensions
    }
    return json.dumps(schema, indent=2)


def _compute_verdict(
    scores: dict[str, DimensionScore], dimensions: tuple[EvalDimension, ...]
) -> str:
    weighted_dims = [d for d in dimensions if d.weight > 0]
    if weighted_dims:
        total_weight = sum(d.weight for d in weighted_dims)
        weighted_avg = sum(scores[d.name].score * d.weight for d in weighted_dims) / total_weight
    else:
        vals = list(scores.values())
        weighted_avg = sum(s.score for s in vals) / len(vals)

    hard_pass = all(
        scores[d.name].score >= d.min_pass_score
        for d in dimensions
        if d.min_pass_score > 0 and d.name in scores
    )
    return "PASS" if weighted_avg >= _PASS_AVERAGE_THRESHOLD and hard_pass else "FAIL"


class EvaluatorAgent:
    async def run(
        self, request: EvalRequest, executor_output: ExecutorOutput
    ) -> EvaluationResult:
        logger = get_logger(__name__)
        dimensions = tuple(request.dimensions) if request.dimensions else DIMENSIONS

        template = load_prompt("evaluator")
        system_prompt = (
            template
            .replace("<<<DIMENSIONS_SECTION>>>", _build_dimensions_section(dimensions))
            .replace("<<<OUTPUT_SCHEMA>>>", _build_output_schema(dimensions))
        )

        evaluator_model = settings.EVALUATOR_MODEL
        logger.info("evaluator_started", task=request.task, executor_model=request.model, evaluator_model=evaluator_model)

        provider = ProviderFactory.get_provider(evaluator_model)
        output = await provider.complete(
            system_prompt=system_prompt,
            user_message=(
                f"Task: {request.task}\n\n"
                f"Original Input: {request.input}\n\n"
                f"Agent Response: {executor_output.response}"
            ),
            model=evaluator_model,
        )

        raw_text = output.text

        try:
            parsed = json.loads(raw_text)
            scores: dict[str, DimensionScore] = {}
            for dim in dimensions:
                scores[dim.name] = DimensionScore(
                    score=parsed[dim.name]["score"],
                    justification=parsed[dim.name]["justification"],
                )
        except (json.JSONDecodeError, KeyError):
            raise AgentException(
                message="Evaluator failed to parse LLM output",
                context={"raw_output": raw_text, "model": request.model},
            )

        verdict = _compute_verdict(scores, dimensions)

        logger.info(
            "evaluator_completed",
            verdict=verdict,
            **{f"{name}_score": ds.score for name, ds in scores.items()},
        )

        return EvaluationResult(
            scores=scores,
            latency_ms=executor_output.latency_ms,
            verdict=verdict,
            model=evaluator_model,
        )
