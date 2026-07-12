from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mcp_tv_url: str
    mcp_plus_url: str
    mcp_news_url: str
    mcp_shared_url: str
    nova_kb_database_url: str
    redis_url: str

    openrouter_api_key: str
    openrouter_llm_model: str = "openai/gpt-5.4-nano"

    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
