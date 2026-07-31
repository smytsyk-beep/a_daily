from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Literal

from pydantic import AliasChoices, Field, PrivateAttr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


AppEnvironment = Literal["dev", "test", "prod"]

_LOCAL_TRUSTED_HOSTS = ("localhost", "127.0.0.1")
_HOST_PATTERN = re.compile(
    r"^(?:\*\.)?"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)
_TELEGRAM_WEBHOOK_SECRET_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,256}$")

_BOT_TOKEN_PLACEHOLDERS = frozenset(
    {
        "REPLACE_WITH_PRODUCTION_TELEGRAM_BOT_TOKEN",
        "*********REPLACE_WITH_YOUR_BOT_TOKEN_FROM_BOTFATHER*********",
    }
)
_WEBHOOK_SECRET_PLACEHOLDERS = frozenset(
    {"REPLACE_WITH_PRODUCTION_TELEGRAM_WEBHOOK_SECRET"}
)
_DATABASE_PASSWORD_PLACEHOLDERS = frozenset(
    {
        "REPLACE_WITH_PRODUCTION_POSTGRES_PASSWORD",
        "*********CHANGE_ME_IN_PROD*********",
    }
)
_INTERNAL_SERVICE_TOKEN_PLACEHOLDERS = frozenset(
    {"REPLACE_WITH_PRODUCTION_INTERNAL_SERVICE_TOKEN"}
)


class SettingsConfigurationError(RuntimeError):
    """A settings failure whose text contains rule names, never input values."""

    heading = "Invalid application configuration"

    def __init__(self, violations: tuple[str, ...] | list[str]) -> None:
        self.violations = tuple(dict.fromkeys(violations))
        detail = "\n".join(f"- {code}" for code in self.violations)
        super().__init__(f"{self.heading}:\n{detail}")


class UnsafeProductionConfiguration(SettingsConfigurationError):
    """Production settings violate one or more fail-closed safety rules."""

    heading = "Unsafe production configuration"


def _invalid_field_codes(error: ValidationError) -> tuple[str, ...]:
    codes: list[str] = []
    for item in error.errors(
        include_url=False,
        include_context=False,
        include_input=False,
    ):
        location = item.get("loc") or ("settings",)
        field_name = str(location[0]).lower()
        codes.append(f"{field_name}_invalid")
    return tuple(sorted(set(codes)))


def _is_missing(value: str | None) -> bool:
    return value is None or not value.strip()


def _is_placeholder(value: str | None, placeholders: frozenset[str]) -> bool:
    return value is not None and value.strip() in placeholders


def _parse_trusted_hosts(raw_value: str | None) -> tuple[str, ...]:
    if raw_value is None:
        return _LOCAL_TRUSTED_HOSTS
    return tuple(host.strip().lower() for host in raw_value.split(","))


def _trusted_hosts_are_valid(hosts: tuple[str, ...]) -> bool:
    return bool(hosts) and all(
        host == "*" or _HOST_PATTERN.fullmatch(host) is not None for host in hosts
    )


