from billing.schemas import CheckoutSessionResponse, SubscriptionStatus


def test_checkout_session_response_fields():
    response = CheckoutSessionResponse(
        checkout_url="https://checkout.stripe.com/test",
        session_id="cs_test123",
    )
    assert response.checkout_url == "https://checkout.stripe.com/test"
    assert response.session_id == "cs_test123"


def test_subscription_status_is_pro_true():
    status = SubscriptionStatus(
        tier="pro",
        stripe_customer_id="cus_123",
        stripe_subscription_id="sub_123",
        is_pro=True,
    )
    assert status.is_pro is True


def test_subscription_status_is_pro_false():
    status = SubscriptionStatus(
        tier="free",
        stripe_customer_id=None,
        stripe_subscription_id=None,
        is_pro=False,
    )
    assert status.is_pro is False
