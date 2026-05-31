from redis.asyncio import Redis

from infra.config import settings


def get_redis_client() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)
