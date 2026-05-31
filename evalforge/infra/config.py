from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_VALID_ENVS = {"development", "staging", "production"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str | None = None
    APP_ENV: str
    LOG_LEVEL: str = "INFO"
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str
    DATABASE_URL: str
    DATABASE_READER_URL: str
    REDIS_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    @field_validator(
        "ANTHROPIC_API_KEY",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
        "DATABASE_URL",
        "DATABASE_READER_URL",
        "REDIS_URL",
        "JWT_SECRET_KEY",
    )
    @classmethod
    def must_be_non_empty(cls, v: str, info) -> str:
        if not v.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return v

    @field_validator("APP_ENV")
    @classmethod
    def must_be_valid_env(cls, v: str) -> str:
        if v not in _VALID_ENVS:
            raise ValueError(
                f"APP_ENV must be one of {sorted(_VALID_ENVS)}, got '{v}'"
            )
        return v


settings = Settings()
