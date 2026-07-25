from __future__ import annotations

import hmac
import logging
import secrets
import time
from hashlib import sha256
from typing import Any

from security.modules.headers.models import CSRFConfig

logger = logging.getLogger("gula.security.modules.headers.csrf")


class CSRFProtector:
    def __init__(self, config: CSRFConfig | None = None) -> None:
        self._config = config or CSRFConfig()
        self._secret = secrets.token_hex(32)
        self._token_store: dict[str, dict[str, Any]] = {}

    def generate_token(self, session_id: str = "") -> str:
        raw = f"{session_id}:{self._secret}:{int(time.time())}:{secrets.token_hex(8)}"
        token = sha256(raw.encode()).hexdigest()
        self._store_token(token, session_id)
        return token

    def validate_token(self, token: str, session_id: str = "") -> bool:
        if self._is_exempt_method("GET"):
            return True

        expected = self._derive_token(session_id)
        if not expected:
            return False

        return hmac.compare_digest(expected, token)

    def validate_request(self, method: str, token: str, session_id: str = "") -> bool:
        if method.upper() in {m.upper() for m in self._config.exempt_methods}:
            return True

        return self.validate_token(token, session_id)

    def validate_double_submit_cookie(self, cookie_token: str, header_token: str) -> bool:
        if not cookie_token or not header_token:
            return False
        return hmac.compare_digest(cookie_token, header_token)

    def generate_cookie_token(self, session_id: str = "") -> str:
        token = secrets.token_urlsafe(self._config.token_length)
        self._store_token(token, session_id)
        return token

    def validate_referer_origin(self, request_origin: str, request_referer: str, allowed_domains: list[str]) -> bool:
        origin = request_origin or request_referer
        if not origin:
            return False

        from urllib.parse import urlparse
        try:
            parsed = urlparse(origin)
            hostname = parsed.hostname or ""
        except Exception:
            return False

        for domain in allowed_domains:
            if hostname == domain or hostname.endswith(f".{domain}"):
                return True
        return False

    def get_cookie_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "key": self._config.cookie_name,
            "httponly": False,
            "secure": self._config.cookie_secure,
            "samesite": self._config.cookie_samesite,
        }
        return attrs

    def create_dependency(self) -> Any:
        try:
            from fastapi import HTTPException, Request

            async def csrf_dependency(request: Request) -> None:
                if request.method.upper() in {m.upper() for m in self._config.exempt_methods}:
                    return

                csrf_token = request.headers.get(self._config.header_name, "")
                cookie_token = request.cookies.get(self._config.cookie_name, "")

                if csrf_token and cookie_token:
                    if self.validate_double_submit_cookie(cookie_token, csrf_token):
                        return

                valid = self.validate_token(csrf_token)
                if not valid:
                    raise HTTPException(status_code=403, detail="CSRF validation failed")

            return csrf_dependency
        except ImportError:
            logger.warning("FastAPI not available for CSRF dependency")

            async def noop_dependency() -> None:
                pass

            return noop_dependency

    def create_middleware(self, app: Any, allowed_origins: list[str] | None = None) -> Any:
        try:
            from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
            from starlette.requests import Request
            from starlette.responses import Response

            origins = allowed_origins or []

            class CSRFMiddleware(BaseHTTPMiddleware):
                def __init__(self, app: Any, protector: CSRFProtector) -> None:
                    super().__init__(app)
                    self._protector = protector

                async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
                    if request.method.upper() in {m.upper() for m in self._protector._config.exempt_methods}:
                        return await call_next(request)

                    token = request.headers.get(self._protector._config.header_name, "")
                    cookie_token = request.cookies.get(self._protector._config.cookie_name, "")

                    if cookie_token and token:
                        if self._protector.validate_double_submit_cookie(cookie_token, token):
                            return await call_next(request)

                    origin = request.headers.get("origin", "")
                    referer = request.headers.get("referer", "")
                    if origins and self._protector.validate_referer_origin(origin, referer, origins):
                        return await call_next(request)

                    if self._protector.validate_token(token):
                        return await call_next(request)

                    from starlette.responses import JSONResponse
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF validation failed"},
                    )

            return CSRFMiddleware(app, self)
        except ImportError:
            logger.warning("Starlette not available for CSRF middleware")
            return app

    def _derive_token(self, session_id: str) -> str | None:
        if session_id in self._token_store:
            return self._token_store[session_id].get("token")
        return None

    def _store_token(self, token: str, session_id: str) -> None:
        self._token_store[session_id] = {"token": token, "created_at": time.time()}

    def _is_exempt_method(self, method: str) -> bool:
        return method.upper() in {m.upper() for m in self._config.exempt_methods}
