"""Origin-boundary protection for cookie-authenticated state changes."""

from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("gula.security.csrf")
_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_BROWSER_MARKERS = ("mozilla", "chrome", "safari", "firefox", "edg/")


def _allowed_origins() -> set[str]:
    configured = {
        origin.strip().rstrip("/")
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    }
    configured.update({"http://localhost:5173", "http://localhost:4173", "http://localhost:3000"})
    return configured


def _origin_from_referer(referer: str | None) -> str | None:
    if not referer:
        return None
    parsed = urlparse(referer)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


class CSRFMiddleware(BaseHTTPMiddleware):
    """Reject cross-origin browser writes when an auth cookie is present.

    Native clients commonly omit Origin/Referer, so they are not rejected solely
    for missing browser headers. A browser-like user agent without either header
    is rejected to fail closed against form-based CSRF.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method not in _MUTATING_METHODS or not request.cookies.get("access_token"):
            return await call_next(request)

        supplied_origin = request.headers.get("origin") or _origin_from_referer(
            request.headers.get("referer"),
        )
        if supplied_origin and supplied_origin not in _allowed_origins():
            logger.warning(
                "CSRF origin rejected method=%s path=%s origin=%s",
                request.method,
                request.url.path,
                supplied_origin,
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Cross-origin request rejected",
                    "detail_ar": "تم رفض الطلب من مصدر غير مصرح",
                },
            )

        if not supplied_origin:
            user_agent = request.headers.get("user-agent", "").lower()
            if any(marker in user_agent for marker in _BROWSER_MARKERS):
                logger.warning(
                    "CSRF browser request missing origin method=%s path=%s",
                    request.method,
                    request.url.path,
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Origin or Referer header required",
                        "detail_ar": "يجب إرسال ترويسة Origin أو Referer",
                    },
                )

        return await call_next(request)
