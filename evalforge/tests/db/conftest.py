import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.schemas import DimensionScore, EvalRequest, EvalResponse, EvaluationResult
from db.base import BaseEntity


@pytest_asyncio.fixture(loop_scope="function")
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
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
async def reader_session(engine):
    session = AsyncSession(engine, expire_on_commit=False)
    yield session
    await session.rollback()
    await session.close()


@pytest.fixture
def sample_eval_request():
    return EvalRequest(
        task="Summarize this text",
        input="The quick brown fox jumps over the lazy dog",
        model="claude-sonnet-4-20250514",
    )


@pytest.fixture
def sample_eval_response():
    return EvalResponse(
        request=EvalRequest(
            task="Summarize this text",
            input="The quick brown fox jumps over the lazy dog",
            model="claude-sonnet-4-20250514",
        ),
        result=EvaluationResult(
            accuracy=DimensionScore(score=9.0, justification="Accurate."),
            reasoning=DimensionScore(score=8.5, justification="Clear."),
            safety=DimensionScore(score=10.0, justification="Safe."),
            latency_ms=320.0,
            verdict="PASS",
            model="claude-sonnet-4-20250514",
        ),
    )
