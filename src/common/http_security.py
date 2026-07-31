from __future__ import annotations

import re
import uuid
from collections.abc import Sequence
from typing import Final

from fastapi import Request
from starlette.datastructures import Headers, MutableHeaders
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from common.error_handling import (
    REQUEST_ID_HEADER,
    log_public_error,
    public_error_response,
)


REQUEST_ID_PATTERN: Final = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _safe_request_id(scope: Scope) -> str:
    incoming = Headers(scope=scope).get(REQUEST_ID_HEADER)
    if incoming is not None and REQUEST_ID_PATTERN.fullmatch(incoming):
        return incoming
    return str(uuid.uuid4())


class CorrelationIdMiddleware:
    """Install one bounded request ID and return it on every HTTP response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        request_id = _safe_request_id(scope)
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        await self.app(scope, receive, send_with_request_id)


class SafeTrustedHostMiddleware(TrustedHostMiddleware):
    """Starlette 0.40 host matching with the canonical JSON rejection body."""

    def __init__(
        self,
        app: ASGIApp,
        allowed_hosts: Sequence[str],
        www_redirect: bool = False,
    ) -> None:
        super().__init__(
            app,
            allowed_hosts=allowed_hosts,
            www_redirect=www_redirect,
        )

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if self.allow_any or scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        host = Headers(scope=scope).get("host", "").split(":")[0]
        is_valid_host = any(
            host == pattern or (pattern.startswith("*") and host.endswith(pattern[1:]))
            for pattern in self.allowed_hosts
        )
        if is_valid_host:
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        log_public_error(request, status_code=400, code="untrusted_host")
        response = public_error_response(
            request,
            status_code=400,
            code="untrusted_host",
        )
        await response(scope, receive, send)
