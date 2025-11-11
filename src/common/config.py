from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_NAME: str = "astrodaily"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "astrodaily"
    POSTGRES_USER: str = "astrodaily"
    POSTGRES_PASSWORD: str = "astrodaily"
    TELEGRAM_BOT_TOKEN: str | None = None
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
