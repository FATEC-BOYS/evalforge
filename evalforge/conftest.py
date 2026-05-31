import os

# Set default env vars before any module-level Settings() instantiation runs.
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("LANGSMITH_API_KEY", "ls-test-key")
os.environ.setdefault("LANGSMITH_PROJECT", "evalforge-test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://evalforge:evalforge_dev@localhost:5432/evalforge")
os.environ.setdefault("DATABASE_READER_URL", "postgresql+asyncpg://evalforge:evalforge_dev@localhost:5432/evalforge")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
