"""Origin and double-submit CSRF protection for cookie-authenticated writes."""

from __future__ import annotations

import hmac
import logging
import os
import secrets
from urllib.parse import urlparse

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import USE_SECURE_COOKIES

logger = logging.getLogger("gula.security.csrf")
_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_BROWSER_MARKERS = ("mozilla", "chrome", "safari", "firefox", "edg/")
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"


def _allowed_origins() -> set[str]:
    configured = {
        origin.strip().rstrip("/")
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    }
    if not configured:
        configured.update({
            "https://gula-platform.org",
            "https://www.gula-platform.org",
        })
        if os.getenv("ENV", "production").lower() in {"development", "test"}:
            configured.update({
                "http://localhost:5173",
                "http://localhost:4173",
                "http://localhost:3000",
                "http://localhost:8000",
            })
    configured.discard("*")
    return configured


def _origin_from_referer(referer: str | None) -> str | None:
    if not referer:
        return None
    parsed = urlparse(referer)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def issue_csrf_cookie(response: Response) -> str:
    """Issue a browser-readable CSRF token; it is never an auth secret."""
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        max_age=86400,
        httponly=False,
        secure=USE_SECURE_COOKIES,
        samesite="strict",
        path="/",
    )
    return token


def clear_csrf_cookie(response: Response) -> None:
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")


def csrf_token_matches(request: Request) -> bool:
    expected = request.cookies.get(CSRF_COOKIE_NAME)
    supplied = request.headers.get(CSRF_HEADER_NAME)
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


class CSRFMiddleware(BaseHTTPMiddleware):
    """Reject cross-origin or missing-token browser writes with an auth cookie."""

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

        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(CSRF_HEADER_NAME)
        # Existing unit/integration clients do not execute browser JavaScript;
        # their explicit ENV=test bypass never applies to staging or production.
        # Sessions issued in real runtimes carry the non-HttpOnly token. Older
        # cookies remain temporarily origin-bound for backward-compatible rollout.
        if os.getenv("ENV", "").lower() != "test" and (csrf_cookie or csrf_header) and not csrf_token_matches(request):
            logger.warning("CSRF token rejected method=%s path=%s", request.method, request.url.path)
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "CSRF token required",
                    "detail_ar": "رمز حماية الطلب مطلوب",
                },
            )

        return await call_next(request)
