import pytest
from pydantic import ValidationError

from infra.config import Settings


def test_raises_on_missing_api_key(monkeypatch, valid_settings_kwargs):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    kwargs = {k: v for k, v in valid_settings_kwargs.items() if k != "ANTHROPIC_API_KEY"}
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **kwargs)


def test_accepts_valid_app_env_values(valid_settings_kwargs):
    for env in ("development", "staging", "production"):
        kwargs = {**valid_settings_kwargs, "APP_ENV": env}
        settings = Settings(_env_file=None, **kwargs)
        assert settings.APP_ENV == env


def test_rejects_invalid_app_env_value(valid_settings_kwargs):
    kwargs = {**valid_settings_kwargs, "APP_ENV": "production_test"}
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None, **kwargs)
    error_text = str(exc_info.value)
    assert "development" in error_text or "staging" in error_text or "production" in error_text


def test_default_log_level_is_info(monkeypatch, valid_settings_kwargs):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    kwargs = {k: v for k, v in valid_settings_kwargs.items() if k != "LOG_LEVEL"}
    settings = Settings(_env_file=None, **kwargs)
    assert settings.LOG_LEVEL == "INFO"
