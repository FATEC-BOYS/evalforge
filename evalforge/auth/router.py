from fastapi import APIRouter

from auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from auth.security import create_access_token, hash_password, verify_password
from db.repositories.user_repository import UserRepository
from infra.exceptions import ValidationException

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest) -> TokenResponse:
    repo = UserRepository()
    hashed = hash_password(request.password)
    user = await repo.save(email=str(request.email), hashed_password=hashed)
    token = create_access_token(user.public_id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    repo = UserRepository()
    user = await repo.find_by_email(str(request.email))
    if user is None or not verify_password(request.password, user.hashed_password):
        raise ValidationException(
            message="Invalid credentials",
            context={"email": str(request.email)},
        )
    token = create_access_token(user.public_id)
    return TokenResponse(access_token=token)
