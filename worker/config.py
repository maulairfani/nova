from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str  # Celery broker + result backend (ADR-0007)

    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool = False

    qdrant_url: str

    openrouter_api_key: str
    openrouter_embedding_model: str = "openai/text-embedding-3-small"

    # Sync driver (worker has no async code) — same trusted internal
    # credentials backend's Alembic migrations use, not a scoped read-only
    # role (see ADR-0022's Alternatives Considered).
    core_database_admin_url: str


settings = Settings()
