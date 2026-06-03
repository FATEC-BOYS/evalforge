import httpx
import json
import pytest
import pytest_asyncio
from httpx import ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from api.dependencies import get_current_user, get_redis
from api.main import app
from auth.schemas import AuthenticatedUser


_CACHED_INSIGHTS = {
    "clusters": [{"cluster_id": 0, "label": "test", "size": 10, "evaluation_ids": []}],
    "total_failures_analyzed": 50,
    "generated_at": "2026-01-01T00:00:00",
}


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.aclose = AsyncMock()
    return redis


@pytest_asyncio.fixture
async def plain_client():
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def insights_client(mock_redis):
    async def _override_redis():
        yield mock_redis

    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        public_id="test-user-id",
        email="test@example.com",
        is_active=True,
    )
    app.dependency_overrides[get_redis] = _override_redis

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_insights_requires_auth(plain_client):
    response = await plain_client.get("/insights")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_insights_returns_422_when_insufficient_data(insights_client):
    with patch("api.main.EvaluationRepository") as MockRepo:
        MockRepo.return_value.count_all = AsyncMock(return_value=100)
        response = await insights_client.get("/insights")

    assert response.status_code == 422
    body = response.json()
    assert "Insufficient data" in body["error"]
    assert body["context"]["current_count"] == 100
    assert body["context"]["required_count"] == 500


@pytest.mark.asyncio
async def test_insights_returns_cached_result_when_available(insights_client, mock_redis):
    mock_redis.get = AsyncMock(return_value=json.dumps(_CACHED_INSIGHTS))

    with patch("api.main.EvaluationRepository") as MockRepo:
        MockRepo.return_value.count_all = AsyncMock(return_value=600)
        response = await insights_client.get("/insights")

    assert response.status_code == 200
    body = response.json()
    assert "clusters" in body
    assert body["clusters"][0]["label"] == "test"


@pytest.mark.asyncio
async def test_insights_dispatches_task_when_no_cache(insights_client, mock_redis):
    mock_redis.get = AsyncMock(side_effect=Exception("Redis unavailable"))

    with patch("api.main.EvaluationRepository") as MockRepo, \
         patch("api.main.InsightsProcessor") as MockProcessor:
        MockRepo.return_value.count_all = AsyncMock(return_value=600)
        MockProcessor.delay = MagicMock()
        response = await insights_client.get("/insights")

    assert response.status_code == 200
    assert response.json()["status"] == "generating"
    MockProcessor.delay.assert_called_once()


@pytest.mark.asyncio
async def test_insights_response_has_required_fields_when_cached(insights_client, mock_redis):
    mock_redis.get = AsyncMock(return_value=json.dumps(_CACHED_INSIGHTS))

    with patch("api.main.EvaluationRepository") as MockRepo:
        MockRepo.return_value.count_all = AsyncMock(return_value=600)
        response = await insights_client.get("/insights")

    assert response.status_code == 200
    body = response.json()
    assert "clusters" in body
    assert "total_failures_analyzed" in body
    assert "generated_at" in body
