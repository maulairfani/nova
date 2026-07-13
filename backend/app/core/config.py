from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mcp_tv_url: str
    mcp_plus_url: str
    mcp_news_url: str
    mcp_shared_url: str
    core_database_url: str
    # postgresql+psycopg:// (sync-capable AND async-capable from the same
    # URL, unlike asyncpg) - used by Alembic migrations (DDL, sync engine)
    # and by app/core/db.py's async engine for querying the identity/access
    # schema (ADR-0021) at runtime. Reuses psycopg (already a backend
    # dependency for the checkpointer) instead of adding a second driver
    # like psycopg2/asyncpg.
    core_database_admin_url: str
    redis_url: str

    openrouter_api_key: str
    openrouter_llm_model: str = "openai/gpt-5.4-nano"

    cors_origins: list[str] = ["http://localhost:3000"]

    # Auth (ADR-0021's schema, login issues these) - no signup, accounts
    # are seeded (seed_users.py), so there's no key-rotation/multi-issuer
    # concern yet that would need anything fancier than a shared secret.
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # one workday


settings = Settings()
