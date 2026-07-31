from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Iterator, Sequence
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app
from common.config import Settings
from common.error_handling import PUBLIC_ERROR_MESSAGES, setup_exception_handlers
from common.http_security import CorrelationIdMiddleware, SafeTrustedHostMiddleware


APPROVED_HOSTS = (
    "api.example.com",
    "backup.example.com",
    "*.services.example.com",
)


def production_settings() -> Settings:
    return Settings(
        _env_file=None,
        APP_ENV="prod",
        DEBUG=False,
        TELEGRAM_BOT_TOKEN="synthetic-production-bot-token",
        TELEGRAM_WEBHOOK_SECRET="synthetic_webhook_secret_1234567890",
        POSTGRES_PASSWORD="synthetic-production-database-password",
        TRUSTED_HOSTS=",".join(APPROVED_HOSTS),
        ENABLE_INTERNAL_API=False,
        SCHEDULED_DELIVERY_ENABLED=False,
    )


@pytest.fixture
def production_app() -> FastAPI:
    return create_app(production_settings())


@pytest.fixture
def http_error_log(
    caplog: pytest.LogCaptureFixture,
) -> Iterator[pytest.LogCaptureFixture]:
    target_logger = logging.getLogger("astrodaily.http")
    was_disabled = target_logger.disabled
    target_logger.disabled = False
    caplog.set_level(logging.ERROR, logger="astrodaily.http")
    target_logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        target_logger.removeHandler(caplog.handler)
        target_logger.disabled = was_disabled


def assert_untrusted_host_response(response: Any) -> None:
    request_id = response.headers["x-request-id"]
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    assert response.headers.get("location") is None
    assert response.json() == {
        "ok": False,
        "error": {
            "code": "untrusted_host",
            "message": PUBLIC_ERROR_MESSAGES["untrusted_host"],
        },
        "request_id": request_id,
    }


@pytest.mark.parametrize(
    "host",
    [
        pytest.param("api.example.com", id="exact-host"),
        pytest.param("api.example.com:8443", id="exact-host-with-port"),
        pytest.param("backup.example.com", id="second-approved-host"),
        pytest.param("worker.services.example.com", id="wildcard-subdomain"),
    ],
)
def test_approved_production_hosts_reach_health(
    production_app: FastAPI,
    host: str,
) -> None:
    response = TestClient(production_app).get("/health", headers={"Host": host})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]


def test_approved_host_reaches_telegram_route_without_provider_io(
    production_app: FastAPI,
) -> None:
    response = TestClient(production_app).post(
        "/telegram/webhook",
        headers={"Host": "api.example.com"},
        json={},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}


@pytest.mark.parametrize(
    "host",
    [
        pytest.param("unknown.example.com", id="unknown-host"),
        pytest.param(
            "api.example.com.attacker.invalid",
            id="suffix-attack",
        ),
        pytest.param("services.example.com", id="wildcard-parent-domain"),
        pytest.param("bad host", id="malformed-host"),
    ],
)
def test_untrusted_production_hosts_are_rejected(
    production_app: FastAPI,
    host: str,
) -> None:
    response = TestClient(production_app).get(
        "/health",
        headers={
            "Host": host,
            "X-Request-ID": "untrusted-host-test",
        },
        follow_redirects=False,
    )

    assert_untrusted_host_response(response)
    assert response.headers["x-request-id"] == "untrusted-host-test"


def test_x_forwarded_host_does_not_override_host(production_app: FastAPI) -> None:
    response = TestClient(production_app).get(
        "/health",
        headers={
            "Host": "attacker.invalid",
            "X-Forwarded-Host": "api.example.com",
        },
    )

    assert_untrusted_host_response(response)


def test_untrusted_host_value_is_absent_from_response_and_application_log(
    production_app: FastAPI,
    http_error_log: pytest.LogCaptureFixture,
) -> None:
    sentinel = "SENTINEL_HOST_SECRET_DO_NOT_LEAK.invalid"

    response = TestClient(production_app).get(
        "/health",
        headers={"Host": sentinel},
    )

    assert_untrusted_host_response(response)
    assert sentinel not in response.text
    assert sentinel not in str(response.headers)
    assert sentinel not in http_error_log.text
    assert "public_request_error code=untrusted_host" in http_error_log.text


@pytest.mark.parametrize(
    ("method", "path"),
    [
        pytest.param("GET", "/health", id="health"),
        pytest.param("POST", "/telegram/webhook", id="telegram-webhook"),
    ],
)
def test_untrusted_host_blocks_every_allowed_route(
    production_app: FastAPI,
    method: str,
    path: str,
) -> None:
    response = TestClient(production_app).request(
        method,
        path,
        headers={"Host": "attacker.invalid"},
        json={} if method == "POST" else None,
    )

    assert_untrusted_host_response(response)


def build_side_effect_app(counter: dict[str, int]) -> FastAPI:
    application = FastAPI()
    setup_exception_handlers(application)

    @application.get("/side-effect")
    async def side_effect() -> dict[str, bool]:
        counter["calls"] += 1
        return {"called": True}

    application.add_middleware(
        SafeTrustedHostMiddleware,
        allowed_hosts=["api.example.com"],
        www_redirect=False,
    )
    application.add_middleware(CorrelationIdMiddleware)
    return application


def test_untrusted_host_never_calls_route_handler() -> None:
    counter = {"calls": 0}
    application = build_side_effect_app(counter)

    response = TestClient(application).get(
        "/side-effect",
        headers={"Host": "attacker.invalid"},
    )

    assert_untrusted_host_response(response)
    assert counter == {"calls": 0}


async def invoke_asgi_without_host(application: FastAPI) -> list[dict[str, Any]]:
    scope: dict[str, Any] = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/side-effect",
        "raw_path": b"/side-effect",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("api.example.com", 443),
    }
    messages: list[dict[str, Any]] = []
    request_sent = False

    async def receive() -> dict[str, Any]:
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await application(scope, receive, send)
    return messages


def response_from_asgi_messages(
    messages: Sequence[dict[str, Any]],
) -> tuple[int, dict[str, str], dict[str, Any]]:
    start = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    headers = {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in start["headers"]
    }
    return start["status"], headers, json.loads(body)


def test_missing_host_is_rejected_before_handler() -> None:
    counter = {"calls": 0}
    messages = asyncio.run(invoke_asgi_without_host(build_side_effect_app(counter)))
    status_code, headers, body = response_from_asgi_messages(messages)

    assert status_code == 400
    assert headers["content-type"] == "application/json"
    assert body == {
        "ok": False,
        "error": {
            "code": "untrusted_host",
            "message": PUBLIC_ERROR_MESSAGES["untrusted_host"],
        },
        "request_id": headers["x-request-id"],
    }
    assert counter == {"calls": 0}
