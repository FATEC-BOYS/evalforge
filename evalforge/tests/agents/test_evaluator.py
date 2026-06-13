import json

import httpx
import pytest
import respx

from agents.evaluator import EvaluatorAgent
from core.schemas import EvaluationResult
from infra.exceptions import AgentException, ProviderException

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def _make_response(text: str) -> dict:
    return {
        "id": "msg_eval_test",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "model": "claude-sonnet-4-20250514",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 80, "output_tokens": 120},
    }


def _scores_response(accuracy: float, reasoning: float, safety: float) -> dict:
    return _make_response(
        json.dumps({
            "accuracy": {"score": accuracy, "justification": "ok"},
            "reasoning": {"score": reasoning, "justification": "ok"},
            "safety": {"score": safety, "justification": "ok"},
        })
    )


@pytest.mark.asyncio
async def test_returns_evaluation_result_schema(
    sample_eval_request, sample_executor_output, mock_anthropic_evaluator_response
):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=mock_anthropic_evaluator_response)
        )
        result = await EvaluatorAgent().run(sample_eval_request, sample_executor_output)

    assert isinstance(result, EvaluationResult)
    assert result.scores["accuracy"].score == 9.0
    assert result.scores["reasoning"].score == 8.5
    assert result.scores["safety"].score == 10.0


@pytest.mark.asyncio
async def test_pass_verdict_when_all_above_threshold(
    sample_eval_request, sample_executor_output
):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=_scores_response(9.0, 8.0, 9.5))
        )
        result = await EvaluatorAgent().run(sample_eval_request, sample_executor_output)

    assert result.verdict == "PASS"


@pytest.mark.asyncio
async def test_fail_verdict_when_safety_below_threshold(
    sample_eval_request, sample_executor_output
):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=_scores_response(9.0, 9.0, 8.9))
        )
        result = await EvaluatorAgent().run(sample_eval_request, sample_executor_output)

    assert result.verdict == "FAIL"


@pytest.mark.asyncio
async def test_fail_verdict_when_average_below_threshold(
    sample_eval_request, sample_executor_output
):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=_scores_response(5.0, 5.0, 9.0))
        )
        result = await EvaluatorAgent().run(sample_eval_request, sample_executor_output)

    assert result.verdict == "FAIL"


@pytest.mark.asyncio
async def test_raises_provider_exception_on_api_failure(
    sample_eval_request, sample_executor_output
):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(500, json={"error": {"message": "Internal server error", "type": "server_error"}})
        )
        with pytest.raises(ProviderException) as exc_info:
            await EvaluatorAgent().run(sample_eval_request, sample_executor_output)

    assert exc_info.value.provider == "anthropic"


@pytest.mark.asyncio
async def test_raises_agent_exception_on_malformed_json(
    sample_eval_request, sample_executor_output
):
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=_make_response("not valid json"))
        )
        with pytest.raises(AgentException) as exc_info:
            await EvaluatorAgent().run(sample_eval_request, sample_executor_output)

    assert "raw_output" in exc_info.value.context


@pytest.mark.asyncio
async def test_raises_agent_exception_on_missing_dimension_key(
    sample_eval_request, sample_executor_output
):
    partial = _make_response(
        json.dumps({"accuracy": {"score": 9.0, "justification": "ok"}})
    )
    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=partial)
        )
        with pytest.raises(AgentException):
            await EvaluatorAgent().run(sample_eval_request, sample_executor_output)


@pytest.mark.asyncio
async def test_custom_dimensions_used_in_evaluation(
    sample_eval_request, sample_executor_output
):
    from core.dimensions import EvalDimension

    custom_dims = [
        EvalDimension(name="compliance", description="Is it compliant?", weight=0.6, min_pass_score=8.0),
        EvalDimension(name="tone", description="Is the tone appropriate?", weight=0.4, min_pass_score=7.0),
    ]
    sample_eval_request.dimensions = custom_dims

    custom_response = _make_response(json.dumps({
        "compliance": {"score": 9.0, "justification": "Fully compliant."},
        "tone": {"score": 8.0, "justification": "Appropriate tone."},
    }))

    with respx.mock:
        respx.post(_ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=custom_response)
        )
        result = await EvaluatorAgent().run(sample_eval_request, sample_executor_output)

    assert result.verdict == "PASS"
    assert result.scores["compliance"].score == 9.0
    assert result.scores["tone"].score == 8.0
