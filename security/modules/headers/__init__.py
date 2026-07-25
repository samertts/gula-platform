GSF-008: Headers Module — Zero-Trust HTTP security headers.

Provides comprehensive HTTP security header management for the GULA
platform including Content Security Policy (CSP), Strict Transport
Security (HSTS), Cross-Origin-Resource-Policy (CORP), Cross-Origin-Embedder-Policy
(COEP), and Subresource Integrity (SRI). Enforces browser security
protections for the GULA web frontend.

Exports:
    SecurityHeadersMiddleware: ASGI middleware for security headers
    ContentSecurityPolicy: CSP builder and validator
    HstsEnforcer: HTTP Strict Transport Security
    CrossOriginPolicy: CORP, COEP, CORB configuration
    SriManager: Subresource Integrity hash management
    HeaderReporter: Report-URI/report-to endpoint handler
"""

from security.modules.headers.middleware import SecurityHeadersMiddleware
from security.modules.headers.csp import ContentSecurityPolicy
from security.modules.headers.hsts import HstsEnforcer
from security.modules.headers.cross_origin import CrossOriginPolicy
from security.modules.headers.sri import SriManager
from security.modules.headers.reporting import HeaderReporter

__all__ = [
    "SecurityHeadersMiddleware",
    "ContentSecurityPolicy",
    "HstsEnforcer",
    "CrossOriginPolicy",
    "SriManager",
    "HeaderReporter",
]
