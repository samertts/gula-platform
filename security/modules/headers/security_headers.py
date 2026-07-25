from __future__ import annotations

import logging
from typing import Any

from security.modules.headers.models import HeaderConfig

logger = logging.getLogger("gula.security.modules.headers.security_headers")


class SecurityHeadersManager:
    def __init__(self, config: HeaderConfig | None = None) -> None:
        self._config = config or HeaderConfig()

    def get_hsts_header(self) -> tuple[str, str]:
        value = f"max-age={self._config.hsts_max_age}"
        if self._config.hsts_include_subdomains:
            value += "; includeSubDomains"
        if self._config.hsts_preload:
            value += "; preload"
        return ("Strict-Transport-Security", value)

    def get_x_content_type_options(self) -> tuple[str, str]:
        return ("X-Content-Type-Options", "nosniff")

    def get_x_frame_options(self) -> tuple[str, str]:
        return ("X-Frame-Options", self._config.x_frame_options)

    def get_x_xss_protection(self) -> tuple[str, str]:
        return ("X-XSS-Protection", "0")

    def get_referrer_policy(self) -> tuple[str, str]:
        return ("Referrer-Policy", self._config.referrer_policy)

    def get_permissions_policy(self) -> tuple[str, str]:
        directives: list[str] = []
        for feature, origins in self._config.permissions_policy.items():
            if not origins:
                directives.append(f"{feature}=()")
            else:
                origins_str = " ".join(origins)
                directives.append(f"{feature}=({origins_str})")
        return ("Permissions-Policy", ", ".join(directives))

    def get_coep(self) -> tuple[str, str]:
        return ("Cross-Origin-Embedder-Policy", "require-corp")

    def get_coop(self) -> tuple[str, str]:
        return ("Cross-Origin-Opener-Policy", "same-origin")

    def get_corp(self) -> tuple[str, str]:
        return ("Cross-Origin-Resource-Policy", "same-origin")

    def get_cache_control_sensitive(self) -> tuple[str, str]:
        return ("Cache-Control", "no-store, no-cache, must-revalidate, proxy-revalidate")

    def get_clear_site_data(self) -> tuple[str, str]:
        return ("Clear-Site-Data", '"cache", "cookies", "storage", "executionContexts"')

    def get_nel_header(self, report_to: str = "default", max_age: int = 2592000) -> tuple[str, str]:
        value = f'{{"report_to": "{report_to}", "max_age": {max_age}, "include_subdomains": true}}'
        return ("NEL", value)

    def get_reporting_endpoints(self, endpoints: dict[str, str] | None = None) -> tuple[str, str]:
        eps = endpoints or {"default": "/_/report"}
        value = ", ".join(f'"{name}="{url}""' for name, url in eps.items())
        return ("Reporting-Endpoints", value)

    def get_all_headers(self, sensitive: bool = True) -> dict[str, str]:
        headers: dict[str, str] = {}

        name, value = self.get_hsts_header()
        headers[name] = value

        name, value = self.get_x_content_type_options()
        headers[name] = value

        name, value = self.get_x_frame_options()
        headers[name] = value

        name, value = self.get_x_xss_protection()
        headers[name] = value

        name, value = self.get_referrer_policy()
        headers[name] = value

        name, value = self.get_permissions_policy()
        headers[name] = value

        name, value = self.get_coep()
        headers[name] = value

        name, value = self.get_coop()
        headers[name] = value

        name, value = self.get_corp()
        headers[name] = value

        if sensitive:
            name, value = self.get_cache_control_sensitive()
            headers[name] = value

        return headers

    def get_logout_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        name, value = self.get_clear_site_data()
        headers[name] = value
        name, value = self.get_cache_control_sensitive()
        headers[name] = value
        return headers

    def create_middleware(self, app: Any, sensitive_paths: list[str] | None = None) -> Any:
        try:
            from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
            from starlette.requests import Request
            from starlette.responses import Response

            sensitive = set(sensitive_paths or [])

            class SecurityHeadersMiddleware(BaseHTTPMiddleware):
                def __init__(self, app: Any, mgr: SecurityHeadersManager) -> None:
                    super().__init__(app)
                    self._mgr = mgr

                async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
                    response = await call_next(request)
                    is_sensitive = any(request.url.path.startswith(p) for p in sensitive)
                    for name, value in self._mgr.get_all_headers(sensitive=is_sensitive).items():
                        if name not in response.headers:
                            response.headers[name] = value
                    return response

            return SecurityHeadersMiddleware(app, self)
        except ImportError:
            logger.warning("Starlette not available for middleware")
            return app

    def get_config(self) -> HeaderConfig:
        return self._config
