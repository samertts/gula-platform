from __future__ import annotations

import logging
import time
from typing import Any, Callable

from security.modules.headers.cors import StrictCORSManager
from security.modules.headers.csp import CSPBuilder
from security.modules.headers.csrf import CSRFProtector
from security.modules.headers.models import SecurityHeadersConfig
from security.modules.headers.sanitizer import InputSanitizer
from security.modules.headers.security_headers import SecurityHeadersManager

logger = logging.getLogger("gula.security.modules.headers.middleware")


class SecurityMiddlewareFactory:
    def __init__(self, config: SecurityHeadersConfig | None = None) -> None:
        self._config = config or SecurityHeadersConfig()
        self._csp = CSPBuilder(self._config.csp)
        self._headers_mgr = SecurityHeadersManager(self._config.headers)
        self._cors_mgr = StrictCORSManager(self._config.cors)
        self._csrf = CSRFProtector(self._config.csrf)
        self._sanitizer = InputSanitizer()
        self._custom_processors: list[Callable] = []

    def add_processor(self, processor: Callable) -> None:
        self._custom_processors.append(processor)

    def create_middleware(self, app: Any, sensitive_paths: list[str] | None = None) -> Any:
        try:
            from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
            from starlette.requests import Request
            from starlette.responses import Response

            sensitive = set(sensitive_paths or [])
            factory = self

            class CompositeSecurityMiddleware(BaseHTTPMiddleware):
                def __init__(self, app: Any) -> None:
                    super().__init__(app)

                async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
                    start_time = time.time()

                    origin = request.headers.get("origin", "")
                    method = request.method

                    cors_headers = factory._cors_mgr.get_cors_headers(origin, method)

                    is_sensitive = any(request.url.path.startswith(p) for p in sensitive)

                    if hasattr(request.state, "csp_nonce"):
                        nonce = request.state.csp_nonce
                    else:
                        nonce = factory._csp.generate_nonce()
                        request.state.csp_nonce = nonce

                    csrf_token = factory._csrf.generate_token()

                    if method == "OPTIONS":
                        response = Response(status_code=204)
                    else:
                        response = await call_next(request)

                    for name, value in factory._headers_mgr.get_all_headers(sensitive=is_sensitive).items():
                        if name not in response.headers:
                            response.headers[name] = value

                    for name, value in cors_headers.items():
                        response.headers[name] = value

                    csp_header = factory._csp.get_header_name()
                    csp_value = factory._csp.build(request_nonce=nonce)
                    response.headers[csp_header] = csp_value

                    response.headers["X-CSRF-Token"] = csrf_token

                    for processor in factory._custom_processors:
                        try:
                            processor(request, response)
                        except Exception as exc:
                            logger.warning("Custom security processor error: %s", exc)

                    response.headers["X-Response-Time-Ms"] = str(int((time.time() - start_time) * 1000))

                    return response

            return CompositeSecurityMiddleware(app)
        except ImportError:
            logger.warning("Starlette not available for security middleware")
            return app

    def create_csp_middleware(self, app: Any) -> Any:
        return self._csp.create_middleware(app)

    def create_security_headers_middleware(self, app: Any, sensitive_paths: list[str] | None = None) -> Any:
        return self._headers_mgr.create_middleware(app, sensitive_paths)

    def create_cors_middleware(self, app: Any) -> Any:
        return self._cors_mgr.create_middleware(app)

    def create_csrf_middleware(self, app: Any, allowed_origins: list[str] | None = None) -> Any:
        return self._csrf.create_middleware(app, allowed_origins)

    def get_csp_builder(self) -> CSPBuilder:
        return self._csp

    def get_headers_manager(self) -> SecurityHeadersManager:
        return self._headers_mgr

    def get_cors_manager(self) -> StrictCORSManager:
        return self._cors_mgr

    def get_csrf_protector(self) -> CSRFProtector:
        return self._csrf

    def get_sanitizer(self) -> InputSanitizer:
        return self._sanitizer
