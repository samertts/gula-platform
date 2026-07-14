from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from shared.logging import bind_log_context

logger = logging.getLogger("gula.middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = request.headers.get("X-Request-ID", uuid.uuid4().hex)
        bind_log_context(request_id=rid)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        logger.info(
            "ACCESS path=%s method=%s status=%d duration=%.1fms",
            request.url.path,
            request.method,
            response.status_code,
            duration_ms,
            extra={
                "latency_ms": duration_ms,
                "path": request.url.path,
                "status": response.status_code,
            },
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, max_size_mb: int = 10) -> None:
        super().__init__(app)
        self._max_bytes = max_size_mb * 1024 * 1024

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self._max_bytes:
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request body exceeds {self._max_bytes // (1024*1024)}MB limit"},
            )
        return await call_next(request)
