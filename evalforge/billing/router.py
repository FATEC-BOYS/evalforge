import stripe
from fastapi import APIRouter, Depends, Request

from api.dependencies import AuthenticatedUser, get_current_user
from billing.schemas import CheckoutSessionResponse, SubscriptionStatus
from db.repositories.user_repository import UserRepository
from infra.config import settings
from infra.exceptions import EvalException
from infra.logger import get_logger

router = APIRouter(prefix="/billing")


@router.post("/checkout")
async def create_checkout(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CheckoutSessionResponse:
    logger = get_logger(__name__)

    if current_user.tier == "pro":
        raise EvalException(
            message="User already on Pro tier",
            context={"user_public_id": current_user.public_id},
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY

    customer = stripe.Customer.create(email=current_user.email)

    session = stripe.checkout.Session.create(
        customer=customer.id,
        payment_method_types=["card"],
        line_items=[{"price": settings.STRIPE_PRO_PRICE_ID, "quantity": 1}],
        mode="subscription",
        success_url="https://evalforge.dev/billing/success",
        cancel_url="https://evalforge.dev/billing/cancel",
    )

    repo = UserRepository()
    await repo.update_stripe_ids(current_user.public_id, customer.id, None)

    logger.info(
        "checkout_session_created",
        user=current_user.public_id,
        session_id=session.id,
    )

    return CheckoutSessionResponse(
        checkout_url=session.url,
        session_id=session.id,
    )


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict:
    logger = get_logger(__name__)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    body = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=body,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        raise EvalException(
            message="Invalid Stripe webhook payload",
            context={"error": str(e)},
        )
    except stripe.error.SignatureVerificationError as e:
        raise EvalException(
            message="Invalid Stripe webhook signature",
            context={"error": str(e)},
        )

    repo = UserRepository()

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        customer_id = session_data["customer"]
        subscription_id = session_data["subscription"]

        user = await repo.find_by_stripe_customer_id(customer_id)
        if user:
            await repo.update_stripe_ids(user.public_id, customer_id, subscription_id)
            await repo.update_tier(user.public_id, "pro")
            logger.info(
                "user_upgraded_to_pro",
                user_public_id=user.public_id,
                customer_id=customer_id,
            )

    elif event["type"] == "customer.subscription.deleted":
        subscription_data = event["data"]["object"]
        customer_id = subscription_data["customer"]

        user = await repo.find_by_stripe_customer_id(customer_id)
        if user:
            await repo.update_tier(user.public_id, "free")
            logger.info(
                "user_downgraded_to_free",
                user_public_id=user.public_id,
                customer_id=customer_id,
            )

    return {"status": "ok"}


@router.get("/status")
async def get_billing_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SubscriptionStatus:
    repo = UserRepository()
    user = await repo.find_by_public_id(current_user.public_id)
    return SubscriptionStatus(
        tier=user.tier if user else "free",
        stripe_customer_id=user.stripe_customer_id if user else None,
        stripe_subscription_id=user.stripe_subscription_id if user else None,
        is_pro=(user.tier == "pro") if user else False,
    )
