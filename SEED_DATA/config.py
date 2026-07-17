from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Admin (DDL-capable) connections — same credentials each unit's own
    # Alembic setup already uses, sync driver (ADR-0016 pattern reused here).
    postgres_tv_admin_url: str
    postgres_plus_admin_url: str
    postgres_news_admin_url: str


settings = Settings()
