from datetime import datetime, timedelta, timezone

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
    result = hash_password("mypassword")
    assert isinstance(result, str)
    assert len(result) > 0


def test_hash_password_is_not_plaintext():
    result = hash_password("mypassword")
    assert result != "mypassword"


def test_verify_password_returns_true_for_correct_password():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_returns_false_for_wrong_password():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_two_hashes_of_same_password_are_different():
    hash1 = hash_password("mypassword")
    hash2 = hash_password("mypassword")
    assert hash1 != hash2


def test_create_access_token_returns_string():
    result = create_access_token("test-public-id")
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_access_token_is_decodable():
    token = create_access_token("test-public-id")
    public_id = decode_access_token(token)
    assert public_id == "test-public-id"


def test_decode_access_token_returns_correct_subject():
    token = create_access_token("user-abc-123")
    result = decode_access_token(token)
    assert result == "user-abc-123"


def test_decode_expired_token_raises_validation_exception():
    payload = {
        "sub": "user-id",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    expired_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(ValidationException) as exc_info:
        decode_access_token(expired_token)
    assert "Invalid or expired token" in exc_info.value.message


def test_decode_invalid_token_raises_validation_exception():
    with pytest.raises(ValidationException) as exc_info:
        decode_access_token("this.is.not.a.valid.token")
    assert "token_preview" in exc_info.value.context
