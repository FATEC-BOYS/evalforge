from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from infra.config import settings

writer_engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
reader_engine = create_async_engine(settings.DATABASE_READER_URL, echo=False, pool_pre_ping=True)

AsyncWriterSession = async_sessionmaker(writer_engine, expire_on_commit=False)
AsyncReaderSession = async_sessionmaker(reader_engine, expire_on_commit=False)


async def get_writer_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncWriterSession() as session:
        async with session.begin():
            yield session


async def get_reader_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncReaderSession() as session:
        yield session
