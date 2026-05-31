from contextlib import asynccontextmanager

import pytest

from db.repositories.user_repository import UserRepository
from infra.exceptions import ValidationException


def _make_repo(writer_session, monkeypatch):
    @asynccontextmanager
    async def _writer():
        yield writer_session

    @asynccontextmanager
    async def _reader():
        yield writer_session

    monkeypatch.setattr("db.repositories.user_repository.get_writer_session", _writer)
    monkeypatch.setattr("db.repositories.user_repository.get_reader_session", _reader)
    return UserRepository()


@pytest.mark.asyncio
async def test_save_creates_user(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    entity = await repo.save("new@evalforge.dev", "hashed_pw_123")
    assert entity.email == "new@evalforge.dev"
    assert entity.public_id is not None
    assert entity.is_active is True


@pytest.mark.asyncio
async def test_save_raises_on_duplicate_email(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    await repo.save("dup@evalforge.dev", "hashed_pw_1")
    with pytest.raises(ValidationException) as exc_info:
        await repo.save("dup@evalforge.dev", "hashed_pw_2")
    assert "already registered" in exc_info.value.message


@pytest.mark.asyncio
async def test_find_by_email_returns_entity(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    await repo.save("find@evalforge.dev", "hashed_pw")
    result = await repo.find_by_email("find@evalforge.dev")
    assert result is not None
    assert result.email == "find@evalforge.dev"


@pytest.mark.asyncio
async def test_find_by_email_returns_none_when_not_found(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    result = await repo.find_by_email("notfound@evalforge.dev")
    assert result is None


@pytest.mark.asyncio
async def test_find_by_public_id_returns_entity(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    entity = await repo.save("pubid@evalforge.dev", "hashed_pw")
    result = await repo.find_by_public_id(entity.public_id)
    assert result is not None
    assert result.public_id == entity.public_id


@pytest.mark.asyncio
async def test_find_by_public_id_returns_none_when_not_found(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    result = await repo.find_by_public_id("nonexistent-public-id")
    assert result is None


@pytest.mark.asyncio
async def test_hashed_password_is_stored(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    await repo.save("pw@evalforge.dev", "hashed_value_xyz")
    result = await repo.find_by_email("pw@evalforge.dev")
    assert result.hashed_password == "hashed_value_xyz"
