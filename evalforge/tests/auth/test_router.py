import pytest

from auth.security import decode_access_token

_REGISTER_PAYLOAD = {"email": "new@evalforge.dev", "password": "password123"}
_LOGIN_PAYLOAD = {"email": "new@evalforge.dev", "password": "password123"}


@pytest.mark.asyncio
async def test_register_returns_200(router_client):
    response = await router_client.post("/auth/register", json=_REGISTER_PAYLOAD)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_returns_token_response(router_client):
    response = await router_client.post("/auth/register", json=_REGISTER_PAYLOAD)
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_token_is_decodable(router_client):
    response = await router_client.post("/auth/register", json=_REGISTER_PAYLOAD)
    token = response.json()["access_token"]
    public_id = decode_access_token(token)
    assert public_id is not None
    assert len(public_id) > 0


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_422(router_client):
    await router_client.post("/auth/register", json=_REGISTER_PAYLOAD)
    response = await router_client.post("/auth/register", json=_REGISTER_PAYLOAD)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_returns_200_with_valid_credentials(router_client):
    await router_client.post("/auth/register", json=_REGISTER_PAYLOAD)
    response = await router_client.post("/auth/login", json=_LOGIN_PAYLOAD)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_returns_token_response(router_client):
    await router_client.post("/auth/register", json=_REGISTER_PAYLOAD)
    response = await router_client.post("/auth/login", json=_LOGIN_PAYLOAD)
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_returns_422_with_wrong_password(router_client):
    await router_client.post("/auth/register", json=_REGISTER_PAYLOAD)
    response = await router_client.post(
        "/auth/login",
        json={"email": "new@evalforge.dev", "password": "wrongpassword"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_returns_422_with_unknown_email(router_client):
    response = await router_client.post(
        "/auth/login",
        json={"email": "unknown@evalforge.dev", "password": "password123"},
    )
    assert response.status_code == 422
