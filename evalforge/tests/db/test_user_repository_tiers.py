from contextlib import asynccontextmanager

import pytest

from db.entities.user import UserEntity
from db.repositories.user_repository import UserRepository


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


def test_user_entity_has_tier_field():
    assert "tier" in UserEntity.__table__.columns.keys()


@pytest.mark.asyncio
async def test_user_default_tier_is_free(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    entity = await repo.save("default@evalforge.dev", "hashed_pw")
    assert entity.tier == "free"


@pytest.mark.asyncio
async def test_update_tier_to_pro(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    entity = await repo.save("topro@evalforge.dev", "hashed_pw")
    updated = await repo.update_tier(entity.public_id, "pro")
    assert updated.tier == "pro"


@pytest.mark.asyncio
async def test_update_tier_to_free(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    entity = await repo.save("tofree@evalforge.dev", "hashed_pw")
    await repo.update_tier(entity.public_id, "pro")
    updated = await repo.update_tier(entity.public_id, "free")
    assert updated.tier == "free"


@pytest.mark.asyncio
async def test_update_stripe_ids(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    entity = await repo.save("stripe@evalforge.dev", "hashed_pw")
    updated = await repo.update_stripe_ids(entity.public_id, "cus_abc123", "sub_abc123")
    assert updated.stripe_customer_id == "cus_abc123"
    assert updated.stripe_subscription_id == "sub_abc123"


@pytest.mark.asyncio
async def test_find_by_stripe_customer_id_returns_entity(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    entity = await repo.save("findme@evalforge.dev", "hashed_pw")
    await repo.update_stripe_ids(entity.public_id, "cus_findme", "sub_findme")
    result = await repo.find_by_stripe_customer_id("cus_findme")
    assert result is not None
    assert result.stripe_customer_id == "cus_findme"


@pytest.mark.asyncio
async def test_find_by_stripe_customer_id_returns_none_when_not_found(writer_session, monkeypatch):
    repo = _make_repo(writer_session, monkeypatch)
    result = await repo.find_by_stripe_customer_id("cus_nonexistent")
    assert result is None
