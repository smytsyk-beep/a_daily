from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from httpx import Response
from pydantic import BaseModel

from common.error_handling import PUBLIC_ERROR_MESSAGES, setup_exception_handlers
from common.http_security import CorrelationIdMiddleware, REQUEST_ID_PATTERN


UNSAFE_DETAIL = "SENTINEL_HTTP_DETAIL_DO_NOT_LEAK"
SECRET_SENTINELS = (
    "SENTINEL_EXCEPTION_SECRET_DO_NOT_LEAK",
    "postgresql://private-user:private-password@private-db/private-data",
    "fake-bot-token:123456789",
    "InternalPaymentProcessorClass",
    "SENTINEL_STACK_MARKER",
    "SENTINEL_QUERY_STRING_DO_NOT_LEAK",
)


class SafeResponse(BaseModel):
    value: int


class ValidationPayload(BaseModel):
    count: int


def build_error_app() -> FastAPI:
    application = FastAPI()
    setup_exception_handlers(application)

    @application.get("/method")
    async def method_route() -> dict[str, bool]:
        return {"ok": True}

    @application.get("/http/{status_code}")
    async def http_error(status_code: int) -> None:
        raise HTTPException(
            status_code=status_code,
            detail=UNSAFE_DETAIL,
            headers={"X-Unsafe-Detail": UNSAFE_DETAIL},
        )

    @application.get("/validated")
    async def validated(limit: int) -> dict[str, int]:
        return {"limit": limit}

    @application.post("/validated-body")
    async def validated_body(payload: ValidationPayload) -> dict[str, int]:
        return {"count": payload.count}

    @application.get("/bad-response", response_model=SafeResponse)
    async def bad_response() -> dict[str, str]:
        return {"value": UNSAFE_DETAIL}

    @application.get("/explode")
    async def explode() -> None:
        raise RuntimeError(" | ".join(SECRET_SENTINELS))

    application.add_middleware(CorrelationIdMiddleware)
    return application


@pytest.fixture
def error_client() -> TestClient:
    return TestClient(build_error_app(), raise_server_exceptions=False)


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


def assert_public_error(
    response: Response,
    *,
    status_code: int,
    code: str,
) -> None:
    assert response.status_code == status_code
    assert response.headers["content-type"] == "application/json"
    request_id = response.headers["x-request-id"]
    assert response.json() == {
        "ok": False,
        "error": {
            "code": code,
            "message": PUBLIC_ERROR_MESSAGES[code],
        },
        "request_id": request_id,
    }


@pytest.mark.parametrize(
    ("method", "path", "status_code", "code"),
    [
        pytest.param("GET", "/missing", 404, "not_found", id="not-found"),
        pytest.param(
            "POST", "/method", 405, "method_not_allowed", id="method-not-allowed"
        ),
        pytest.param("GET", "/http/400", 400, "bad_request", id="bad-request"),
        pytest.param("GET", "/http/401", 401, "unauthorized", id="unauthorized"),
        pytest.param("GET", "/http/403", 403, "forbidden", id="forbidden"),
        pytest.param("GET", "/http/409", 409, "conflict", id="conflict"),
        pytest.param("GET", "/http/429", 429, "rate_limited", id="rate-limited"),
        pytest.param(
            "GET",
            "/validated?limit=not-an-integer",
            422,
            "validation_error",
            id="validation-error",
        ),
    ],
)
def test_public_4xx_error_matrix_is_stable_and_safe(
    error_client: TestClient,
    http_error_log: pytest.LogCaptureFixture,
    method: str,
    path: str,
    status_code: int,
    code: str,
) -> None:
    response = error_client.request(method, path)

    assert_public_error(response, status_code=status_code, code=code)
    assert UNSAFE_DETAIL not in response.text
    assert UNSAFE_DETAIL not in str(response.headers)
    assert UNSAFE_DETAIL not in http_error_log.text
    if code == "validation_error":
        assert "not-an-integer" not in response.text
        assert "not-an-integer" not in http_error_log.text


def test_validation_error_does_not_return_request_body(
    error_client: TestClient,
    http_error_log: pytest.LogCaptureFixture,
) -> None:
    sentinel = "SENTINEL_VALIDATION_INPUT_DO_NOT_LEAK"

    response = error_client.post(
        "/validated-body",
        json={"count": sentinel},
    )

    assert_public_error(response, status_code=422, code="validation_error")
    assert sentinel not in response.text
    assert sentinel not in str(response.headers)
    assert sentinel not in http_error_log.text


