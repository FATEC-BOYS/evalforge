import pytest

from core.schemas import DimensionScore, EvalRequest, EvaluationResult, ExecutorOutput


@pytest.fixture
def sample_eval_request():
    return EvalRequest(
        task="Summarize this text",
        input="The quick brown fox jumps over the lazy dog",
        model="claude-sonnet-4-20250514",
    )


@pytest.fixture
def mock_executor_output():
    return ExecutorOutput(
        response="A fox jumped over a dog.",
        latency_ms=320.0,
        cost_usd=0.0005,
    )


@pytest.fixture
def mock_evaluation_result():
    return EvaluationResult(
        scores={
            "accuracy": DimensionScore(score=9.0, justification="Accurate."),
            "reasoning": DimensionScore(score=8.5, justification="Clear."),
            "safety": DimensionScore(score=10.0, justification="Safe."),
        },
        latency_ms=320.0,
        verdict="PASS",
        model="claude-sonnet-4-20250514",
    )
