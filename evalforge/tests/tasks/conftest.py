import pytest
from unittest.mock import AsyncMock

from core.schemas import DimensionScore, EvalRequest, EvalResponse, EvaluationResult


def _make_eval_response(request: EvalRequest | None = None) -> EvalResponse:
    req = request or EvalRequest(
        task="Summarize this text",
        input="The quick brown fox jumps over the lazy dog",
        model="claude-sonnet-4-20250514",
    )
    return EvalResponse(
        request=req,
        result=EvaluationResult(
            scores={
                "accuracy": DimensionScore(score=9.0, justification="Accurate."),
                "reasoning": DimensionScore(score=8.5, justification="Clear."),
                "safety": DimensionScore(score=10.0, justification="Safe."),
            },
            latency_ms=300.0,
            verdict="PASS",
            model="claude-sonnet-4-20250514",
        ),
    )


@pytest.fixture
def mock_orchestrator_for_task():
    mock = AsyncMock()
    mock.run = AsyncMock(side_effect=lambda req: _make_eval_response(req))
    return mock


@pytest.fixture
def sample_request_dict():
    return {
        "task": "Summarize this text",
        "input": "The quick brown fox jumps over the lazy dog",
        "model": "claude-sonnet-4-20250514",
    }


@pytest.fixture
def sample_task_id():
    return "task-idempotent-id-abc123"
