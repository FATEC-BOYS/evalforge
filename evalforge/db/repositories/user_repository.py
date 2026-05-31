from sqlalchemy import select

from db.entities.user import UserEntity
from db.session import get_reader_session, get_writer_session
from infra.exceptions import ValidationException


class UserRepository:
    async def save(self, email: str, hashed_password: str) -> UserEntity:
        existing = await self.find_by_email(email)
        if existing is not None:
            raise ValidationException(
                message="Email already registered",
                context={"email": email},
            )
        entity = UserEntity(email=email, hashed_password=hashed_password)
        async with get_writer_session() as session:
            session.add(entity)
            await session.flush()
        return entity

    async def find_by_email(self, email: str) -> UserEntity | None:
        async with get_reader_session() as session:
            result = await session.execute(
                select(UserEntity).where(UserEntity.email == email)
            )
            return result.scalar_one_or_none()

    async def find_by_public_id(self, public_id: str) -> UserEntity | None:
        async with get_reader_session() as session:
            result = await session.execute(
                select(UserEntity).where(UserEntity.public_id == public_id)
            )
            return result.scalar_one_or_none()
