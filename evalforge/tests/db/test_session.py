import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.session import AsyncReaderSession, AsyncWriterSession, get_reader_session, get_writer_session


@pytest.mark.asyncio
async def test_writer_session_is_async_session():
    session = AsyncWriterSession()
    assert isinstance(session, AsyncSession)
    await session.close()


@pytest.mark.asyncio
async def test_reader_session_is_async_session():
    session = AsyncReaderSession()
    assert isinstance(session, AsyncSession)
    await session.close()


@pytest.mark.asyncio
async def test_get_writer_session_yields_session(engine, monkeypatch):
    test_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr("db.session.AsyncWriterSession", test_factory)

    async with get_writer_session() as session:
        assert session is not None
        assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_get_reader_session_yields_session(engine, monkeypatch):
    test_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr("db.session.AsyncReaderSession", test_factory)

    async with get_reader_session() as session:
        assert session is not None
        assert isinstance(session, AsyncSession)
