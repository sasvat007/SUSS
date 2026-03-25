from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CapitalSense"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production-at-least-32-characters"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Field-level hashing salt
    FIELD_ENCRYPTION_KEY: str = "change-me-field-key-32-bytes!!!!"

    # ML Backend
    ML_BACKEND_URL: str = "http://localhost:8001"
    ML_BACKEND_API_KEY: str = "ml-api-key"

    # Setu
    SETU_CLIENT_ID: Optional[str] = None
    SETU_CLIENT_SECRET: Optional[str] = None
    SETU_BASE_URL: str = "https://prod.setu.co/api"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # Tesseract
    TESSERACT_CMD: str = "tesseract"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Fallback Data
    DEFAULT_BANK_BALANCE: float = 50000.0

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
