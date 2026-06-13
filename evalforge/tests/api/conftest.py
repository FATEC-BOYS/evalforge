import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport
from unittest.mock import AsyncMock, MagicMock

from api.dependencies import RequestContext, get_current_user, get_orchestrator, get_request_context
from api.main import app
from auth.schemas import AuthenticatedUser
from core.orchestrator import OrchestratorGraph
from core.schemas import DimensionScore, EvalRequest, EvalResponse, EvaluationResult


@pytest.fixture
def mock_orchestrator():
    mock = MagicMock(spec=OrchestratorGraph)
    mock.run = AsyncMock(
        return_value=EvalResponse(
            request=EvalRequest(task="Summarize", input="Some text"),
            result=EvaluationResult(
                scores={
                    "accuracy": DimensionScore(score=9.0, justification="Accurate."),
                    "reasoning": DimensionScore(score=8.5, justification="Clear."),
                    "safety": DimensionScore(score=10.0, justification="Safe."),
                },
                latency_ms=320.0,
                verdict="PASS",
                model="claude-sonnet-4-20250514",
            ),
        )
    )
    return mock


@pytest.fixture
def mock_eval_request_payload():
    return {
        "task": "Summarize this text",
        "input": "The quick brown fox jumps over the lazy dog",
        "model": "claude-sonnet-4-20250514",
    }


@pytest_asyncio.fixture
async def app_client(mock_orchestrator):
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        request_id="test-request-id-123"
    )
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        public_id="test-user-public-id",
        email="test@example.com",
        is_active=True,
    )

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
