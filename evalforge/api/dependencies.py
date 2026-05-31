import uuid
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from auth.schemas import AuthenticatedUser
from auth.security import decode_access_token
from core.orchestrator import OrchestratorGraph
from db.repositories.user_repository import UserRepository
from infra.exceptions import ValidationException

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@dataclass
class RequestContext:
    request_id: str


def get_request_id() -> str:
    return str(uuid.uuid4())


def get_request_context() -> RequestContext:
    request_id = get_request_id()
    return RequestContext(request_id=request_id)


def get_orchestrator() -> OrchestratorGraph:
    return OrchestratorGraph()


async def get_current_user(
    token: str = Depends(_oauth2_scheme),
) -> AuthenticatedUser:
    public_id = decode_access_token(token)
    repo = UserRepository()
    user = await repo.find_by_public_id(public_id)
    if user is None or not user.is_active:
        raise ValidationException(
            message="User not found or inactive",
            context={"public_id": public_id},
        )
    return AuthenticatedUser(
        public_id=user.public_id,
        email=user.email,
        is_active=user.is_active,
    )
