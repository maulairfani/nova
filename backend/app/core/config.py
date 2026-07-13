from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mcp_tv_url: str
    mcp_plus_url: str
    mcp_news_url: str
    mcp_shared_url: str
    core_database_url: str
    # Sync driver, used only by Alembic migrations (DDL) - never at request
    # runtime. Same credentials/DB as core_database_url, different driver
    # (matches mcp_servers/*/config.py's admin-URL-vs-runtime-URL split,
    # ADR-0016), reusing psycopg (already a backend dependency for the
    # checkpointer) instead of adding a second driver like psycopg2.
    core_database_admin_url: str
    redis_url: str

    openrouter_api_key: str
    openrouter_llm_model: str = "openai/gpt-5.4-nano"

    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
