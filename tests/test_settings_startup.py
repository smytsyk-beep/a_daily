from __future__ import annotations

import json
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
    assert result.stdout.strip() == "2"
    for value in environment.values():
        if "SENTINEL" in value:
            assert value not in result.stdout


def test_canonical_production_import_has_exact_routes_and_no_runtime_io() -> None:
    environment = valid_production_environment()
    child_environment = os.environ.copy()
    for key in STARTUP_ENV_KEYS:
        child_environment.pop(key, None)
    child_environment.update(environment)
    child_environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    script = """
import json
import sys

import httpx
import psycopg2
from sqlalchemy.engine import Engine

def forbidden_runtime_io(*args, **kwargs):
    raise AssertionError("runtime I/O during application assembly")

psycopg2.connect = forbidden_runtime_io
Engine.connect = forbidden_runtime_io
httpx.Client.request = forbidden_runtime_io
httpx.AsyncClient.request = forbidden_runtime_io

from fastapi.routing import APIRoute
from app.main import app

private_route_modules = {
    "app.routes_birth_data",
    "app.routes_db",
    "app.routes_events",
    "app.routes_feedback",
    "app.routes_metrics",
    "app.routes_modules",
    "app.routes_orchestrator",
    "app.routes_user_prefs",
    "app.routes_user_summary",
}
payload = {
    "routes": sorted(
        [method, route.path]
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    ),
    "docs_url": app.docs_url,
    "redoc_url": app.redoc_url,
    "openapi_url": app.openapi_url,
    "debug": app.debug,
    "private_route_modules": sorted(private_route_modules.intersection(sys.modules)),
}
print(json.dumps(payload, sort_keys=True))
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT / "tests",
        env=child_environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert json.loads(result.stdout) == {
        "routes": [["GET", "/health"], ["POST", "/telegram/webhook"]],
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
        "debug": False,
        "private_route_modules": [],
    }
    for value in environment.values():
        if "SENTINEL" in value:
            assert value not in result.stdout
