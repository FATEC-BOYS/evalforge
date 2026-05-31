from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from infra.exceptions import RateLimitException
from infra.logger import get_logger

RATE_LIMIT = 10
WINDOW_SECONDS = 3600


async def check_rate_limit(user_public_id: str, redis: Redis) -> None:
    logger = get_logger(__name__)
    key = f"rate_limit:{user_public_id}"
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, WINDOW_SECONDS)
        if count > RATE_LIMIT:
            raise RateLimitException(
                message="Rate limit exceeded",
                context={
                    "user_public_id": user_public_id,
                    "limit": RATE_LIMIT,
                    "current_count": count,
                },
                retry_after=WINDOW_SECONDS,
            )
    except RateLimitException:
        raise
    except (ConnectionError, RedisConnectionError):
        logger.warning("redis_unavailable_rate_limit_skipped", user=user_public_id)
