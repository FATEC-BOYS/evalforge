from unittest.mock import AsyncMock, patch

import pytest

from core.orchestrator import OrchestratorGraph
from core.schemas import EvalResponse
from infra.exceptions import AgentException, OrchestratorException

_EXECUTOR_PATH = "core.orchestrator.ExecutorAgent"
_EVALUATOR_PATH = "core.orchestrator.EvaluatorAgent"


@pytest.mark.asyncio
async def test_full_pipeline_returns_eval_response(
    sample_eval_request, mock_executor_output, mock_evaluation_result
):
    with patch(_EXECUTOR_PATH) as MockExec, patch(_EVALUATOR_PATH) as MockEval:
        MockExec.return_value.run = AsyncMock(return_value=mock_executor_output)
        MockEval.return_value.run = AsyncMock(return_value=mock_evaluation_result)
        result = await OrchestratorGraph().run(sample_eval_request)

    assert isinstance(result, EvalResponse)
    assert result.request.task == "Summarize this text"
    assert result.result.verdict == "PASS"


@pytest.mark.asyncio
async def test_executor_failure_skips_evaluator(
    sample_eval_request, mock_evaluation_result
):
    with patch(_EXECUTOR_PATH) as MockExec, patch(_EVALUATOR_PATH) as MockEval:
        MockExec.return_value.run = AsyncMock(
            side_effect=AgentException(
                message="Executor failed",
                context={"model": "claude-sonnet-4-20250514"},
            )
        )
        evaluator_mock = AsyncMock(return_value=mock_evaluation_result)
        MockEval.return_value.run = evaluator_mock

        with pytest.raises(OrchestratorException) as exc_info:
            await OrchestratorGraph().run(sample_eval_request)

    evaluator_mock.assert_not_called()
    assert "Pipeline failed" in exc_info.value.message


@pytest.mark.asyncio
async def test_evaluator_failure_raises_orchestrator_exception(
    sample_eval_request, mock_executor_output
):
    with patch(_EXECUTOR_PATH) as MockExec, patch(_EVALUATOR_PATH) as MockEval:
        MockExec.return_value.run = AsyncMock(return_value=mock_executor_output)
        MockEval.return_value.run = AsyncMock(
            side_effect=AgentException(
                message="Evaluator failed",
                context={"model": "claude-sonnet-4-20250514"},
            )
        )
        with pytest.raises(OrchestratorException):
            await OrchestratorGraph().run(sample_eval_request)


@pytest.mark.asyncio
async def test_error_node_is_reached_on_executor_exception(sample_eval_request):
    with patch(_EXECUTOR_PATH) as MockExec, patch(_EVALUATOR_PATH):
        MockExec.return_value.run = AsyncMock(side_effect=RuntimeError("boom"))
        with pytest.raises(OrchestratorException) as exc_info:
            await OrchestratorGraph().run(sample_eval_request)

    assert "task" in exc_info.value.context
    assert "model" in exc_info.value.context


@pytest.mark.asyncio
async def test_missing_evaluation_result_raises_orchestrator_exception(
    sample_eval_request, mock_executor_output
):
    with patch(_EXECUTOR_PATH) as MockExec, patch(_EVALUATOR_PATH) as MockEval:
        MockExec.return_value.run = AsyncMock(return_value=mock_executor_output)
        MockEval.return_value.run = AsyncMock(return_value=None)
        with pytest.raises(OrchestratorException) as exc_info:
            await OrchestratorGraph().run(sample_eval_request)

    assert "without evaluation result" in exc_info.value.message


@pytest.mark.asyncio
async def test_orchestrator_logs_start_and_completion(
    sample_eval_request, mock_executor_output, mock_evaluation_result
):
    with patch(_EXECUTOR_PATH) as MockExec, patch(_EVALUATOR_PATH) as MockEval:
        MockExec.return_value.run = AsyncMock(return_value=mock_executor_output)
        MockEval.return_value.run = AsyncMock(return_value=mock_evaluation_result)
        await OrchestratorGraph().run(sample_eval_request)


@pytest.mark.asyncio
async def test_orchestrator_propagates_request_to_response(
    sample_eval_request, mock_executor_output, mock_evaluation_result
):
    with patch(_EXECUTOR_PATH) as MockExec, patch(_EVALUATOR_PATH) as MockEval:
        MockExec.return_value.run = AsyncMock(return_value=mock_executor_output)
        MockEval.return_value.run = AsyncMock(return_value=mock_evaluation_result)
        result = await OrchestratorGraph().run(sample_eval_request)

    assert result.request.task == sample_eval_request.task
    assert result.request.input == sample_eval_request.input
    assert result.request.model == sample_eval_request.model
