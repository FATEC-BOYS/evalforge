from pydantic import BaseModel


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


class SubscriptionStatus(BaseModel):
    tier: str
    stripe_customer_id: str | None
    stripe_subscription_id: str | None
    is_pro: bool
