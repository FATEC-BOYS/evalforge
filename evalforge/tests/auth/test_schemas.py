import pytest
from pydantic import ValidationError

from auth.schemas import AuthenticatedUser, LoginRequest, RegisterRequest, TokenResponse


def test_register_request_accepts_valid_data():
    req = RegisterRequest(email="user@example.com", password="secret123")
    assert req.email == "user@example.com"
    assert req.password == "secret123"


def test_register_request_rejects_short_password():
    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com", password="short")


def test_register_request_rejects_invalid_email():
    with pytest.raises(ValidationError):
        RegisterRequest(email="not-an-email", password="validpass123")


def test_register_request_requires_email():
    with pytest.raises(ValidationError):
        RegisterRequest(password="validpass123")


def test_register_request_requires_password():
    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com")


def test_register_request_password_exactly_8_chars():
    req = RegisterRequest(email="user@example.com", password="exactly8")
    assert req.password == "exactly8"


def test_login_request_accepts_valid_data():
    req = LoginRequest(email="user@example.com", password="anypassword")
    assert req.email == "user@example.com"
    assert req.password == "anypassword"


def test_login_request_rejects_invalid_email():
    with pytest.raises(ValidationError):
        LoginRequest(email="not-an-email", password="anypassword")


def test_token_response_default_token_type():
    token = TokenResponse(access_token="eyJhbGciOiJIUzI1NiJ9.test.sig")
    assert token.token_type == "bearer"


def test_token_response_custom_token_type():
    token = TokenResponse(access_token="abc", token_type="custom")
    assert token.token_type == "custom"


def test_authenticated_user_fields():
    user = AuthenticatedUser(
        public_id="some-uuid",
        email="user@example.com",
        is_active=True,
    )
    assert user.public_id == "some-uuid"
    assert user.email == "user@example.com"
    assert user.is_active is True


def test_authenticated_user_inactive():
    user = AuthenticatedUser(
        public_id="some-uuid",
        email="user@example.com",
        is_active=False,
    )
    assert user.is_active is False
