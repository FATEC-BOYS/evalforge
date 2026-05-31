import pytest
from unittest.mock import AsyncMock

from api.rate_limit import RateLimitException, check_rate_limit
from infra.exceptions import EvalException


@pytest.mark.asyncio
async def test_check_rate_limit_allows_first_request(mock_redis):
    await check_rate_limit("user-123", mock_redis)
    mock_redis.incr.assert_called_once()


@pytest.mark.asyncio
async def test_check_rate_limit_sets_expiry_on_first_request(mock_redis):
    await check_rate_limit("user-123", mock_redis)
    mock_redis.expire.assert_called_once()
    call_args = mock_redis.expire.call_args
    all_args = list(call_args.args) + list(call_args.kwargs.values())
    assert 3600 in all_args


@pytest.mark.asyncio
async def test_check_rate_limit_does_not_reset_expiry_on_subsequent_requests():
    mock = AsyncMock()
    mock.incr = AsyncMock(return_value=5)
    mock.expire = AsyncMock(return_value=True)
    await check_rate_limit("user-123", mock)
    mock.expire.assert_not_called()


@pytest.mark.asyncio
async def test_check_rate_limit_blocks_at_threshold(mock_redis_at_limit):
    with pytest.raises(RateLimitException):
        await check_rate_limit("user-123", mock_redis_at_limit)


def test_rate_limit_exception_is_eval_exception():
    assert issubclass(RateLimitException, EvalException)


def test_rate_limit_exception_carries_context():
    exc = RateLimitException(
        message="Rate limit exceeded",
        context={"user_public_id": "user-123", "limit": 10},
    )
    assert exc.context["user_public_id"] == "user-123"
    assert exc.context["limit"] == 10


@pytest.mark.asyncio
async def test_check_rate_limit_uses_correct_key_pattern(mock_redis):
    await check_rate_limit("user-abc", mock_redis)
    key = mock_redis.incr.call_args.args[0]
    assert key == "rate_limit:user-abc"


@pytest.mark.asyncio
async def test_redis_unavailable_does_not_raise_rate_limit_exception(mock_redis_unavailable):
    # Redis down → allow the request rather than blocking all users
    await check_rate_limit("user-123", mock_redis_unavailable)


@pytest.mark.asyncio
async def test_rate_limit_key_is_user_scoped(mock_redis):
    await check_rate_limit("user-aaa", mock_redis)
    await check_rate_limit("user-bbb", mock_redis)
    keys = [c.args[0] for c in mock_redis.incr.call_args_list]
    assert "rate_limit:user-aaa" in keys
    assert "rate_limit:user-bbb" in keys
    assert keys[0] != keys[1]
