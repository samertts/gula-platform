from __future__ import annotations

import logging
import re
from typing import Any

from security.modules.headers.models import CORSConfig

logger = logging.getLogger("gula.security.modules.headers.cors")


class StrictCORSManager:
    def __init__(self, config: CORSConfig | None = None) -> None:
        self._config = config or CORSConfig()
        self._origin_allowed: list[re.Pattern] = []
        self._endpoint_methods: dict[str, set[str]] = {}
        self._tenant_origins: dict[str, list[str]] = {}

        for origin in self._config.allow_origins:
            try:
                pattern = re.compile(re.escape(origin).replace(r"\*", ".*"))
                self._origin_allowed.append(pattern)
            except re.error:
                logger.warning("Invalid origin pattern: %s", origin)

    def is_origin_allowed(self, origin: str) -> bool:
        if not origin:
            return False

        if origin in self._config.allow_origins:
            return True

        for pattern in self._origin_allowed:
            if pattern.fullmatch(origin):
                return True

        return False

    def get_cors_headers(
        self,
        origin: str,
        request_method: str = "GET",
        request_headers: list[str] | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, str]:
        headers: dict[str, str] = {}

        allowed_origin = self._resolve_origin(origin, tenant_id)
        if not allowed_origin:
            return {}

        headers["Access-Control-Allow-Origin"] = allowed_origin

        if self._config.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"

        if request_method == "OPTIONS":
            methods = self._get_allowed_methods()
            headers["Access-Control-Allow-Methods"] = ", ".join(methods)

            allowed_headers = self._get_allowed_headers(request_headers)
            headers["Access-Control-Allow-Headers"] = ", ".join(allowed_headers)

            if self._config.max_age > 0:
                headers["Access-Control-Max-Age"] = str(self._config.max_age)

        if self._config.expose_headers:
            headers["Access-Control-Expose-Headers"] = ", ".join(self._config.expose_headers)

        headers["Vary"] = "Origin"

        return headers

    def _resolve_origin(self, origin: str, tenant_id: str | None = None) -> str:
        if not origin:
            return ""

        if tenant_id and tenant_id in self._tenant_origins:
            tenant_allowed = self._tenant_origins[tenant_id]
            if origin in tenant_allowed:
                return origin
            for pattern_str in tenant_allowed:
                try:
                    pattern = re.compile(re.escape(pattern_str).replace(r"\*", ".*"))
                    if pattern.fullmatch(origin):
                        return origin
                except re.error:
                    pass
            return ""

        if origin in self._config.allow_origins:
            return origin

        for pattern in self._origin_allowed:
            if pattern.fullmatch(origin):
                return origin

        return ""

    def _get_allowed_methods(self) -> list[str]:
        if self._config.allow_methods:
            return self._config.allow_methods
        return ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

    def _get_allowed_headers(self, request_headers: list[str] | None = None) -> list[str]:
        allowed = list(self._config.allow_headers)
        if request_headers:
            for h in request_headers:
                h_lower = h.lower()
                if h_lower not in (a.lower() for a in allowed):
                    if h_lower not in _BLOCKED_HEADERS:
                        allowed.append(h)
        return allowed

    def set_endpoint_methods(self, path: str, methods: list[str]) -> None:
        self._endpoint_methods[path] = set(m.upper() for m in methods)

    def add_tenant_origin(self, tenant_id: str, origin: str) -> None:
        if tenant_id not in self._tenant_origins:
            self._tenant_origins[tenant_id] = []
        if origin not in self._tenant_origins[tenant_id]:
            self._tenant_origins[tenant_id].append(origin)

    def create_middleware(self, app: Any) -> Any:
        try:
            from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
            from starlette.requests import Request
            from starlette.responses import Response

            class CORSMiddleware(BaseHTTPMiddleware):
                def __init__(self, app: Any, mgr: StrictCORSManager) -> None:
                    super().__init__(app)
                    self._mgr = mgr

                async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
                    origin = request.headers.get("origin", "")
                    method = request.method
                    req_headers_str = request.headers.get("access-control-request-headers", "")
                    req_headers = [h.strip() for h in req_headers_str.split(",") if h.strip()] if req_headers_str else None

                    if method == "OPTIONS":
                        response = Response(status_code=204)
                    else:
                        response = await call_next(request)

                    cors_headers = self._mgr.get_cors_headers(origin, method, req_headers)
                    for name, value in cors_headers.items():
                        response.headers[name] = value

                    return response

            return CORSMiddleware(app, self)
        except ImportError:
            logger.warning("Starlette not available for CORS middleware")
            return app

    def get_config(self) -> CORSConfig:
        return self._config


_BLOCKED_HEADERS = {
    "host",
    "origin",
    "referer",
    "cookie",
    "set-cookie",
    "authorization",
    "proxy-authorization",
    "via",
    "x-forwarded-for",
    "x-forwarded-host",
    "x-forwarded-proto",
}
