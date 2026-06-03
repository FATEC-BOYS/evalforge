import numpy as np
import pytest
from unittest.mock import AsyncMock, patch

from infra.exceptions import AgentException
from providers.base import ProviderOutput


def test_cluster_returns_labels_list(analyzer, sample_embeddings):
    result = analyzer.cluster(sample_embeddings)
    assert isinstance(result, list)
    assert len(result) == len(sample_embeddings)


def test_cluster_labels_are_integers(analyzer, sample_embeddings):
    result = analyzer.cluster(sample_embeddings)
    assert all(isinstance(label, (int, np.integer)) for label in result)


def test_cluster_noise_label_is_minus_one(analyzer):
    embeddings = [
        [float(i) * 1_000_000, float(i) * 1_000_000, float(i) * 1_000_000]
        for i in range(10)
    ]
    result = analyzer.cluster(embeddings)
    assert -1 in result or all(label == -1 for label in result)


def test_cluster_groups_similar_embeddings(analyzer):
    group_a = [[0.0, 0.0, 0.0] for _ in range(5)]
    group_b = [[10.0, 10.0, 10.0] for _ in range(5)]
    embeddings = group_a + group_b
    result = analyzer.cluster(embeddings)
    assert len(set(label for label in result if label != -1)) >= 1


@pytest.mark.asyncio
async def test_get_embeddings_calls_provider(analyzer, mock_provider_for_clustering):
    with patch("ml.clustering.ProviderFactory.get_provider", return_value=mock_provider_for_clustering):
        await analyzer.get_embeddings(["text one", "text two"], "claude-sonnet-4-20250514")

    assert mock_provider_for_clustering.complete.call_count == 2


@pytest.mark.asyncio
async def test_get_embeddings_returns_list_of_lists(analyzer, mock_provider_for_clustering):
    with patch("ml.clustering.ProviderFactory.get_provider", return_value=mock_provider_for_clustering):
        result = await analyzer.get_embeddings(["text"], "claude-sonnet-4-20250514")

    assert isinstance(result, list)
    assert isinstance(result[0], list)
    assert all(isinstance(v, float) for v in result[0])


@pytest.mark.asyncio
async def test_get_embeddings_raises_on_invalid_json(analyzer):
    mock_provider = AsyncMock()
    mock_provider.complete = AsyncMock(
        return_value=ProviderOutput(
            text="not valid json",
            input_tokens=10,
            output_tokens=5,
        )
    )

    with patch("ml.clustering.ProviderFactory.get_provider", return_value=mock_provider):
        with pytest.raises(AgentException) as exc_info:
            await analyzer.get_embeddings(["text"], "claude-sonnet-4-20250514")

    assert "raw_output" in exc_info.value.context


@pytest.mark.asyncio
async def test_label_cluster_returns_string(analyzer, mock_provider_for_labeling):
    with patch("ml.clustering.ProviderFactory.get_provider", return_value=mock_provider_for_labeling):
        result = await analyzer.label_cluster(
            ["justification 1", "justification 2"],
            "claude-sonnet-4-20250514",
        )

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_label_cluster_samples_max_five_texts(analyzer, mock_provider_for_labeling):
    with patch("ml.clustering.ProviderFactory.get_provider", return_value=mock_provider_for_labeling):
        await analyzer.label_cluster(
            [f"text {i}" for i in range(20)],
            "claude-sonnet-4-20250514",
        )

    call_args = mock_provider_for_labeling.complete.call_args
    args, kwargs = call_args
    user_message = kwargs.get("user_message") or (args[1] if len(args) > 1 else "")
    texts_found = sum(1 for i in range(20) if f"text {i}" in user_message)
    assert texts_found <= 5


@pytest.mark.asyncio
async def test_analyze_returns_cluster_list(analyzer, sample_evaluations, sample_embeddings):
    analyzer.get_embeddings = AsyncMock(return_value=sample_embeddings)
    analyzer.cluster = lambda _: [0, 0, 0, 1, 1, 1, -1, -1, 0, 1]
    analyzer.label_cluster = AsyncMock(return_value="Accuracy failures in complex tasks")

    result = await analyzer.analyze(sample_evaluations)

    assert isinstance(result, list)
    assert len(result) >= 1


@pytest.mark.asyncio
async def test_analyze_excludes_noise_cluster(analyzer, sample_evaluations, sample_embeddings):
    analyzer.get_embeddings = AsyncMock(return_value=sample_embeddings)
    analyzer.cluster = lambda _: [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1]

    result = await analyzer.analyze(sample_evaluations)

    assert result == []


@pytest.mark.asyncio
async def test_analyze_cluster_dict_has_required_fields(analyzer, sample_evaluations, sample_embeddings):
    analyzer.get_embeddings = AsyncMock(return_value=sample_embeddings)
    analyzer.cluster = lambda _: [0] * 10
    analyzer.label_cluster = AsyncMock(return_value="Test label")

    result = await analyzer.analyze(sample_evaluations)

    assert len(result) >= 1
    cluster = result[0]
    assert "cluster_id" in cluster
    assert "label" in cluster
    assert "size" in cluster
    assert "evaluation_ids" in cluster


@pytest.mark.asyncio
async def test_analyze_cluster_size_matches_members(analyzer, sample_evaluations, sample_embeddings):
    analyzer.get_embeddings = AsyncMock(return_value=sample_embeddings)
    analyzer.cluster = lambda _: [0, 0, 0, 1, 1, -1, -1, -1, -1, -1]
    analyzer.label_cluster = AsyncMock(return_value="Test label")

    result = await analyzer.analyze(sample_evaluations)

    cluster_0 = next(c for c in result if c["cluster_id"] == 0)
    assert cluster_0["size"] == 3
    cluster_1 = next(c for c in result if c["cluster_id"] == 1)
    assert cluster_1["size"] == 2
