from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Campus Space Booking API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = True

    SECRET_KEY: str = "dev-insecure-secret-key-change-me-32-chars-minimum"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/campus_booking"
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL_SECONDS: int = 180

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    MAX_BOOKING_DURATION_HOURS: int = 8
    MIN_BOOKING_DURATION_MINUTES: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
