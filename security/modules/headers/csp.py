from __future__ import annotations

import hashlib
import logging
import secrets
from base64 import urlsafe_b64encode
from typing import Any

from security.modules.headers.models import CSPConfig

logger = logging.getLogger("gula.security.modules.headers.csp")

_CSP_DIRECTIVES = {
    "default-src": ["'self'"],
    "script-src": ["'self'"],
    "style-src": ["'self'"],
    "img-src": ["'self'", "data:", "https:"],
    "connect-src": ["'self'"],
    "font-src": ["'self'"],
    "frame-src": ["'self'"],
    "object-src": ["'none'"],
    "media-src": ["'self'"],
    "manifest-src": ["'self'"],
    "worker-src": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
    "base-uri": ["'self'"],
}


class CSPBuilder:
    def __init__(self, config: CSPConfig | None = None) -> None:
        self._config = config or CSPConfig()
        self._directives: dict[str, list[str]] = {}
        self._nonces: dict[str, str] = {}
        self._hashes: dict[str, list[str]] = {}
        for directive, sources in _CSP_DIRECTIVES.items():
            self._directives[directive] = list(sources)

    def set_directive(self, directive: str, sources: list[str]) -> None:
        self._directives[directive] = list(sources)

    def add_source(self, directive: str, source: str) -> None:
        if directive not in self._directives:
            self._directives[directive] = []
        if source not in self._directives[directive]:
            self._directives[directive].append(source)

    def remove_source(self, directive: str, source: str) -> None:
        if directive in self._directives:
            self._directives[directive] = [s for s in self._directives[directive] if s != source]

    def generate_nonce(self, length: int = 32) -> str:
        nonce = urlsafe_b64encode(secrets.token_bytes(length)).rstrip(b"=").decode()
        return nonce

    def add_nonce(self, directive: str, nonce: str | None = None) -> str:
        n = nonce or self.generate_nonce()
        self._directives.setdefault(directive, [])
        self._nonces[f"{directive}:{n}"] = n
        return n

    def add_hash(self, directive: str, content: str, algorithm: str = "sha256") -> str:
        if algorithm == "sha256":
            digest = hashlib.sha256(content.encode()).digest()
        elif algorithm == "sha384":
            digest = hashlib.sha384(content.encode()).digest()
        elif algorithm == "sha512":
            digest = hashlib.sha512(content.encode()).digest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        hash_b64 = urlsafe_b64encode(digest).rstrip(b"=").decode()
        hash_str = f"'{algorithm}-{hash_b64}'"
        key = f"{directive}:{algorithm}"
        if key not in self._hashes:
            self._hashes[key] = []
        if hash_str not in self._hashes[key]:
            self._hashes[key].append(hash_str)
        self._directives.setdefault(directive, [])
        return hash_str

    def build(self, request_nonce: str | None = None) -> str:
        parts: list[str] = []

        for directive, sources in self._directives.items():
            if not sources:
                continue
            value = " ".join(sources)
            parts.append(f"{directive} {value}")

        if request_nonce:
            for i, directive in enumerate(self._directives):
                if directive in ("script-src", "style-src", "default-src"):
                    self._directives[directive].append(f"'nonce-{request_nonce}'")

        if self._config.upgrade_insecure_requests:
            parts.append("upgrade-insecure-requests")

        if self._config.enforce_trusted_types:
            parts.append("require-trusted-types-for 'script'")

        if self._config.report_uri:
            parts.append(f"report-uri {self._config.report_uri}")

        if self._config.report_to:
            parts.append(f"report-to {self._config.report_to}")

        return "; ".join(parts)

    def build_header_value(self, request_nonce: str | None = None) -> str:
        csp_value = self.build(request_nonce)
        if self._config.report_only:
            return csp_value
        return csp_value

    def get_header_name(self) -> str:
        if self._config.report_only:
            return "Content-Security-Policy-Report-Only"
        return "Content-Security-Policy"

    def create_middleware(self, app: Any) -> Any:
        try:
            from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
            from starlette.requests import Request
            from starlette.responses import Response

            class CSPMiddleware(BaseHTTPMiddleware):
                def __init__(self, app: Any, builder: CSPBuilder) -> None:
                    super().__init__(app)
                    self._builder = builder

                async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
                    nonce = self._builder.generate_nonce()
                    request.state.csp_nonce = nonce
                    response = await call_next(request)
                    header_name = self._builder.get_header_name()
                    header_value = self._builder.build(request_nonce=nonce)
                    response.headers[header_name] = header_value
                    return response

            return CSPMiddleware(app, self)
        except ImportError:
            logger.warning("Starlette not available for CSP middleware")
            return app

    def reset(self) -> None:
        self._directives = {}
        for directive, sources in _CSP_DIRECTIVES.items():
            self._directives[directive] = list(sources)
        self._nonces.clear()
        self._hashes.clear()

    def to_dict(self) -> dict[str, list[str]]:
        return dict(self._directives)

    def get_config(self) -> CSPConfig:
        return self._config
