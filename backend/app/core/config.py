from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings read from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Parent Guide API"
    app_env: str = "dev"
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/parent_guide"
    # Seed legal parameters on startup, so `make up` always gives a usable database.
    seed_on_startup: bool = True
    # Password of the admin panel (X-Admin-Token header). Change it outside local development.
    admin_token: str = "admin"

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, url: str) -> str:
        """Hosted Postgres (Neon, Vercel) hands out plain `postgres://` URLs: add our driver."""
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
