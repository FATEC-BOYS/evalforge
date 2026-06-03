import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tasks.insights_processor import InsightsProcessor


def test_insights_processor_is_celery_task():
    assert hasattr(InsightsProcessor, "delay")
    assert hasattr(InsightsProcessor, "apply_async")


def test_insights_processor_name():
    assert InsightsProcessor.name == "tasks.insights_processor.InsightsProcessor"


def test_insights_processor_returns_insufficient_data_when_few_evaluations():
    with patch("tasks.insights_processor.FailureClusterAnalyzer") as MockAnalyzer:
        MockAnalyzer.return_value.get_failed_justifications = AsyncMock(
            return_value=[{} for _ in range(10)]
        )

        result = InsightsProcessor.run()

    assert result["status"] == "insufficient_data"
    assert result["count"] == 10


def test_insights_processor_runs_analysis_when_enough_data():
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.aclose = AsyncMock()

    with patch("tasks.insights_processor.FailureClusterAnalyzer") as MockAnalyzer, \
         patch("tasks.insights_processor.get_redis_client", return_value=mock_redis):
        MockAnalyzer.return_value.get_failed_justifications = AsyncMock(
            return_value=[{} for _ in range(60)]
        )
        MockAnalyzer.return_value.analyze = AsyncMock(
            return_value=[
                {"cluster_id": 0, "label": "test", "size": 10, "evaluation_ids": []}
            ]
        )

        result = InsightsProcessor.run()

    assert result["status"] == "completed"


def test_insights_processor_caches_result_in_redis():
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.aclose = AsyncMock()

    with patch("tasks.insights_processor.FailureClusterAnalyzer") as MockAnalyzer, \
         patch("tasks.insights_processor.get_redis_client", return_value=mock_redis):
        MockAnalyzer.return_value.get_failed_justifications = AsyncMock(
            return_value=[{} for _ in range(60)]
        )
        MockAnalyzer.return_value.analyze = AsyncMock(
            return_value=[
                {"cluster_id": 0, "label": "test", "size": 10, "evaluation_ids": []}
            ]
        )

        InsightsProcessor.run()

    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    args, kwargs = call_args
    key = args[0] if args else kwargs.get("name", "")
    assert key == "insights:latest"


def test_insights_processor_handles_failure_gracefully():
    with patch("tasks.insights_processor.FailureClusterAnalyzer") as MockAnalyzer:
        MockAnalyzer.return_value.get_failed_justifications = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = InsightsProcessor.run()

    assert result["status"] == "failed"
    assert "error" in result
