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

    async def update_tier(self, public_id: str, tier: str) -> UserEntity:
        async with get_writer_session() as session:
            result = await session.execute(
                select(UserEntity).where(UserEntity.public_id == public_id)
            )
            user = result.scalar_one_or_none()
            if user is None:
                raise ValidationException(
                    message="User not found",
                    context={"public_id": public_id},
                )
            user.tier = tier
            await session.flush()
            return user

    async def update_stripe_ids(
        self,
        public_id: str,
        stripe_customer_id: str,
        stripe_subscription_id: str | None,
    ) -> UserEntity:
        async with get_writer_session() as session:
            result = await session.execute(
                select(UserEntity).where(UserEntity.public_id == public_id)
            )
            user = result.scalar_one_or_none()
            if user is None:
                raise ValidationException(
                    message="User not found",
                    context={"public_id": public_id},
                )
            user.stripe_customer_id = stripe_customer_id
            if stripe_subscription_id is not None:
                user.stripe_subscription_id = stripe_subscription_id
            await session.flush()
            return user

    async def find_by_stripe_customer_id(self, stripe_customer_id: str) -> UserEntity | None:
        async with get_reader_session() as session:
            result = await session.execute(
                select(UserEntity).where(UserEntity.stripe_customer_id == stripe_customer_id)
            )
            return result.scalar_one_or_none()
