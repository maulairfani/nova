from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    tavily_api_key: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool = False


settings = Settings()
