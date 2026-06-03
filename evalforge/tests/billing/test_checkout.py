import httpx
import pytest
from httpx import ASGITransport

from api.main import app


@pytest.mark.asyncio
async def test_checkout_requires_auth():
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.post("/billing/checkout")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_checkout_returns_200_for_free_user(billing_client_free, mock_stripe):
    response = await billing_client_free.post("/billing/checkout")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_checkout_returns_checkout_url(billing_client_free, mock_stripe):
    response = await billing_client_free.post("/billing/checkout")
    body = response.json()
    assert "checkout_url" in body
    assert body["checkout_url"] == "https://checkout.stripe.com/test"


@pytest.mark.asyncio
async def test_checkout_returns_session_id(billing_client_free, mock_stripe):
    response = await billing_client_free.post("/billing/checkout")
    body = response.json()
    assert "session_id" in body
    assert body["session_id"] == "cs_test123"


@pytest.mark.asyncio
async def test_checkout_raises_422_for_pro_user(billing_client_pro):
    response = await billing_client_pro.post("/billing/checkout")
    assert response.status_code == 422
    assert "already on Pro" in response.json()["error"]


@pytest.mark.asyncio
async def test_checkout_creates_stripe_customer(billing_client_free, mock_stripe):
    await billing_client_free.post("/billing/checkout")
    mock_stripe.Customer.create.assert_called_once_with(email="free@evalforge.dev")


@pytest.mark.asyncio
async def test_checkout_creates_stripe_session(billing_client_free, mock_stripe):
    await billing_client_free.post("/billing/checkout")
    mock_stripe.checkout.Session.create.assert_called_once()
