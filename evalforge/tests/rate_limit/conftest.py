import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    mock.incr = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    mock.scan = AsyncMock(return_value=(0, []))
    return mock


@pytest.fixture
def mock_redis_at_limit():
    mock = AsyncMock()
    mock.incr = AsyncMock(return_value=11)
    mock.expire = AsyncMock(return_value=True)
    mock.scan = AsyncMock(return_value=(0, []))
    return mock


@pytest.fixture
def mock_redis_unavailable():
    mock = AsyncMock()
    mock.incr = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
    mock.expire = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
    mock.scan = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
    return mock


@pytest.fixture
def sample_user_public_id():
    return "test-user-public-id-123"
