import httpx
import pytest
from httpx import ASGITransport
from unittest.mock import AsyncMock, patch

from api.main import app


def _make_checkout_event(customer_id: str = "cus_test123", subscription_id: str = "sub_test123") -> dict:
    return {
        "type": "checkout.session.completed",
        "data": {"object": {"customer": customer_id, "subscription": subscription_id}},
    }


def _make_subscription_deleted_event(customer_id: str = "cus_test123") -> dict:
    return {
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": customer_id}},
    }


@pytest.mark.asyncio
async def test_webhook_handles_checkout_completed(mock_free_user_entity):
    with patch("billing.router.stripe") as mock_s, \
         patch("billing.router.UserRepository") as MockRepo:
        mock_s.Webhook.construct_event.return_value = _make_checkout_event()
        MockRepo.return_value.find_by_stripe_customer_id = AsyncMock(
            return_value=mock_free_user_entity
        )
        MockRepo.return_value.update_tier = AsyncMock(return_value=mock_free_user_entity)
        MockRepo.return_value.update_stripe_ids = AsyncMock(return_value=mock_free_user_entity)

        async with httpx.AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/billing/webhook",
                content=b"fake_webhook_body",
                headers={"stripe-signature": "t=123,v1=abc"},
            )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    call_args = MockRepo.return_value.update_tier.call_args
    assert call_args.args[1] == "pro"


@pytest.mark.asyncio
async def test_webhook_handles_subscription_deleted(mock_pro_user_entity):
    with patch("billing.router.stripe") as mock_s, \
         patch("billing.router.UserRepository") as MockRepo:
        mock_s.Webhook.construct_event.return_value = _make_subscription_deleted_event()
        MockRepo.return_value.find_by_stripe_customer_id = AsyncMock(
            return_value=mock_pro_user_entity
        )
        MockRepo.return_value.update_tier = AsyncMock(return_value=mock_pro_user_entity)

        async with httpx.AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/billing/webhook",
                content=b"fake_webhook_body",
                headers={"stripe-signature": "t=123,v1=abc"},
            )

    assert response.status_code == 200
    call_args = MockRepo.return_value.update_tier.call_args
    assert call_args.args[1] == "free"


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_signature():
    class _FakeSigError(Exception):
        def __init__(self, msg="", sig_header=""):
            super().__init__(msg)

    with patch("billing.router.stripe") as mock_s:
        mock_s.error.SignatureVerificationError = _FakeSigError
        mock_s.Webhook.construct_event.side_effect = _FakeSigError(
            "No signatures found", "t=123,v1=bad"
        )

        async with httpx.AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/billing/webhook",
                content=b"fake_body",
                headers={"stripe-signature": "t=123,v1=bad"},
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_webhook_ignores_unknown_event_types():
    with patch("billing.router.stripe") as mock_s, \
         patch("billing.router.UserRepository") as MockRepo:
        mock_s.Webhook.construct_event.return_value = {
            "type": "payment_intent.succeeded",
            "data": {"object": {}},
        }
        MockRepo.return_value.update_tier = AsyncMock()

        async with httpx.AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/billing/webhook",
                content=b"fake_webhook_body",
                headers={"stripe-signature": "t=123,v1=abc"},
            )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    MockRepo.return_value.update_tier.assert_not_called()
