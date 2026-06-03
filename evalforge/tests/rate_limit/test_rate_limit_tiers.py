import pytest

from api.rate_limit import check_rate_limit
from infra.exceptions import RateLimitException


@pytest.mark.asyncio
async def test_pro_user_bypasses_rate_limit(mock_redis):
    await check_rate_limit("pro-user-123", mock_redis, tier="pro")
    mock_redis.incr.assert_not_called()


@pytest.mark.asyncio
async def test_free_user_is_rate_limited(mock_redis_at_limit):
    with pytest.raises(RateLimitException):
        await check_rate_limit("free-user-123", mock_redis_at_limit, tier="free")


@pytest.mark.asyncio
async def test_default_tier_is_free(mock_redis_at_limit):
    with pytest.raises(RateLimitException):
        await check_rate_limit("user-123", mock_redis_at_limit)


@pytest.mark.asyncio
async def test_pro_user_does_not_touch_redis(mock_redis):
    await check_rate_limit("pro-user-123", mock_redis, tier="pro")
    assert mock_redis.incr.call_count == 0
    assert mock_redis.expire.call_count == 0
