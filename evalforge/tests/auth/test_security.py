import time

import pytest
from jose import jwt

from auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from infra.config import settings
from infra.exceptions import ValidationException


def test_hash_password_returns_string():
    result = hash_password("mysecretpassword")
    assert isinstance(result, str)
    assert len(result) > 0


def test_hash_password_is_not_plaintext():
    plain = "mysecretpassword"
    result = hash_password(plain)
    assert result != plain


def test_hash_password_produces_different_hashes_for_same_input():
    h1 = hash_password("samepassword")
    h2 = hash_password("samepassword")
    assert h1 != h2


def test_verify_password_correct():
    plain = "correctpassword"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("correctpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token_returns_string():
    token = create_access_token("some-public-id")
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_contains_sub():
    public_id = "user-public-id-abc"
    token = create_access_token(public_id)
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == public_id


def test_create_access_token_contains_exp():
    token = create_access_token("user-public-id-abc")
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert "exp" in payload


def test_decode_access_token_returns_public_id():
    public_id = "user-public-id-xyz"
    token = create_access_token(public_id)
    result = decode_access_token(token)
    assert result == public_id


def test_decode_access_token_raises_on_invalid_token():
    with pytest.raises(ValidationException) as exc_info:
        decode_access_token("this.is.not.a.valid.token")
    assert exc_info.value.message == "Invalid or expired token"


def test_decode_access_token_raises_on_wrong_secret():
    from jose import jwt as _jwt
    token = _jwt.encode({"sub": "user-id"}, "wrong-secret", algorithm="HS256")
    with pytest.raises(ValidationException):
        decode_access_token(token)


def test_decode_access_token_raises_on_expired_token(monkeypatch):
    from datetime import datetime, timedelta, timezone
    from jose import jwt as _jwt

    payload = {
        "sub": "user-id",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    token = _jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(ValidationException) as exc_info:
        decode_access_token(token)
    assert exc_info.value.message == "Invalid or expired token"


def test_decode_access_token_error_context_has_token_preview():
    with pytest.raises(ValidationException) as exc_info:
        decode_access_token("badtoken")
    assert "token_preview" in exc_info.value.context
