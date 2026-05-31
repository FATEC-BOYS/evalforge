from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.schemas import DimensionScore, EvalRequest, EvalResponse, EvaluationResult
from infra.exceptions import OrchestratorException
from tasks.evaluation_processor import EvaluationProcessor


def _make_eval_response(request: EvalRequest) -> EvalResponse:
    return EvalResponse(
        request=request,
        result=EvaluationResult(
            accuracy=DimensionScore(score=9.0, justification="Accurate."),
            reasoning=DimensionScore(score=8.5, justification="Clear."),
            safety=DimensionScore(score=10.0, justification="Safe."),
            latency_ms=300.0,
            verdict="PASS",
            model="claude-sonnet-4-20250514",
        ),
    )


def test_processor_is_celery_task():
    assert hasattr(EvaluationProcessor, "delay")
    assert hasattr(EvaluationProcessor, "apply_async")


def test_processor_name():
    assert EvaluationProcessor.name == "tasks.evaluation_processor.EvaluationProcessor"


def test_processor_runs_orchestrator(mock_orchestrator_for_task, sample_request_dict):
    with patch("tasks.evaluation_processor.OrchestratorGraph") as MockGraph:
        MockGraph.return_value = mock_orchestrator_for_task
        EvaluationProcessor.run(sample_request_dict, "user-123")

    mock_orchestrator_for_task.run.assert_called_once()
    call_arg = mock_orchestrator_for_task.run.call_args[0][0]
    assert isinstance(call_arg, EvalRequest)
    assert call_arg.task == sample_request_dict["task"]
    assert call_arg.input == sample_request_dict["input"]


def test_processor_is_idempotent(sample_request_dict, sample_task_id):
    run_count = 0

    async def _counting_run(request):
        nonlocal run_count
        run_count += 1
        return _make_eval_response(request)

    mock_redis = AsyncMock()
    # First call: key set (nx=True) → not a duplicate → 1 (truthy)
    # Second call: key already exists → None (falsy)
    mock_redis.set = AsyncMock(side_effect=[1, None])

    with patch("tasks.evaluation_processor.OrchestratorGraph") as MockGraph, \
         patch("tasks.evaluation_processor.get_redis_client", return_value=mock_redis):
        MockGraph.return_value.run = _counting_run
        EvaluationProcessor.run(sample_request_dict, "user-123", task_id=sample_task_id)
        EvaluationProcessor.run(sample_request_dict, "user-123", task_id=sample_task_id)

    assert run_count == 1


def test_processor_persists_result(mock_orchestrator_for_task, sample_request_dict):
    with patch("tasks.evaluation_processor.OrchestratorGraph") as MockGraph, \
         patch("tasks.evaluation_processor.EvaluationRepository") as MockRepo:
        MockGraph.return_value = mock_orchestrator_for_task
        MockRepo.return_value.save = AsyncMock()
        EvaluationProcessor.run(sample_request_dict, "user-123")

    MockRepo.return_value.save.assert_called_once()


def test_processor_handles_orchestrator_failure(sample_request_dict):
    mock_logger = MagicMock()

    with patch("tasks.evaluation_processor.OrchestratorGraph") as MockGraph, \
         patch("tasks.evaluation_processor.get_logger", return_value=mock_logger):
        MockGraph.return_value.run = AsyncMock(
            side_effect=OrchestratorException(
                message="Pipeline failed",
                context={"task": "Summarize"},
            )
        )
        # Must not propagate
        EvaluationProcessor.run(sample_request_dict, "user-123")

    mock_logger.error.assert_called()
