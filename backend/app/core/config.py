"""Application settings.

Values come from environment variables, or from `backend/.env` during development.
Secrets never live in source code. Pydantic validates everything at startup, so a
missing or malformed value stops the app immediately with a clear error instead of
failing later in the middle of a request.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: str

    jwt_secret: SecretStr = Field(min_length=32)
    access_token_expire_minutes: int = Field(default=60 * 24 * 7, ge=5)

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        # Supabase and most hosts give URLs starting with "postgresql://" or
        # "postgres://". SQLAlchemy also needs to know which Python driver to use.
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL (postgresql://...)")
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