class Settings(BaseSettings):
    # --- общие параметры приложения ---
    APP_ENV: AppEnvironment = "dev"
    APP_NAME: str = "astrodaily"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    DEBUG: bool = False

    # --- база данных ---
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "astrodaily"
    POSTGRES_USER: str = "astrodaily"
    POSTGRES_PASSWORD: str = Field(default="astrodaily", repr=False)
    DATABASE_URL_OVERRIDE: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "DATABASE_URL_OVERRIDE"),
        repr=False,
        exclude=True,
    )

    SQLALCHEMY_ECHO: bool = False

    # --- production trust-boundary settings ---
    TELEGRAM_BOT_TOKEN: str | None = Field(default=None, repr=False)
    TELEGRAM_WEBHOOK_SECRET: str | None = Field(default=None, repr=False)
    TRUSTED_HOSTS_INPUT: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TRUSTED_HOSTS", "TRUSTED_HOSTS_INPUT"),
        repr=False,
        exclude=True,
    )
    ENABLE_INTERNAL_API: bool = False
    INTERNAL_SERVICE_TOKEN: str | None = Field(default=None, repr=False)
    SCHEDULED_DELIVERY_ENABLED: bool = False

    # --- integrations / secrets ---
    STRIPE_SECRET_KEY: str | None = Field(default=None, repr=False)
    STRIPE_WEBHOOK_SECRET: str | None = Field(default=None, repr=False)

    # logging
    LOG_LEVEL: str = "INFO"

    # Skyfield
    astro_ephemeris_dir: str = Field(
        default="data/ephemeris", description="Dir for Skyfield ephemeris cache"
    )
    astro_ephemeris_file: str = Field(
        default="de440s.bsp", description="Ephemeris filename"
    )

    # --- Geocoding / timezone ---
    GEOCODER_MODE: str = "stub"
    GEOCODER_CACHE_TTL_DAYS: int = 3650

    NOMINATIM_BASE_URL: str = "http://nominatim:8080"
    NOMINATIM_TIMEOUT_S: int = 5

    GOOGLE_GEOCODING_API_KEY: str | None = Field(default=None, repr=False)
    GOOGLE_GEOCODING_TIMEOUT_S: int = 5

    # --- LLM (Quality Content) ---
    OPENAI_API_KEY: str | None = Field(default=None, repr=False)
    ANTHROPIC_API_KEY: str | None = Field(default=None, repr=False)
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_ENABLED: bool = False
    LLM_CACHE_TTL_DAYS: int = 7
    LLM_MAX_DAILY_COST_USD: float = 10.0
    LLM_MAX_MONTHLY_COST_USD: float = 200.0

    # A/B тест дайджеста: доля пользователей (0–100), которым показываем LLM-рендер
    AB_DIGEST_LLM_PERCENT: int = 50

    _trusted_hosts: tuple[str, ...] = PrivateAttr(default=_LOCAL_TRUSTED_HOSTS)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        hide_input_in_errors=True,
        populate_by_name=True,
    )

    def __init__(self, **values: Any) -> None:
        try:
            super().__init__(**values)
        except ValidationError as error:
            raise SettingsConfigurationError(_invalid_field_codes(error)) from None

    @field_validator("APP_ENV", mode="before")
    @classmethod
    def normalize_app_environment(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    def model_post_init(self, __context: Any) -> None:
        self._trusted_hosts = _parse_trusted_hosts(self.TRUSTED_HOSTS_INPUT)
        if self.APP_ENV == "prod":
            self.validate_production()
        elif self.TRUSTED_HOSTS_INPUT is not None and not _trusted_hosts_are_valid(
            self._trusted_hosts
        ):
            raise SettingsConfigurationError(("trusted_hosts_invalid",))

    @property
    def TRUSTED_HOSTS(self) -> tuple[str, ...]:
        """Normalized comma-separated host patterns for future middleware use."""

        return self._trusted_hosts

    @property
    def DATABASE_URL(self) -> str:
        """Return the validated override or build a URL from POSTGRES_* fields."""

        if self.DATABASE_URL_OVERRIDE and self.DATABASE_URL_OVERRIDE.strip():
            return self.DATABASE_URL_OVERRIDE.strip()
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
            query={"client_encoding": "utf8"},
        ).render_as_string(hide_password=False)

    def validate_production(self) -> Settings:
        """Fail closed using deterministic rule codes and no input values."""

        violations: list[str] = []

        if self.DEBUG:
            violations.append("debug_enabled")

        if _is_missing(self.TELEGRAM_BOT_TOKEN):
            violations.append("telegram_bot_token_missing")
        elif _is_placeholder(self.TELEGRAM_BOT_TOKEN, _BOT_TOKEN_PLACEHOLDERS):
            violations.append("telegram_bot_token_placeholder")

        if _is_missing(self.TELEGRAM_WEBHOOK_SECRET):
            violations.append("telegram_webhook_secret_missing")
        elif _is_placeholder(
            self.TELEGRAM_WEBHOOK_SECRET, _WEBHOOK_SECRET_PLACEHOLDERS
        ):
            violations.append("telegram_webhook_secret_placeholder")
        elif (
            _TELEGRAM_WEBHOOK_SECRET_PATTERN.fullmatch(
                self.TELEGRAM_WEBHOOK_SECRET.strip()
            )
            is None
        ):
            violations.append("telegram_webhook_secret_invalid")

        database_password: str | None
        if self.DATABASE_URL_OVERRIDE and self.DATABASE_URL_OVERRIDE.strip():
            try:
                parsed_url = make_url(self.DATABASE_URL_OVERRIDE.strip())
                if (
                    parsed_url.get_backend_name() != "postgresql"
                    or parsed_url.host is None
                    or parsed_url.database is None
                ):
                    raise ArgumentError("unsupported database URL")
                database_password = parsed_url.password
            except (ArgumentError, TypeError, ValueError):
                violations.append("database_url_invalid")
                database_password = None
        else:
            database_password = self.POSTGRES_PASSWORD

        if "database_url_invalid" not in violations:
            if _is_missing(database_password):
                violations.append("database_password_missing")
            elif database_password.strip() == "astrodaily" or _is_placeholder(
                database_password, _DATABASE_PASSWORD_PLACEHOLDERS
            ):
                violations.append("database_password_unsafe")

        if self.TRUSTED_HOSTS_INPUT is None or not any(self._trusted_hosts):
            violations.append("trusted_hosts_missing")
        elif "*" in self._trusted_hosts:
            violations.append("trusted_hosts_wildcard")
        elif not _trusted_hosts_are_valid(self._trusted_hosts):
            violations.append("trusted_hosts_invalid")

        if self.ENABLE_INTERNAL_API:
            if _is_missing(self.INTERNAL_SERVICE_TOKEN):
                violations.append("internal_service_token_missing")
            elif _is_placeholder(
                self.INTERNAL_SERVICE_TOKEN, _INTERNAL_SERVICE_TOKEN_PLACEHOLDERS
            ):
                violations.append("internal_service_token_placeholder")

        if self.SCHEDULED_DELIVERY_ENABLED:
            violations.append("scheduled_delivery_enabled")

        if violations:
            raise UnsafeProductionConfiguration(violations)
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the single validated application settings instance."""

    return Settings()


# Backward compatibility for modules that import the settings singleton.
settings = get_settings()
