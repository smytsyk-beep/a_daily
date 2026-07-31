from __future__ import annotations

import logging
from typing import Final

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger("astrodaily.http")

REQUEST_ID_HEADER: Final = "X-Request-ID"

PUBLIC_ERROR_MESSAGES: Final[dict[str, str]] = {
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

_HTTP_STATUS_ERRORS: Final[dict[int, str]] = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
}


def request_id_for(request: Request) -> str:
    """Return the request ID installed by correlation middleware."""

    return request.state.request_id


def public_error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
) -> JSONResponse:
    """Build the only public error envelope used by the HTTP application."""

    request_id = request_id_for(request)
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "error": {
                "code": code,
                "message": PUBLIC_ERROR_MESSAGES[code],
            },
            "request_id": request_id,
        },
        headers={REQUEST_ID_HEADER: request_id},
    )


def log_public_error(request: Request, *, status_code: int, code: str) -> None:
    """Log only stable request metadata, never exception or request contents."""

    route = request.scope.get("route")
    route_template = getattr(route, "path", "<unmatched>")
    logger.error(
        "public_request_error code=%s request_id=%s method=%s route=%s status=%d",
        code,
        request_id_for(request),
        request.method,
        route_template,
        status_code,
    )


def _http_error_code(status_code: int) -> str:
    if status_code >= 500:
        return "internal_error"
    return _HTTP_STATUS_ERRORS.get(status_code, "bad_request")


def _safe_error(
    request: Request,
    *,
    status_code: int,
    code: str,
) -> JSONResponse:
    log_public_error(request, status_code=status_code, code=code)
    return public_error_response(request, status_code=status_code, code=code)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        return _safe_error(
            request,
            status_code=exc.status_code,
            code=_http_error_code(exc.status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request,
        _exc: RequestValidationError,
    ) -> JSONResponse:
        return _safe_error(
            request,
            status_code=422,
            code="validation_error",
        )

    @app.exception_handler(ResponseValidationError)
    async def response_validation_exception_handler(
        request: Request,
        _exc: ResponseValidationError,
    ) -> JSONResponse:
        return _safe_error(
            request,
            status_code=500,
            code="internal_error",
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        _exc: Exception,
    ) -> JSONResponse:
        return _safe_error(
            request,
            status_code=500,
            code="internal_error",
        )
