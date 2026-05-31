from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from infra.config import settings
from infra.exceptions import ValidationException

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(user_public_id: str) -> str:
    payload = {
        "sub": user_public_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise ValidationException(
                message="Invalid or expired token",
                context={"token_preview": token[:10] + "..."},
            )
        return sub
    except JWTError:
        raise ValidationException(
            message="Invalid or expired token",
            context={"token_preview": token[:10] + "..."},
        )
