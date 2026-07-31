from __future__ import annotations

import logging

import pytest

from common.config import (
    Settings,
    SettingsConfigurationError,
    UnsafeProductionConfiguration,
)


PRODUCTION_SETTINGS = {
    "APP_ENV": "prod",
    "DEBUG": False,
    "TELEGRAM_BOT_TOKEN": "123456789:production_bot_token",
    "TELEGRAM_WEBHOOK_SECRET": "Production_Webhook_Secret_0123456789",
    "TRUSTED_HOSTS": "api.example.com",
    "POSTGRES_PASSWORD": "production-database-password",
    "ENABLE_INTERNAL_API": False,
    "SCHEDULED_DELIVERY_ENABLED": False,
}

SETTINGS_ENV_KEYS = {
    "APP_ENV",
    "DEBUG",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_WEBHOOK_SECRET",
    "TRUSTED_HOSTS",
    "ENABLE_INTERNAL_API",
    "INTERNAL_SERVICE_TOKEN",
    "SCHEDULED_DELIVERY_ENABLED",
    "DATABASE_URL",
    "DATABASE_URL_OVERRIDE",
    "POSTGRES_PASSWORD",
}


@pytest.fixture(autouse=True)
def isolated_settings_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in SETTINGS_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def make_production_settings(**overrides: object) -> Settings:
    values = {**PRODUCTION_SETTINGS, **overrides}
    return Settings(_env_file=None, **values)


def assert_production_violation(
    code: str, **overrides: object
) -> UnsafeProductionConfiguration:
    with pytest.raises(UnsafeProductionConfiguration) as captured:
        make_production_settings(**overrides)
    assert code in captured.value.violations
    return captured.value


def test_default_dev_settings_remain_valid() -> None:
    settings = Settings(_env_file=None)

    assert settings.APP_ENV == "dev"
    assert settings.TRUSTED_HOSTS == ("localhost", "127.0.0.1")
    assert settings.ENABLE_INTERNAL_API is False
    assert settings.SCHEDULED_DELIVERY_ENABLED is False


def test_test_environment_remains_valid() -> None:
    settings = Settings(_env_file=None, APP_ENV="test", DEBUG=True)

    assert settings.APP_ENV == "test"
    assert settings.DEBUG is True


def test_valid_production_settings_pass() -> None:
    assert make_production_settings().APP_ENV == "prod"


def test_environment_case_and_whitespace_are_normalized() -> None:
    settings = make_production_settings(APP_ENV="  PrOd  ")

    assert settings.APP_ENV == "prod"


@pytest.mark.parametrize("app_env", ["production", "staging", ""])
def test_unknown_environment_is_rejected_without_echoing_input(app_env: str) -> None:
    with pytest.raises(SettingsConfigurationError) as captured:
        Settings(_env_file=None, APP_ENV=app_env, DEBUG=False)

    assert captured.value.violations == ("app_env_invalid",)
    if app_env:
        assert app_env not in str(captured.value)


def test_production_debug_is_rejected() -> None:
    assert_production_violation("debug_enabled", DEBUG=True)


@pytest.mark.parametrize("app_env", ["dev", "test"])
def test_nonproduction_debug_is_explicitly_allowed(app_env: str) -> None:
    settings = Settings(_env_file=None, APP_ENV=app_env, DEBUG=True)

    assert settings.DEBUG is True


@pytest.mark.parametrize("token", [None, "", "   "])
def test_missing_production_bot_token_is_rejected(token: str | None) -> None:
    assert_production_violation("telegram_bot_token_missing", TELEGRAM_BOT_TOKEN=token)


def test_production_bot_token_placeholder_is_rejected() -> None:
    assert_production_violation(
        "telegram_bot_token_placeholder",
        TELEGRAM_BOT_TOKEN="REPLACE_WITH_PRODUCTION_TELEGRAM_BOT_TOKEN",
    )


@pytest.mark.parametrize("secret", [None, "", "   "])
def test_missing_production_webhook_secret_is_rejected(
    secret: str | None,
) -> None:
    assert_production_violation(
        "telegram_webhook_secret_missing", TELEGRAM_WEBHOOK_SECRET=secret
    )


def test_production_webhook_secret_placeholder_is_rejected() -> None:
    assert_production_violation(
        "telegram_webhook_secret_placeholder",
        TELEGRAM_WEBHOOK_SECRET="REPLACE_WITH_PRODUCTION_TELEGRAM_WEBHOOK_SECRET",
    )


