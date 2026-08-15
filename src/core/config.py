import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Autonomous Self-Healing Agent Platform"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database Settings
    DATABASE_URL: str = "sqlite:///./platform.db"  # Defaults to SQLite for local dev/testing, PostgreSQL in docker/prod

    # Redis & Celery Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Vector Database Settings
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: str = "code-audit-memory"
    USE_LOCAL_VECTOR_STORE: bool = True  # Fallback to local memory vector store if Pinecone is unconfigured

    # LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_LLM_MODEL: str = "gpt-4o"
    USE_MOCK_LLM: bool = False  # Allows running deterministic mock LLM for offline testing

    # Observability & LangSmith Settings
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "autonomous-code-audit-platform"

    # GitHub Settings
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    # Sandbox & Execution Limits
    SANDBOX_TIMEOUT_SECONDS: int = 60
    MAX_RETRY_ATTEMPTS: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
