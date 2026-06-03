import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from api.dependencies import get_current_user
from api.main import app
from auth.schemas import AuthenticatedUser
from db.entities.user import UserEntity


@pytest.fixture
def mock_stripe():
    class _SignatureVerificationError(Exception):
        def __init__(self, msg="", sig_header=""):
            super().__init__(msg)

    with patch("billing.router.stripe") as mock:
        mock.error.SignatureVerificationError = _SignatureVerificationError
        mock.Customer.create.return_value = MagicMock(id="cus_test123")
        mock.checkout.Session.create.return_value = MagicMock(
            url="https://checkout.stripe.com/test",
            id="cs_test123",
        )
        mock.Webhook.construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                }
            },
        }
        yield mock


@pytest.fixture
def free_user():
    return AuthenticatedUser(
        public_id="free-user-public-id",
        email="free@evalforge.dev",
        is_active=True,
        tier="free",
    )


@pytest.fixture
def pro_user():
    return AuthenticatedUser(
        public_id="pro-user-public-id",
        email="pro@evalforge.dev",
        is_active=True,
        tier="pro",
    )


@pytest.fixture
def mock_free_user_entity():
    entity = UserEntity(email="free@evalforge.dev", hashed_password="hashed_pw")
    entity.public_id = "free-user-public-id"
    entity.tier = "free"
    entity.stripe_customer_id = None
    entity.stripe_subscription_id = None
    entity.is_active = True
    return entity


@pytest.fixture
def mock_pro_user_entity():
    entity = UserEntity(email="pro@evalforge.dev", hashed_password="hashed_pw")
    entity.public_id = "pro-user-public-id"
    entity.tier = "pro"
    entity.stripe_customer_id = "cus_test123"
    entity.stripe_subscription_id = "sub_test123"
    entity.is_active = True
    return entity


@pytest_asyncio.fixture
async def billing_client_free(mock_free_user_entity, free_user):
    app.dependency_overrides[get_current_user] = lambda: free_user

    with patch("billing.router.UserRepository") as MockRepo:
        MockRepo.return_value.find_by_public_id = AsyncMock(return_value=mock_free_user_entity)
        MockRepo.return_value.update_stripe_ids = AsyncMock(return_value=mock_free_user_entity)
        MockRepo.return_value.update_tier = AsyncMock(return_value=mock_free_user_entity)
        MockRepo.return_value.find_by_stripe_customer_id = AsyncMock(
            return_value=mock_free_user_entity
        )

        async with httpx.AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def billing_client_pro(mock_pro_user_entity, pro_user):
    app.dependency_overrides[get_current_user] = lambda: pro_user

    with patch("billing.router.UserRepository") as MockRepo:
        MockRepo.return_value.find_by_public_id = AsyncMock(return_value=mock_pro_user_entity)
        MockRepo.return_value.update_stripe_ids = AsyncMock(return_value=mock_pro_user_entity)
        MockRepo.return_value.update_tier = AsyncMock(return_value=mock_pro_user_entity)
        MockRepo.return_value.find_by_stripe_customer_id = AsyncMock(
            return_value=mock_pro_user_entity
        )

        async with httpx.AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            yield client

    app.dependency_overrides.clear()
