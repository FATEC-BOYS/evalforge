import json

import pytest

from core.schemas import EvalRequest, ExecutorOutput


@pytest.fixture
def sample_eval_request():
    return EvalRequest(
        task="Summarize this text",
        input="The quick brown fox jumps over the lazy dog",
        model="claude-sonnet-4-20250514",
    )


@pytest.fixture
def sample_executor_output():
    return ExecutorOutput(
        response="This text describes a fox jumping over a dog.",
        latency_ms=320.0,
        cost_usd=0.0005,
    )


@pytest.fixture
def mock_anthropic_executor_response():
    return {
        "id": "msg_executor_test",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {"response": "This text describes a fox jumping over a dog."}
                ),
            }
        ],
        "model": "claude-sonnet-4-20250514",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }


@pytest.fixture
def mock_anthropic_evaluator_response():
    return {
        "id": "msg_evaluator_test",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "accuracy": {"score": 9.0, "justification": "Accurate summary."},
                        "reasoning": {"score": 8.5, "justification": "Clear reasoning."},
                        "safety": {"score": 10.0, "justification": "No safety concerns."},
                    }
                ),
            }
        ],
        "model": "claude-sonnet-4-20250514",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 80, "output_tokens": 120},
    }
