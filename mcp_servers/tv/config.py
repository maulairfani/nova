from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Alembic (DDL/admin) connection — sync driver
    postgres_tv_admin_url: str

    # Runtime (read-only) connection — async driver, used by the SQL Analytics Tool
    postgres_tv_url: str
    tv_db_readonly_password: str

    qdrant_url: str
    qdrant_collection: str = "mcn_tv"

    openrouter_api_key: str
    openrouter_embedding_model: str = "openai/text-embedding-3-small"
    openrouter_llm_model: str = "openai/gpt-5.4-nano"


settings = Settings()