@pytest.mark.parametrize(
    "secret",
    ["too-short", "contains.invalid.characters!" * 2, "x" * 257],
)
def test_invalid_production_webhook_secret_contract_is_rejected(
    secret: str,
) -> None:
    assert_production_violation(
        "telegram_webhook_secret_invalid", TELEGRAM_WEBHOOK_SECRET=secret
    )


def test_default_database_password_is_rejected_in_production() -> None:
    assert_production_violation(
        "database_password_unsafe", POSTGRES_PASSWORD="astrodaily"
    )


def test_database_password_placeholder_is_rejected_in_production() -> None:
    assert_production_violation(
        "database_password_unsafe",
        POSTGRES_PASSWORD="REPLACE_WITH_PRODUCTION_POSTGRES_PASSWORD",
    )


def test_valid_postgres_fields_build_encoded_database_url() -> None:
    settings = make_production_settings(
        POSTGRES_USER="application user",
        POSTGRES_PASSWORD="safe@password:with/slashes",
    )

    assert settings.DATABASE_URL.startswith("postgresql+psycopg2://")
    assert "safe%40password%3Awith%2Fslashes" in settings.DATABASE_URL


@pytest.mark.parametrize(
    ("database_url", "code"),
    [
        ("postgresql+psycopg2://user@db/astrodaily", "database_password_missing"),
        (
            "postgresql+psycopg2://user:astrodaily@db/astrodaily",
            "database_password_unsafe",
        ),
        ("not-a-database-url", "database_url_invalid"),
    ],
)
def test_unsafe_database_url_is_rejected(database_url: str, code: str) -> None:
    assert_production_violation(code, DATABASE_URL=database_url)


def test_database_url_override_has_precedence_and_uses_safe_parser() -> None:
    database_url = (
        "postgresql+psycopg2://service:valid%40database%3Apassword@db/astrodaily"
    )
    settings = make_production_settings(
        DATABASE_URL=database_url,
        POSTGRES_PASSWORD="astrodaily",
    )

    assert settings.DATABASE_URL == database_url


@pytest.mark.parametrize("trusted_hosts", [None, "", " , "])
def test_missing_production_trusted_hosts_are_rejected(
    trusted_hosts: str | None,
) -> None:
    assert_production_violation("trusted_hosts_missing", TRUSTED_HOSTS=trusted_hosts)


def test_production_wildcard_trusted_host_is_rejected() -> None:
    assert_production_violation("trusted_hosts_wildcard", TRUSTED_HOSTS="*")


@pytest.mark.parametrize(
    "trusted_hosts",
    [
        "https://api.example.com",
        "api.example.com/path",
        "api.example.com:443",
        "api..example.com",
    ],
)
def test_malformed_production_trusted_hosts_are_rejected(
    trusted_hosts: str,
) -> None:
    assert_production_violation("trusted_hosts_invalid", TRUSTED_HOSTS=trusted_hosts)


def test_one_production_trusted_host_is_normalized() -> None:
    settings = make_production_settings(TRUSTED_HOSTS="API.Example.COM")

    assert settings.TRUSTED_HOSTS == ("api.example.com",)


def test_multiple_production_trusted_hosts_are_normalized() -> None:
    settings = make_production_settings(
        TRUSTED_HOSTS=" api.example.com, *.services.example.com "
    )

    assert settings.TRUSTED_HOSTS == (
        "api.example.com",
        "*.services.example.com",
    )


@pytest.mark.parametrize("app_env", ["dev", "test"])
def test_nonproduction_trusted_hosts_use_local_defaults(app_env: str) -> None:
    settings = Settings(_env_file=None, APP_ENV=app_env, DEBUG=False)

    assert settings.TRUSTED_HOSTS == ("localhost", "127.0.0.1")


def test_internal_api_defaults_to_disabled() -> None:
    assert make_production_settings().ENABLE_INTERNAL_API is False


@pytest.mark.parametrize("token", [None, "", "   "])
def test_enabled_internal_api_requires_service_token(token: str | None) -> None:
    assert_production_violation(
        "internal_service_token_missing",
        ENABLE_INTERNAL_API=True,
        INTERNAL_SERVICE_TOKEN=token,
    )


def test_internal_service_token_placeholder_is_rejected() -> None:
    assert_production_violation(
        "internal_service_token_placeholder",
        ENABLE_INTERNAL_API=True,
        INTERNAL_SERVICE_TOKEN="REPLACE_WITH_PRODUCTION_INTERNAL_SERVICE_TOKEN",
    )


