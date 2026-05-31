import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from api.dependencies import RequestContext, get_request_context
from api.main import app
from api.rate_limit import RateLimitException


class _MockUser:
    public_id = "test-user-public-id-123"


@pytest_asyncio.fixture
async def async_app_client():
    from api.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: _MockUser()
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        request_id="test-request-id"
    )

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_eval_request_payload():
    return {
        "task": "Summarize this text",
        "input": "The quick brown fox jumps over the lazy dog",
        "model": "claude-sonnet-4-20250514",
    }


@pytest.mark.asyncio
async def test_evaluate_returns_processing_status(async_app_client, mock_eval_request_payload):
    with patch("api.main.EvaluationProcessor") as MockProcessor:
        MockProcessor.delay = MagicMock()
        response = await async_app_client.post("/evaluate", json=mock_eval_request_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processing"
    assert "evaluation_id" in body
    assert len(body["evaluation_id"]) > 0


@pytest.mark.asyncio
async def test_evaluate_evaluation_id_is_unique(async_app_client, mock_eval_request_payload):
    with patch("api.main.EvaluationProcessor") as MockProcessor:
        MockProcessor.delay = MagicMock()
        r1 = await async_app_client.post("/evaluate", json=mock_eval_request_payload)
        r2 = await async_app_client.post("/evaluate", json=mock_eval_request_payload)

    assert r1.json()["evaluation_id"] != r2.json()["evaluation_id"]


@pytest.mark.asyncio
async def test_get_evaluate_result_returns_404_when_not_found(async_app_client):
    with patch("api.main.EvaluationRepository") as MockRepo:
        MockRepo.return_value.find_by_public_id = AsyncMock(return_value=None)
        response = await async_app_client.get("/evaluate/nonexistent-id-xyz")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_evaluate_result_returns_result_when_found(async_app_client):
    mock_entity = MagicMock()
    mock_entity.public_id = "valid-public-id"
    mock_entity.verdict = "PASS"
    mock_entity.accuracy_score = 9.0
    mock_entity.accuracy_justification = "Accurate."
    mock_entity.reasoning_score = 8.5
    mock_entity.reasoning_justification = "Clear."
    mock_entity.safety_score = 10.0
    mock_entity.safety_justification = "Safe."
    mock_entity.latency_ms = 300.0
    mock_entity.model = "claude-sonnet-4-20250514"

    with patch("api.main.EvaluationRepository") as MockRepo:
        MockRepo.return_value.find_by_public_id = AsyncMock(return_value=mock_entity)
        response = await async_app_client.get("/evaluate/valid-public-id")

    assert response.status_code == 200
    assert "verdict" in response.json()


@pytest.mark.asyncio
async def test_evaluate_triggers_celery_task(async_app_client, mock_eval_request_payload):
    with patch("api.main.EvaluationProcessor") as MockProcessor:
        MockProcessor.delay = MagicMock()
        await async_app_client.post("/evaluate", json=mock_eval_request_payload)

    MockProcessor.delay.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_exceeded_returns_429(async_app_client, mock_eval_request_payload):
    with patch("api.main.check_rate_limit", new_callable=AsyncMock) as mock_rl:
        mock_rl.side_effect = RateLimitException(
            message="Rate limit exceeded",
            context={"user_public_id": "user-123", "limit": 10},
        )
        response = await async_app_client.post("/evaluate", json=mock_eval_request_payload)

    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["error"]


@pytest.mark.asyncio
async def test_rate_limit_uses_authenticated_user_id(async_app_client, mock_eval_request_payload):
    captured = {}

    async def _capture(user_public_id, redis):
        captured["user_public_id"] = user_public_id

    with patch("api.main.check_rate_limit", side_effect=_capture):
        await async_app_client.post("/evaluate", json=mock_eval_request_payload)

    assert captured["user_public_id"] == _MockUser.public_id
