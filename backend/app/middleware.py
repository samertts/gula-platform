"""Middleware classes for GULA Platform.

Separated from main.py to avoid circular imports with factory.py.
All middleware class definitions live here; they are registered by the factory.
"""

from __future__ import annotations

import logging
import os
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import APP_VERSION, IS_PRODUCTION, MAX_REQUEST_BODY_MB
from .core.logging_config import bind_log_context

logger = logging.getLogger("gula")

_ALWAYS_ALLOWED_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/health/ready",
        "/health/live",
        "/health/status",
        "/health/deep",
        "/health/kernel",
    }
)


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies."""

    def __init__(self, app, max_size_mb: int = 10):
        super().__init__(app)
        self._max_bytes = max_size_mb * 1024 * 1024

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self._max_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": f"Request body too large (max {MAX_REQUEST_BODY_MB}MB)",
                    "detail_ar": f"حجم البيانات أكبر من المسموح به ({MAX_REQUEST_BODY_MB} ميغابايت)",
                },
            )
        return await call_next(request)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a unique ID to every request for tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        bind_log_context(request_id=request_id)
        from .database import _endpoint_var, _request_id_var

        rid_token = _request_id_var.set(request_id)
        ep_token = _endpoint_var.set(request.url.path)
        try:
            response = await call_next(request)
        finally:
            _request_id_var.reset(rid_token)
            _endpoint_var.reset(ep_token)
        response.headers["X-Request-ID"] = request_id
        return response


_SILENT_PATHS: frozenset[str] = frozenset({"/health", "/health/ready", "/health/live"})


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Emit a structured access-log line per request."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        status = response.status_code
        path = request.url.path
        if path not in _SILENT_PATHS:
            log_fn = logger.warning if elapsed_ms > 2000 or status >= 500 else logger.info
            log_fn(
                "%s %s %d",
                request.method, path, status,
                extra={"path": path, "latency_ms": elapsed_ms, "status": status},
            )
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
        response.headers["X-API-Version"] = APP_VERSION
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/assets/") or path.endswith((".css", ".js", ".png", ".ico")):
            return response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; connect-src 'self' https://gula-platform.org; "
            "font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        if request.method == "GET" and request.url.path in _ALWAYS_ALLOWED_PATHS:
            response.headers["Cache-Control"] = "public, max-age=10, stale-while-revalidate=5"
        else:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class ReadinessMiddleware(BaseHTTPMiddleware):
    """Reject non-whitelisted requests with 503 until startup guard passes."""

    async def dispatch(self, request: Request, call_next):
        from .core.startup_guard import system_ready

        if not system_ready and request.url.path not in _ALWAYS_ALLOWED_PATHS:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Service is starting up. Please retry in a moment.",
                    "detail_ar": "الخدمة تبدأ التشغيل. يرجى المحاولة بعد لحظة.",
                },
            )
        return await call_next(request)


class DocsAuthMiddleware(BaseHTTPMiddleware):
    """Guard /docs, /redoc, /openapi.json behind admin JWT in production."""

    _PROTECTED = {"/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path not in self._PROTECTED:
            return await call_next(request)
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Authentication required"})
        from .security.auth import decode_token

        payload = decode_token(token)
        if not payload or payload.get("role") not in ("admin", "master_admin"):
            return JSONResponse(status_code=403, content={"detail": "Admin access required"})
        return await call_next(request)


class KernelMiddleware(BaseHTTPMiddleware):
    """Attach kernel context to every request."""

    async def dispatch(self, request: Request, call_next):
        from .kernel.integration import kernel_middleware

        return await kernel_middleware(request, call_next)


_MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_REQUESTS", "200"))

_CRITICAL_PATH_PREFIXES: tuple = (
    "/results",
    "/orders",
    "/samples",
    "/critical-alerts",
)


def _is_critical_write(method: str, path: str) -> bool:
    return method in ("POST", "PUT", "PATCH") and any(
        path.startswith(p) for p in _CRITICAL_PATH_PREFIXES
    )


class ConcurrencyLimitMiddleware(BaseHTTPMiddleware):
    """Return 503 when server is handling too many requests.

    Clinical write operations are always allowed through.
    """

    _active: int = 0
    _instance: ConcurrencyLimitMiddleware | None = None

    def __init__(self, app, max_concurrent: int = _MAX_CONCURRENT):
        super().__init__(app)
        self._max = max_concurrent
        ConcurrencyLimitMiddleware._instance = self

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _ALWAYS_ALLOWED_PATHS:
            return await call_next(request)
        if _is_critical_write(request.method, request.url.path):
            return await call_next(request)
        if ConcurrencyLimitMiddleware._active >= self._max:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Server busy — try again shortly",
                    "detail_ar": "الخادم مشغول — حاول مرة أخرى بعد لحظة",
                    "retry_after": 5,
                },
                headers={"Retry-After": "5"},
            )
        ConcurrencyLimitMiddleware._active += 1
        try:
            return await call_next(request)
        finally:
            ConcurrencyLimitMiddleware._active -= 1
