import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # --- общие параметры приложения ---
    APP_ENV: str = "dev"  # dev / prod / test
    APP_NAME: str = "astrodaily"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080

    # флаг отладки FastAPI и прочих подсистем
    DEBUG: bool = False

    # --- база данных ---
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "astrodaily"
    POSTGRES_USER: str = "astrodaily"
    POSTGRES_PASSWORD: str = "astrodaily"

    # echo SQLAlchemy (логировать SQL-запросы)
    SQLALCHEMY_ECHO: bool = False

    # --- интеграции / секреты ---
    TELEGRAM_BOT_TOKEN: str | None = None
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None

    # логирование
    LOG_LEVEL: str = "INFO"

    # Skyfield
    astro_ephemeris_dir: str = Field(
        default="data/ephemeris", description="Dir for Skyfield ephemeris cache"
    )
    astro_ephemeris_file: str = Field(
        default="de440s.bsp", description="Ephemeris filename"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    # --- Geocoding / timezone ---
    GEOCODER_MODE: str = "stub"  # "stub" | "chain" | "nominatim" | "google"
    GEOCODER_CACHE_TTL_DAYS: int = 3650  # ~10 лет, т.к. города не меняются часто

    NOMINATIM_BASE_URL: str = "http://nominatim:8080"
    NOMINATIM_TIMEOUT_S: int = 5

    GOOGLE_GEOCODING_API_KEY: str | None = None
    GOOGLE_GEOCODING_TIMEOUT_S: int = 5

    # --- LLM (Quality Content) ---
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    LLM_PROVIDER: str = "openai"  # openai | anthropic | ollama
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_ENABLED: bool = False  # feature flag
    LLM_CACHE_TTL_DAYS: int = 7
    LLM_MAX_DAILY_COST_USD: float = 10.0
    LLM_MAX_MONTHLY_COST_USD: float = 200.0

    # A/B тест дайджеста: доля пользователей (0–100), которым показываем LLM-рендер при подходящих условиях
    AB_DIGEST_LLM_PERCENT: int = 50

    @property
    def DATABASE_URL(self) -> str:
        """
        Единая точка формирования URL БД.
        В CI можно передать готовую строку через env DATABASE_URL,
        локально используем параметры POSTGRES_*.
        """
        # В CI/production будем передавать готовую строку через env
        if url := os.getenv("DATABASE_URL"):
            return url

        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            f"?client_encoding=utf8"
        )


@lru_cache
def get_settings() -> Settings:
    """
    Синглтон для настроек.

    Использование:
        from app.common.config import get_settings
        settings = get_settings()
    """
    return Settings()


# для обратной совместимости, если где-то уже импортируется settings
settings = get_settings()
