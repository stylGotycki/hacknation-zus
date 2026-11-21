from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings read from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Parent Guide API"
    app_env: str = "dev"
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/parent_guide"
    # Seed legal parameters on startup, so `make up` always gives a usable database.
    seed_on_startup: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
