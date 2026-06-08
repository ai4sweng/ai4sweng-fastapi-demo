"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the demo API."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI4SWEng Inventory API"
    debug: bool = False
    database_url: str = "sqlite:///./inventory_demo.db"
    jwt_secret: str = "demo-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    default_page_size: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
