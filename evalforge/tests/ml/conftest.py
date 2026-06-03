import pytest
from unittest.mock import AsyncMock

from providers.base import ProviderOutput


@pytest.fixture
def sample_evaluations():
    return [
        {
            "public_id": f"eval-{i}",
            "accuracy_justification": "The response lacks factual accuracy.",
            "reasoning_justification": "The reasoning is unclear and incomplete.",
            "safety_justification": "No safety concerns.",
            "model": "claude-sonnet-4-20250514",
        }
        for i in range(10)
    ]


@pytest.fixture
def sample_embeddings():
    return [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in range(10)]


@pytest.fixture
def mock_provider_for_clustering():
    mock = AsyncMock()
    mock.complete = AsyncMock(
        return_value=ProviderOutput(
            text="[0.1, 0.2, 0.3, 0.4, 0.5]",
            input_tokens=50,
            output_tokens=20,
        )
    )
    return mock


@pytest.fixture
def mock_provider_for_labeling():
    mock = AsyncMock()
    mock.complete = AsyncMock(
        return_value=ProviderOutput(
            text="Responses lack factual accuracy in complex reasoning tasks",
            input_tokens=100,
            output_tokens=15,
        )
    )
    return mock


@pytest.fixture
def analyzer():
    from ml.clustering import FailureClusterAnalyzer

    return FailureClusterAnalyzer()
