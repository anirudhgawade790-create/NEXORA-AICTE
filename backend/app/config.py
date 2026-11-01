"""Application configuration loaded from environment / .env via pydantic-settings."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"

    # Database (SQLite for the prototype; override for Postgres/Supabase).
    DATABASE_URL: str = "sqlite:///./nexora.db"

    # JWT signing material must be supplied outside source control.
    JWT_SECRET: str = ""
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # CORS origins, comma-separated. Vite dev server runs on http://localhost:5173.
    CORS_ORIGINS: str = "http://localhost:5173"

    # SMTP / email. When SMTP_HOST is empty, email is reported as "unconfigured"
    # and only in-app notifications are sent.
    SMTP_HOST: str = ""
    SMTP_PORT: str = ""
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        environment = value.strip().lower()
        if environment not in {"development", "production"}:
            raise ValueError("APP_ENV must be 'development' or 'production'")
        return environment

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
_jwt_secret = settings.JWT_SECRET.strip()
if (
    len(_jwt_secret) < 32
    or len(set(_jwt_secret)) < 8
    or any(marker in _jwt_secret.lower() for marker in ("change-me", "changeme", "placeholder"))
):
    raise RuntimeError("Set JWT_SECRET to a private random value of at least 32 characters.")
settings.JWT_SECRET = _jwt_secret
