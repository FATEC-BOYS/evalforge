import httpx
import pytest
from httpx import ASGITransport

from api.main import app


@pytest.mark.asyncio
async def test_status_requires_auth():
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/billing/status")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_status_returns_free_for_free_user(billing_client_free):
    response = await billing_client_free.get("/billing/status")
    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "free"
    assert body["is_pro"] is False


@pytest.mark.asyncio
async def test_status_returns_pro_for_pro_user(billing_client_pro):
    response = await billing_client_pro.get("/billing/status")
    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "pro"
    assert body["is_pro"] is True


@pytest.mark.asyncio
async def test_status_returns_stripe_ids_for_pro_user(billing_client_pro):
    response = await billing_client_pro.get("/billing/status")
    assert response.status_code == 200
    body = response.json()
    assert body["stripe_customer_id"] == "cus_test123"
    assert body["stripe_subscription_id"] == "sub_test123"


@pytest.mark.asyncio
async def test_status_returns_null_stripe_ids_for_free_user(billing_client_free):
    response = await billing_client_free.get("/billing/status")
    assert response.status_code == 200
    body = response.json()
    assert body["stripe_customer_id"] is None
    assert body["stripe_subscription_id"] is None
