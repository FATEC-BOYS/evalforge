import pytest


@pytest.fixture
def valid_settings_kwargs() -> dict:
    return {
        "ANTHROPIC_API_KEY": "sk-ant-fake-key",
        "APP_ENV": "development",
        "LOG_LEVEL": "INFO",
        "LANGSMITH_API_KEY": "ls-fake-key",
        "LANGSMITH_PROJECT": "evalforge-test",
    }