def test_response_validation_failure_is_safe_500(error_client: TestClient) -> None:
    response = error_client.get("/bad-response")

    assert_public_error(response, status_code=500, code="internal_error")
    assert UNSAFE_DETAIL not in response.text
    assert UNSAFE_DETAIL not in str(response.headers)


def test_unhandled_exception_and_logs_disclose_no_internals(
    error_client: TestClient,
    http_error_log: pytest.LogCaptureFixture,
) -> None:
    response = error_client.get(
        "/explode?probe=SENTINEL_QUERY_STRING_DO_NOT_LEAK",
        headers={"Authorization": "Bearer SENTINEL_AUTHORIZATION_DO_NOT_LEAK"},
    )

    assert_public_error(response, status_code=500, code="internal_error")
    rendered = response.text + str(response.headers) + http_error_log.text
    for sentinel in (*SECRET_SENTINELS, "SENTINEL_AUTHORIZATION_DO_NOT_LEAK"):
        assert sentinel not in rendered
    for internal_marker in (
        "RuntimeError",
        "ValueError",
        "Exception",
        "traceback",
        'File "',
        "line ",
    ):
        assert internal_marker not in rendered
    assert "public_request_error code=internal_error" in http_error_log.text
    assert "route=/explode status=500" in http_error_log.text


def test_safe_incoming_request_id_is_preserved(error_client: TestClient) -> None:
    response = error_client.get(
        "/missing",
        headers={"X-Request-ID": "client.safe-id_123"},
    )

    assert response.headers["x-request-id"] == "client.safe-id_123"
    assert response.json()["request_id"] == "client.safe-id_123"


@pytest.mark.parametrize(
    "invalid_request_id",
    [
        pytest.param("contains spaces", id="spaces"),
        pytest.param("secret:value", id="unsupported-punctuation"),
        pytest.param("x" * 129, id="too-long"),
    ],
)
def test_invalid_request_id_is_replaced(
    error_client: TestClient,
    invalid_request_id: str,
) -> None:
    response = error_client.get(
        "/missing",
        headers={"X-Request-ID": invalid_request_id},
    )

    request_id = response.headers["x-request-id"]
    assert request_id != invalid_request_id
    assert response.json()["request_id"] == request_id
    assert REQUEST_ID_PATTERN.fullmatch(request_id)
    assert uuid.UUID(request_id)


def test_success_response_also_has_request_id(error_client: TestClient) -> None:
    response = error_client.get("/method")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert REQUEST_ID_PATTERN.fullmatch(response.headers["x-request-id"])


async def invoke_with_raw_request_id(raw_request_id: bytes) -> list[dict[str, Any]]:
    application = build_error_app()
    scope: dict[str, Any] = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/missing",
        "raw_path": b"/missing",
        "query_string": b"",
        "headers": [(b"x-request-id", raw_request_id)],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 443),
    }
    messages: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await application(scope, receive, send)
    return messages


@pytest.mark.parametrize(
    "raw_request_id",
    [
        pytest.param(b"unsafe\r\ninjected", id="crlf"),
        pytest.param(b"unsafe\x00control", id="control-character"),
    ],
)
def test_control_characters_in_request_id_are_replaced(raw_request_id: bytes) -> None:
    messages = asyncio.run(invoke_with_raw_request_id(raw_request_id))
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
    request_id = headers["x-request-id"]

    assert raw_request_id.decode("latin-1") != request_id
    assert json.loads(body)["request_id"] == request_id
    assert uuid.UUID(request_id)


def test_public_error_code_set_is_small_and_canonical() -> None:
    assert PUBLIC_ERROR_MESSAGES == {
        "bad_request": "Invalid request",
        "untrusted_host": "Invalid host",
        "unauthorized": "Authentication required",
        "forbidden": "Access forbidden",
        "not_found": "Resource not found",
        "method_not_allowed": "Method not allowed",
        "conflict": "Request conflict",
        "validation_error": "Request validation failed",
        "rate_limited": "Too many requests",
        "internal_error": "Internal server error",
    }
