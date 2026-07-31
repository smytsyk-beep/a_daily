from __future__ import annotations

from collections import Counter

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import create_app
from common.config import Settings


PRODUCTION_ROUTE_INVENTORY = {
    ("GET", "/health"),
    ("POST", "/telegram/webhook"),
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

NON_PRODUCTION_ROUTE_INVENTORY = Counter(
    [
        ("GET", "/"),
        ("GET", "/"),
        ("GET", "/health"),
        ("GET", "/db/health"),
        ("GET", "/orchestrator/preview"),
        ("GET", "/events/recent"),
        ("POST", "/events/feedback"),
        ("GET", "/modules/digest/daily"),
        ("GET", "/modules/alerts/strong"),
        ("GET", "/modules/calendar.ics"),
        ("GET", "/modules/"),
        ("GET", "/digest/daily"),
        ("GET", "/alerts/strong"),
        ("GET", "/calendar.ics"),
        ("POST", "/telegram/webhook"),
        ("GET", "/users/{user_id}/prefs"),
        ("PATCH", "/users/{user_id}/prefs"),
        ("GET", "/birth/{user_ref}"),
        ("POST", "/birth/upsert"),
        ("GET", "/user/summary"),
        ("GET", "/metrics"),
    ]
)

PRODUCTION_DENIED_ROUTE_MATRIX = [
    pytest.param("GET", "/", id="root"),
    pytest.param("GET", "/docs", id="docs"),
    pytest.param("GET", "/redoc", id="redoc"),
    pytest.param("GET", "/openapi.json", id="openapi"),
    pytest.param("GET", "/db/health", id="database-health"),
    pytest.param(
        "GET", "/orchestrator/preview?user_id=synthetic", id="orchestrator-preview"
    ),
    pytest.param("GET", "/events/recent?limit=1", id="events"),
    pytest.param("POST", "/events/feedback", id="feedback"),
    pytest.param("GET", "/modules/digest/daily", id="module-digest"),
    pytest.param("GET", "/modules/alerts/strong", id="module-alerts"),
    pytest.param(
        "GET", "/modules/calendar.ics?user_id=synthetic", id="module-calendar"
    ),
    pytest.param("GET", "/modules/", id="module-registry"),
    pytest.param("GET", "/digest/daily", id="public-digest"),
    pytest.param("GET", "/alerts/strong", id="public-alerts"),
    pytest.param("GET", "/calendar.ics?user_id=synthetic", id="public-calendar"),
    pytest.param("GET", "/users/1/prefs", id="user-preferences-read"),
    pytest.param("PATCH", "/users/1/prefs", id="user-preferences-write"),
    pytest.param("GET", "/birth/1", id="birth-data-read"),
    pytest.param("POST", "/birth/upsert", id="birth-data-write"),
    pytest.param("GET", "/user/summary?user_ref=1", id="user-summary"),
    pytest.param("GET", "/metrics", id="metrics"),
]


def make_settings(app_env: str, debug: bool) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "APP_ENV": app_env,
        "DEBUG": debug,
    }
    if app_env == "prod":
        values.update(
            {
                "TELEGRAM_BOT_TOKEN": "synthetic-production-bot-token",
                "TELEGRAM_WEBHOOK_SECRET": "synthetic_webhook_secret_1234567890",
                "POSTGRES_PASSWORD": "synthetic-production-database-password",
                "TRUSTED_HOSTS_INPUT": "pilot.example.invalid",
                "ENABLE_INTERNAL_API": False,
                "SCHEDULED_DELIVERY_ENABLED": False,
            }
        )
    return Settings(**values)


@pytest.fixture(autouse=True)
def isolated_settings_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in SETTINGS_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def route_inventory(application: FastAPI) -> Counter[tuple[str, str]]:
    return Counter(
        (method, route.path)
        for route in application.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    )


@pytest.fixture
def production_app() -> FastAPI:
    return create_app(make_settings("prod", debug=False))


def test_production_fastapi_metadata(production_app: FastAPI) -> None:
    assert production_app.debug is False
    assert production_app.docs_url is None
    assert production_app.redoc_url is None
    assert production_app.openapi_url is None
    assert Exception in production_app.exception_handlers


def test_production_route_inventory_is_exact(production_app: FastAPI) -> None:
    assert route_inventory(production_app) == Counter(PRODUCTION_ROUTE_INVENTORY)


def test_production_has_only_one_telegram_route(production_app: FastAPI) -> None:
    telegram_routes = {
        item
        for item in route_inventory(production_app)
        if item[1].startswith("/telegram")
    }
    assert telegram_routes == {("POST", "/telegram/webhook")}


@pytest.mark.parametrize(("method", "path"), PRODUCTION_DENIED_ROUTE_MATRIX)
def test_production_denied_route_matrix_returns_404(
    production_app: FastAPI,
    method: str,
    path: str,
) -> None:
    response = TestClient(production_app).request(method, path)
    assert response.status_code == 404


def test_production_health_contract_is_exact_and_safe(production_app: FastAPI) -> None:
    response = TestClient(production_app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("app_env", "debug"),
    [
        pytest.param("dev", False, id="dev-debug-false"),
        pytest.param("dev", True, id="dev-debug-true"),
        pytest.param("test", False, id="test-debug-false"),
        pytest.param("test", True, id="test-debug-true"),
    ],
)
def test_non_production_registration_depends_on_environment_not_debug(
    app_env: str,
    debug: bool,
) -> None:
    application = create_app(make_settings(app_env, debug))
    client = TestClient(application)

    assert route_inventory(application) == NON_PRODUCTION_ROUTE_INVENTORY
    assert application.debug is debug
    assert application.docs_url == "/docs"
    assert application.redoc_url == "/redoc"
    assert application.openapi_url == "/openapi.json"
    assert client.get("/").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}
