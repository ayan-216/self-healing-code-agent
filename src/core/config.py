import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Autonomous Self-Healing Agent Platform"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # database settings
    DATABASE_URL: str = "sqlite:///./platform.db"  # defaults to sqlite for local dev/testing, postgresql in docker/prod

    # redis & celery settings
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # vector database settings
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: str = "code-audit-memory"
    USE_LOCAL_VECTOR_STORE: bool = True  # fallback to local memory vector store if pinecone is unconfigured

    # llm settings
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_LLM_MODEL: str = "gpt-4o"
    USE_MOCK_LLM: bool = False  # allows running deterministic mock llm for offline testing

    # observability & langsmith settings
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "autonomous-code-audit-platform"

    # github settings
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    # sandbox & execution limits
    SANDBOX_TIMEOUT_SECONDS: int = 60
    MAX_RETRY_ATTEMPTS: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
