import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from api.main import app
from auth.schemas import AuthenticatedUser
from auth.security import create_access_token
from db.entities.user import UserEntity
from infra.exceptions import ValidationException


def _make_user_entity(email="user@example.com", is_active=True):
    from auth.security import hash_password
    entity = UserEntity(
        email=email,
        hashed_password=hash_password("secret123"),
    )
    entity.is_active = is_active
    return entity


@pytest_asyncio.fixture(loop_scope="function")
async def client():
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_register_returns_200_with_token(client):
    entity = _make_user_entity()
    with patch(
        "auth.router.UserRepository.save", new_callable=AsyncMock, return_value=entity
    ):
        response = await client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "secret123"},
        )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_access_token_is_valid_jwt(client):
    entity = _make_user_entity()
    with patch(
        "auth.router.UserRepository.save", new_callable=AsyncMock, return_value=entity
    ):
        response = await client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "secret123"},
        )
    token = response.json()["access_token"]
    from auth.security import decode_access_token
    public_id = decode_access_token(token)
    assert public_id == entity.public_id


@pytest.mark.asyncio
async def test_register_with_existing_email_returns_422(client):
    with patch(
        "auth.router.UserRepository.save",
        new_callable=AsyncMock,
        side_effect=ValidationException(
            message="Email already registered",
            context={"email": "user@example.com"},
        ),
    ):
        response = await client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "secret123"},
        )
    assert response.status_code == 422
    assert response.json()["error"] == "Email already registered"


@pytest.mark.asyncio
async def test_register_with_short_password_returns_422(client):
    response = await client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_with_invalid_email_returns_422(client):
    response = await client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "secret123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_returns_200_with_token(client):
    entity = _make_user_entity()
    with patch(
        "auth.router.UserRepository.find_by_email",
        new_callable=AsyncMock,
        return_value=entity,
    ):
        response = await client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "secret123"},
        )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_422(client):
    entity = _make_user_entity()
    with patch(
        "auth.router.UserRepository.find_by_email",
        new_callable=AsyncMock,
        return_value=entity,
    ):
        response = await client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "wrongpassword"},
        )
    assert response.status_code == 422
    assert response.json()["error"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_with_unknown_email_returns_422(client):
    with patch(
        "auth.router.UserRepository.find_by_email",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = await client.post(
            "/auth/login",
            json={"email": "unknown@example.com", "password": "secret123"},
        )
    assert response.status_code == 422
    assert response.json()["error"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_access_token_is_valid_jwt(client):
    entity = _make_user_entity()
    with patch(
        "auth.router.UserRepository.find_by_email",
        new_callable=AsyncMock,
        return_value=entity,
    ):
        response = await client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "secret123"},
        )
    token = response.json()["access_token"]
    from auth.security import decode_access_token
    public_id = decode_access_token(token)
    assert public_id == entity.public_id