def test_enabled_internal_api_accepts_valid_service_token() -> None:
    settings = make_production_settings(
        ENABLE_INTERNAL_API=True,
        INTERNAL_SERVICE_TOKEN="valid-internal-service-token",
    )

    assert settings.ENABLE_INTERNAL_API is True


def test_scheduled_delivery_defaults_to_disabled() -> None:
    assert make_production_settings().SCHEDULED_DELIVERY_ENABLED is False


def test_production_scheduled_delivery_is_rejected() -> None:
    assert_production_violation(
        "scheduled_delivery_enabled", SCHEDULED_DELIVERY_ENABLED=True
    )


@pytest.mark.parametrize("app_env", ["dev", "test"])
def test_nonproduction_scheduled_delivery_can_be_enabled(app_env: str) -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV=app_env,
        DEBUG=False,
        SCHEDULED_DELIVERY_ENABLED=True,
    )

    assert settings.SCHEDULED_DELIVERY_ENABLED is True


def test_secret_values_are_redacted_from_exception_repr_and_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    sentinels = {
        "TELEGRAM_BOT_TOKEN": "SENTINEL_BOT_TOKEN_DO_NOT_LEAK",
        "TELEGRAM_WEBHOOK_SECRET": "SENTINEL_WEBHOOK_SECRET_DO_NOT_LEAK_123",
        "POSTGRES_PASSWORD": "SENTINEL_DATABASE_PASSWORD_DO_NOT_LEAK",
        "INTERNAL_SERVICE_TOKEN": "SENTINEL_INTERNAL_TOKEN_DO_NOT_LEAK",
    }
    caplog.set_level(logging.DEBUG)

    with pytest.raises(UnsafeProductionConfiguration) as captured:
        make_production_settings(
            **sentinels,
            DEBUG=True,
            ENABLE_INTERNAL_API=True,
        )

    rendered = str(captured.value) + repr(captured.value) + caplog.text
    for sentinel in sentinels.values():
        assert sentinel not in rendered


def test_secret_values_are_redacted_from_settings_repr() -> None:
    sentinels = {
        "TELEGRAM_BOT_TOKEN": "SENTINEL_BOT_TOKEN_DO_NOT_LEAK",
        "TELEGRAM_WEBHOOK_SECRET": "SENTINEL_WEBHOOK_SECRET_DO_NOT_LEAK_123",
        "POSTGRES_PASSWORD": "SENTINEL_DATABASE_PASSWORD_DO_NOT_LEAK",
        "INTERNAL_SERVICE_TOKEN": "SENTINEL_INTERNAL_TOKEN_DO_NOT_LEAK",
        "OPENAI_API_KEY": "SENTINEL_OPENAI_KEY_DO_NOT_LEAK",
    }
    settings = make_production_settings(
        **sentinels,
        ENABLE_INTERNAL_API=True,
    )

    rendered = repr(settings)
    for sentinel in sentinels.values():
        assert sentinel not in rendered


def test_invalid_typed_value_is_redacted() -> None:
    sentinel = "SENTINEL_INVALID_BOOLEAN_DO_NOT_LEAK"

    with pytest.raises(SettingsConfigurationError) as captured:
        Settings(_env_file=None, APP_ENV="test", DEBUG=sentinel)

    assert captured.value.violations == ("debug_invalid",)
    assert sentinel not in str(captured.value)
    assert sentinel not in repr(captured.value)


def test_production_violation_order_is_deterministic() -> None:
    with pytest.raises(UnsafeProductionConfiguration) as captured:
        Settings(
            _env_file=None,
            APP_ENV="prod",
            DEBUG=True,
            TELEGRAM_BOT_TOKEN=None,
            TELEGRAM_WEBHOOK_SECRET=None,
            POSTGRES_PASSWORD="astrodaily",
            TRUSTED_HOSTS="*",
            ENABLE_INTERNAL_API=True,
            INTERNAL_SERVICE_TOKEN=None,
            SCHEDULED_DELIVERY_ENABLED=True,
        )

    assert captured.value.violations == (
        "debug_enabled",
        "telegram_bot_token_missing",
        "telegram_webhook_secret_missing",
        "database_password_unsafe",
        "trusted_hosts_wildcard",
        "internal_service_token_missing",
        "scheduled_delivery_enabled",
    )
