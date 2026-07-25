# GSF-004: Application Security Module

Part of the GULA Security Framework (GSF).

## Components

| Component | File | Description |
|-----------|------|-------------|
| Models | `models.py` | Pydantic configuration models |
| CSP | `csp.py` | Content Security Policy builder with nonce/hash support |
| Security Headers | `security_headers.py` | HSTS, XFO, COEP, COOP, CORP, NEL headers |
| CORS | `cors.py` | Strict CORS with origin validation, tenant-aware |
| CSRF | `csrf.py` | CSRF protection (double-submit cookie, synchronizer token) |
| Sanitizer | `sanitizer.py` | Input/output sanitization (XSS, SQLi, SSRF, path traversal) |
| Middleware | `middleware.py` | Composable security middleware pipeline |

## Integration

Provides FastAPI/Starlette middleware for:
- `SecurityMiddlewareFactory` - composite middleware (all headers)
- `CSPBuilder.create_middleware()` - CSP-only middleware
- `SecurityHeadersManager.create_middleware()` - security headers only
- `StrictCORSManager.create_middleware()` - CORS handling
- `CSRFProtector.create_middleware()` - CSRF validation
- `CSRFProtector.create_dependency()` - FastAPI dependency
