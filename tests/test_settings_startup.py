from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STARTUP_ENV_KEYS = {
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


def run_application_import(**environment: str) -> subprocess.CompletedProcess[str]:
    child_environment = os.environ.copy()
    for key in STARTUP_ENV_KEYS:
        child_environment.pop(key, None)
    child_environment.update(environment)
    child_environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-c", "from app.main import app; print(len(app.routes))"],
        cwd=REPO_ROOT / "tests",
        env=child_environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def valid_production_environment() -> dict[str, str]:
    return {
        "APP_ENV": "prod",
        "DEBUG": "false",
        "TELEGRAM_BOT_TOKEN": "SENTINEL_STARTUP_BOT_TOKEN_DO_NOT_LEAK",
        "TELEGRAM_WEBHOOK_SECRET": "SENTINEL_STARTUP_WEBHOOK_SECRET_123456",
        "TRUSTED_HOSTS": "api.example.com",
        "POSTGRES_PASSWORD": "SENTINEL_STARTUP_DATABASE_PASSWORD_DO_NOT_LEAK",
        "ENABLE_INTERNAL_API": "false",
        "SCHEDULED_DELIVERY_ENABLED": "false",
    }


def test_invalid_production_settings_block_canonical_application_import() -> None:
    environment = valid_production_environment()
    environment["DEBUG"] = "true"

    result = run_application_import(**environment)

    assert result.returncode != 0
    assert "debug_enabled" in result.stdout
    for value in environment.values():
        if "SENTINEL" in value:
            assert value not in result.stdout


def test_valid_production_settings_pass_canonical_application_import() -> None:
    environment = valid_production_environment()

    result = run_application_import(**environment)

    assert result.returncode == 0, result.stdout
    assert result.stdout.strip().isdigit()
    for value in environment.values():
        if "SENTINEL" in value:
            assert value not in result.stdout
