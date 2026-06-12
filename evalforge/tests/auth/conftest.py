from contextlib import asynccontextmanager

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock

from api.dependencies import get_current_user, get_orchestrator
from api.main import app
from auth.schemas import AuthenticatedUser
from auth.security import create_access_token, hash_password
from core.orchestrator import OrchestratorGraph
from core.schemas import DimensionScore, EvalRequest, EvalResponse, EvaluationResult
from db.base import BaseEntity
from db.entities.user import UserEntity


@pytest.fixture
def test_settings_override():
    return {
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRATION_MINUTES": 30,
    }


@pytest.fixture
def sample_user_email():
    return "testuser@evalforge.dev"


@pytest.fixture
def sample_user_password():
    return "securepassword123"


@pytest.fixture
def sample_hashed_password():
    return hash_password("securepassword123")


@pytest.fixture
def mock_user_entity():
    entity = UserEntity(
        email="testuser@evalforge.dev",
        hashed_password=hash_password("securepassword123"),
    )
    entity.public_id = "test-public-id-123"
    entity.is_active = True
    return entity


@pytest.fixture
def valid_token():
    return create_access_token("test-public-id-123")


def _mock_orchestrator():
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


@pytest_asyncio.fixture(loop_scope="function")
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(loop_scope="function")
async def writer_session(engine):
    session = AsyncSession(engine, expire_on_commit=False)
    yield session
    await session.rollback()
    await session.close()


@pytest_asyncio.fixture(loop_scope="function")
async def auth_client():
    """Client with orchestrator and current_user mocked — bypasses all auth."""
    app.dependency_overrides[get_orchestrator] = _mock_orchestrator
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        public_id="test-public-id-123",
        email="testuser@evalforge.dev",
        is_active=True,
    )
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(loop_scope="function")
async def router_client(engine):
    """Client for /auth/* routes with SQLite in-memory and mocked orchestrator."""

    @asynccontextmanager
    async def _writer():
        session = AsyncSession(engine, expire_on_commit=False)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def _reader():
        session = AsyncSession(engine, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()

    import db.repositories.user_repository as _ur
    import db.session as _session
    original_writer = _session.get_writer_session
    original_reader = _session.get_reader_session
    _session.get_writer_session = _writer
    _session.get_reader_session = _reader
    _ur.get_writer_session = _writer
    _ur.get_reader_session = _reader

    app.dependency_overrides[get_orchestrator] = _mock_orchestrator

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
    _session.get_writer_session = original_writer
    _session.get_reader_session = original_reader
    _ur.get_writer_session = original_writer
    _ur.get_reader_session = original_reader
