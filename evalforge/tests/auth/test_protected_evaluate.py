from datetime import datetime, timedelta, timezone

import httpx
import pytest
from httpx import ASGITransport
from jose import jwt
from unittest.mock import AsyncMock, MagicMock

from api.dependencies import get_orchestrator
from api.main import app
from core.orchestrator import OrchestratorGraph
from core.schemas import DimensionScore, EvalRequest, EvalResponse, EvaluationResult
from infra.config import settings

_EVAL_PAYLOAD = {
    "task": "Summarize this text",
    "input": "The quick brown fox jumps over the lazy dog",
    "model": "claude-sonnet-4-20250514",
}


def _make_mock_orchestrator():
    mock = MagicMock(spec=OrchestratorGraph)
    mock.run = AsyncMock(
        return_value=EvalResponse(
            request=EvalRequest(task="Summarize this text", input="The quick brown fox"),
            result=EvaluationResult(
                accuracy=DimensionScore(score=9.0, justification="Accurate."),
                reasoning=DimensionScore(score=8.5, justification="Clear."),
                safety=DimensionScore(score=10.0, justification="Safe."),
                latency_ms=320.0,
                verdict="PASS",
                model="claude-sonnet-4-20250514",
            ),
        )
    )
    return mock


@pytest.mark.asyncio
async def test_evaluate_without_token_returns_401():
    app.dependency_overrides[get_orchestrator] = _make_mock_orchestrator
    try:
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            response = await client.post("/evaluate", json=_EVAL_PAYLOAD)
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_evaluate_with_valid_token_returns_200(auth_client, valid_token):
    response = await auth_client.post(
        "/evaluate",
        json=_EVAL_PAYLOAD,
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_evaluate_with_invalid_token_returns_401():
    # Our ValidationException handler returns 422 for auth errors when a
    # token IS present but invalid — only a missing token triggers 401.
    app.dependency_overrides[get_orchestrator] = _make_mock_orchestrator
    try:
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/evaluate",
                json=_EVAL_PAYLOAD,
                headers={"Authorization": "Bearer invalidtoken123"},
            )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_evaluate_with_expired_token_returns_401():
    payload = {
        "sub": "user-id",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    expired_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    app.dependency_overrides[get_orchestrator] = _make_mock_orchestrator
    try:
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/evaluate",
                json=_EVAL_PAYLOAD,
                headers={"Authorization": f"Bearer {expired_token}"},
            )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_user_id_in_body_is_ignored(auth_client, valid_token):
    payload_with_user_id = {**_EVAL_PAYLOAD, "user_id": "injected-id"}
    response = await auth_client.post(
        "/evaluate",
        json=payload_with_user_id,
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert response.status_code == 200
    result = response.json()
    assert "user_id" not in result.get("request", {})


@pytest.mark.asyncio
async def test_authenticated_user_is_logged(auth_client, valid_token):
    response = await auth_client.post(
        "/evaluate",
        json=_EVAL_PAYLOAD,
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert response.status_code == 200
