# Security Hardening Report — GULA Platform v2.1.0

> **Assessment Date:** 2026-07-14
> **Scope:** `backend/app/` monolith (FastAPI), `shared/` library, `backend/app/security/`
> **Methodology:** Static code analysis against 20 security dimensions

---

## 1. Authentication `backend/app/security/auth.py`

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | JWT (HS256) access + refresh tokens; Redis-backed JTI blacklist; bcrypt password hashing with dummy-hash timing-safe login; cookie + Bearer header extraction; token type discrimination (access vs refresh) |
| **What's missing** | No MFA/2FA; no account-lockout after N failed attempts (rate limiting only blocks IP, not user); password complexity policy is absent at the API layer; no refresh-token rotation (old refresh token remains valid after rotation) |
| **Priority** | **HIGH** |

**Recommended fixes:**

```python
# Add account lockout to login.py (backend/app/routes/login.py)
# After failed login attempt, track in Redis:
from ..security.redis_client import cache

FAIL_KEY = f"login_fail:user:{user.id}" if user else f"login_fail:ip:{client_ip}"
attempts = cache.incr(FAIL_KEY)
if attempts == 1:
    cache.expire(FAIL_KEY, 900)  # 15-min sliding window
if attempts >= 5:
    cache.set(f"locked:{FAIL_KEY}", "1", ex=900)
    raise HTTPException(status_code=423, detail="Account temporarily locked. Try again in 15 minutes.")
```

---

## 2. Authorization `backend/app/security/rbac.py`, `dependencies.py`

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | 9 roles × extended permissions from shared.rbac; ABAC via `require_own_lab()` for tenant isolation; `require_permission()` FastAPI dependency with O(1) permission lookup; `require_role()` for role gating; `require_feature_for_lab()` with per-tenant feature flags; `assert_lab_within_limit()` for subscription caps; permission versioning (`bump_perm_version`) for instant revocation; province-level admin scoping |
| **What's missing** | Permission caching/stale detection (always computes from role at request time — acceptable for O(1) dict lookup); no attribute-based access for resource-level ownership beyond lab_id |
| **Priority** | **LOW** |

No urgent fixes needed.

---

## 3. Secrets Management `backend/app/config.py`

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | `_is_weak_secret()` detection rejects common weak patterns; `SECRET_KEY` — hard `sys.exit(1)` if missing/weak in production; `ENCRYPTION_KEY` — same hard fail; `NID_HMAC_KEY` — hard fail in production, falls back to `ENCRYPTION_KEY`/`SECRET_KEY` in dev; `REFRESH_TOKEN_SECRET` — hard fail in production; no hardcoded defaults in production (every secret requires env var); `make secrets-gen` generates strong random values |
| **What's missing** | No automated secret rotation; no external secrets backend (Vault/AWS Secrets Manager); env-file-based secrets are static until manually rotated; `SUPABASE_SERVICE_KEY`, `MOI_NID_API_KEY`, `FCM_SERVER_KEY`, `APNS_KEY`, `CF_API_TOKEN` have no weak-pattern validation |
| **Priority** | **MEDIUM** |

```python
# Add validation for all API keys in config.py (pattern already exists):
for _key_name, _key_val in [
    ("SUPABASE_SERVICE_KEY", SUPABASE_SERVICE_KEY),
    ("MOI_NID_API_KEY", MOI_NID_API_KEY),
    ("FCM_SERVER_KEY", FCM_SERVER_KEY),
    ("CF_API_TOKEN", CF_API_TOKEN),
    ("APNS_KEY", APNS_KEY),
]:
    if _key_val and IS_PRODUCTION and _is_weak_secret(_key_val):
        logger.critical("Weak %s detected in production", _key_name)
        sys.exit(1)
```

---

## 4. Encryption `backend/app/security/encryption.py`, `shared/security/encryption.py`

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | Fernet (AES-128-CBC + HMAC-SHA256) symmetric encryption; `encrypt_national_id()` — HMAC-sign-then-encrypt pattern (integrity + confidentiality); `decrypt_national_id()` verifies HMAC before decryption (prevents padding-oracle); all encryption via canonical `shared.security` library |
| **What's missing** | Key rotation mechanism for `ENCRYPTION_KEY` (must re-encrypt all stored NIDs); no key-version tagging on ciphertexts; `encrypt()`/`decrypt()` in backend app are thin wrappers (adequate) |
| **Priority** | **MEDIUM** |

```python
# Add key-version prefix to encrypted values (shared/security/encryption.py):
from cryptography.fertil import Fernet, MultiFernet

_CURRENT_KEY_VERSION = "v1"

def encrypt_value(value: str, key: str) -> str:
    f = _get_fernet(key)
    return f"{_CURRENT_KEY_VERSION}:{f.encrypt(value.encode()).decode()}"

def decrypt_value(token: str, primary_key: str, fallback_keys: list[str] | None = None) -> str:
    version, ciphertext = token.split(":", 1)
    keys = [primary_key] + (fallback_keys or [])
    ferrets = [Fernet(k.encode() if isinstance(k, str) else k) for k in keys]
    mf = MultiFernet(ferrets)
    return mf.decrypt(ciphertext.encode()).decode()
```

---

## 5. TLS `backend/app/main.py` (middleware)

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **WARNING** |
| **What works** | `Strict-Transport-Security: max-age=31536000; includeSubDomains` set on every response in production (`SecurityHeadersMiddleware`); TLS terminated at nginx `api-gateway` (Docker Compose network) |
| **What's missing** | No HSTS `preload` directive; no certificate pinning (HPKP deprecated — acceptable); no OCSP stapling configuration in nginx; no TLS version enforcement in app code (handled by nginx — needs verification) |
| **Priority** | **MEDIUM** |

```
# Add to nginx API gateway config (config/haproxy/ or api-gateway nginx):
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
```

---

## 6. Security Headers `backend/app/main.py:390-428`

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **WARNING** |
| **What works** | `X-Content-Type-Options: nosniff`; `X-Frame-Options: DENY`; `X-XSS-Protection: 1; mode=block`; `Referrer-Policy: strict-origin-when-cross-origin`; `Permissions-Policy: camera=(), microphone=(), geolocation=()`; `Cross-Origin-Opener-Policy: same-origin`; `Cache-Control: no-store, no-cache, must-revalidate` (non-health); CSP with `default-src 'self'`; HSTS (production) |
| **What's missing** | **CSP `script-src` and `style-src` include `'unsafe-inline'`** — this dramatically weakens XSS protection; no `report-uri`/`report-to` for CSP violation reporting; `Cross-Origin-Embedder-Policy` not set; stale-while-revalidate on health endpoints is acceptable |
| **Priority** | **HIGH** |

```python
# Fix CSP in SecurityHeadersMiddleware (main.py:405-416):
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' 'strict-dynamic' 'nonce-{nonce}'; "
    "style-src 'self' 'unsafe-inline'; "  # unsafe-inline required for most CSS frameworks
    "img-src 'self' data: blob:; "
    "connect-src 'self' https://gula-platform.org; "
    "font-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'; "
    "report-uri /csp-violation; "
    "report-to csp-endpoint"
)
```

---

## 7. CORS `backend/app/main.py:316-353`

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | Explicit origin whitelist via `CORS_ORIGINS` env var; production defaults to `https://gula-platform.org` only; development includes localhost + design tool origins (`aistudio.google.com`, `claude.ai`); restricted methods (`GET/POST/PUT/DELETE/PATCH/OPTIONS`); restricted headers including `Authorization`, `Content-Type`, `Idempotency-Key`; `allow_credentials=True` is correct for cookie-based auth |
| **What's missing** | No dynamic origin validation (static list only — fine for this architecture); `allow_credentials=True` with `allow_origins=[...]` can leak credentials if list is wrong |
| **Priority** | **LOW** |

No urgent fixes needed.

---

## 8. Rate Limiting `backend/app/security/rate_limit.py`

| <!-- | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | Redis-backed (shared across workers) with in-memory fallback; multi-tier: public (30/min), user (60/min), auth (10/min), admin (20/min); dual-key strategy (`user:{id}` + `ip:{addr}`) prevents rotating-IP bypass; dynamic IP hard-block on 5× threshold abuse; standardised `X-RateLimit-*` and `Retry-After` headers; bypass in `ENV=test` to avoid flaky tests |
| **What's missing** | Fixed-window algorithm (allows burst at window edge — acceptable); no rate limiting on specific sensitive endpoints beyond the generic tiers; no per-route granular limits; concurrency limiting exists in `ConcurrencyLimitMiddleware` (separate system) |
| **Priority** | **LOW** |

Consider migrating to sliding-window for tighter rate accuracy:

```python
# Sliding-window rate check (alternative to fixed-window in rate_limit.py):
def _check_sliding(key: str, max_requests: int, window_seconds: int) -> bool:
    import time as _time
    now = _time.time()
    window_key = f"rl:sliding:{key}"
    cache.zremrangebyscore(window_key, 0, now - window_seconds)
    count = cache.zcard(window_key)
    if count >= max_requests:
        return False
    cache.zadd(window_key, {str(uuid.uuid4()): now})
    cache.expire(window_key, window_seconds * 2)
    return True
```

---

## 9. SQL Injection

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | Full SQLAlchemy ORM usage with parameterized queries; no raw SQL string concatenation with user input found; `text()` calls use fixed queries (`SELECT 1`, `SELECT version_num`, `SET statement_timeout`); Pydantic input validation on all request models |
| **What's missing** | No automated SQL injection testing in CI; no SQLAlchemy event-based query inspection |
| **Priority** | **LOW** |

No fixes needed.

---

## 10. XSS

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **WARNING** |
| **What works** | CSP restricted to `self` for most directives; API returns JSON only (no HTML rendering); httpOnly cookies prevent JS access; `X-XSS-Protection: 1; mode=block`; Pydantic input validation |
| **What's missing** | **`'unsafe-inline'` in CSP `script-src`** neutralizes XSS protection for inline scripts; no explicit HTML output encoding (acceptable since API is JSON-only); no input sanitization for user-supplied text that could be displayed in dashboards |
| **Priority** | **HIGH** |

See **Security Headers** fix above for CSP hardening. Additionally, add an output sanitization helper for any user text rendered in JSON responses:

```python
# Add to shared library for HTML-safe text in JSON responses:
import html

def sanitize_display_text(text: str | None) -> str | None:
    if text is None:
        return None
    return html.escape(text, quote=True)
```

---

## 11. CSRF

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **NOT_IMPLEMENTED** |
| **What works** | Cookies set with `SameSite=Strict` (prevents cross-site cookie sending on all but top-level navigations); httpOnly cookies (cannot be read by JS); `X-Frame-Options: DENY` prevents clickjacking |
| **What's missing** | **No CSRF token mechanism** — relying solely on SameSite=Strict is insufficient. Browser support varies (Safari, older Chrome, embedded browsers). Modern frameworks like FastAPI have no built-in CSRF middleware. Any cookie-authenticated endpoint could theoretically be targeted via CSRF in non-Strict browsers |
| **Priority** | **HIGH** |

```python
# Add CSRF protection middleware (backend/app/security/csrf.py):
from __future__ import annotations

import secrets
from typing import Callable

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


class CSRFMiddleware(BaseHTTPMiddleware):
    """Protect unsafe methods with CSRF token validation.

    Strategy: Double-Submit Cookie Pattern
    - Set a random CSRF token cookie (httpOnly=False, SameSite=Lax)
    - Require the same token in X-CSRF-Token header for POST/PUT/DELETE/PATCH
    - Compare: cookie value must match header value
    """

    _SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

    async def dispatch(self, request: Request, call_next):
        if request.method not in self._SAFE_METHODS:
            # Check header against cookie (both must exist and match)
            cookie_token = request.cookies.get("csrf_token")
            header_token = request.headers.get("X-CSRF-Token")
            if not cookie_token or not header_token or cookie_token != header_token:
                raise HTTPException(
                    status_code=403,
                    detail="CSRF validation failed",
                    detail_ar="فشل التحقق من صحة الطلب",
                )

        response = await call_next(request)

        # Set/refresh CSRF cookie on every response if not present
        if "csrf_token" not in request.cookies:
            import secrets
            token = secrets.token_hex(32)
            response.set_cookie(
                key="csrf_token",
                value=token,
                max_age=86400,  # 24 hours
                path="/",
                secure=True,
                samesite="lax",
                httponly=False,  # Must be readable by JS for SPA
            )
        return response


# Register in main.py:
# from .security.csrf import CSRFMiddleware
# app.add_middleware(CSRFMiddleware)
```

---

## 12. SSRF

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **NOT_IMPLEMENTED** |
| **What works** | Nothing — no SSRF protection found |
| **What's missing** | **No URL validation or allowlisting** for external API calls. The platform integrates with government NID, insurance, and residency APIs (`MOI_NID_API_URL`, `INSURANCE_API_URL`, `RESIDENCY_API_URL`). These URLs come from env vars but are used directly with no validation. If an attacker can influence the adapter mode or URL, they could SSRF internal services. AI model calls to `OLLAMA_BASE_URL` also lack URL validation. |
| **Priority** | **CRITICAL** |

```python
# Add SSRF guard to shared library (shared/security/ssrf.py):
from __future__ import annotations

import ipaddress
import logging
from urllib.parse import urlparse

logger = logging.getLogger("gula.ssrf")

_ALLOWED_SCHEMES = frozenset({"https"})
_BLOCKED_HOSTS = frozenset({
    "169.254.169.254",  # AWS/GCP metadata
    "100.100.100.200",  # Alibaba metadata
    "metadata.google.internal",
    "169.254.169.254",
})

def validate_external_url(url: str, *, allowlist: set[str] | None = None) -> str:
    """Validate URL for SSRF safety. Returns the URL if safe, raises ValueError."""
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"URL scheme '{parsed.scheme}' not allowed (must be https)")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")
    if hostname.lower().endswith((".local", ".internal", ".localhost")):
        raise ValueError(f"URL hostname '{hostname}' is internal")
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError(f"URL resolves to private IP: {hostname}")
    except ValueError:
        # It's a hostname (not an IP) — check allowlist if provided
        if allowlist and not any(hostname.endswith(a) for a in allowlist):
            raise ValueError(f"URL hostname '{hostname}' not in allowlist")
        # Check for DNS rebinding protection: require trailing dot or 2+ labels
        if hostname.count(".") < 1 and not hostname == "localhost":
            raise ValueError(f"URL hostname '{hostname}' looks suspicious (too few labels)")
    # Block known metadata endpoints
    if hostname.lower() in _BLOCKED_HOSTS:
        raise ValueError(f"URL hostname '{hostname}' is blocked (metadata endpoint)")
    return url


# Usage in API gateway layer:
# from shared.security.ssrf import validate_external_url
# validated_url = validate_external_url(url, allowlist={"gov.iq", "gula-platform.org"})
```

---

## 13. RCE

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | No `exec()`/`eval()` in production code; no `os.system()` in production routes; AI sandbox uses explicit operation whitelist (`_REGISTRY`); `subprocess` only in test/engineering tooling (not shipped); kernel plugin loader blocks dangerous operations |
| **What's missing** | Occasional `subprocess` usage in engineering/CI scripts (acceptable — not production routes) |
| **Priority** | **LOW** |

No fixes needed.

---

## 14. Path Traversal

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** (limited surface) |
| **What works** | No file-serving endpoints in production API; audit anchor file writes use `Path` objects with fixed pattern (`ANCHOR_DIR / f"audit_anchors_{year-month}.log"`); no user-supplied path components |
| **What's missing** | No explicit path traversal prevention on any file operations; none currently needed given the architecture |
| **Priority** | **LOW** |

No fixes needed.

---

## 15. File Upload `backend/app/routes/id_scan.py`

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | Size limit: 2MB per file (5× smaller than `MAX_UPLOAD_SIZE_MB` default); request body limit: 10MB (`MaxBodySizeMiddleware`); strict content-type validation (`image/jpeg`, `image/png`, `image/webp`, `image/bmp`); minimum size check (1000 bytes) to reject corrupted files; images processed in executor (no blocking event loop) |
| **What's missing** | No virus/malware scanning; no image re-compression to strip EXIF/metadata; no file-storage quarantine period |
| **Priority** | **MEDIUM** |

```python
# Add EXIF stripping after upload (id_scan.py):
from PIL import Image
import io

def _strip_exif(image_bytes: bytes) -> bytes:
    """Remove all EXIF metadata from uploaded images."""
    img = Image.open(io.BytesIO(image_bytes))
    # Re-save without EXIF data
    output = io.BytesIO()
    img.save(output, format=img.format, exif=b"")
    return output.getvalue()

# Also consider adding ClamAV scanning via clamd socket:
# def _scan_for_viruses(contents: bytes) -> bool:
#     import clamd
#     cd = clamd.ClamdUnixSocket()
#     result = cd.instream(io.BytesIO(contents))
#     return result.get('stream', {}).get('OK', False)
```

---

## 16. Audit Trail `backend/app/services/audit_service.py`, `backend/app/models/audit_log.py`

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | SHA-256 hash-chained audit log (`chain_hash = SHA-256(prev_hash + record_data)`); HMAC-signed anchor files written to disk every 100 entries for external verification; `verify_audit_chain()` endpoint for integrity checking; genesis hash (`"0"*64`) for chain root; hash-chain survives DB restart; dual-key anchor HMAC (primary + previous key for key rotation); `chain_hash` column nullable with graceful handling of legacy rows |
| **What's missing** | No read-receipt or external SIEM forwarding; anchor files written to container-local filesystem (lost on restart unless volume-mounted); no periodic chain verification as a background task |
| **Priority** | **MEDIUM** |

```python
# Add periodic chain verification to auto_repair or health watchdog:
# (in backend/app/main.py or backend/app/core/auto_repair.py)

async def _audit_chain_verifier():
    """Daily audit chain integrity check."""
    import asyncio
    from ..services.audit_service import verify_audit_chain
    from ..database import SessionLocal

    while True:
        await asyncio.sleep(86400)  # daily
        try:
            db = SessionLocal()
            result = verify_audit_chain(db, limit=5000)
            db.close()
            if not result["verified"]:
                logger.critical(
                    "AUDIT CHAIN TAMPERED: %d broken entries found",
                    len(result["broken_entries"])
                )
        except Exception as e:
            logger.error("Audit chain verification failed: %s", e)
```

---

## 17. Logging `backend/app/core/logging_config.py`

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **WARNING** |
| **What works** | Structured JSON logging via `shared.logging.JSONFormatter`; request ID correlation via `RequestIDMiddleware`; correlation context vars for DB error logs; MPI endpoints deliberately avoid raw PII; Sentry integration for error tracking |
| **What's missing** | **No centralized PII redaction** in logging pipeline — user emails, IP addresses, and details fields could contain PII that is logged verbatim. The failed-login log hashes the email with HMAC (good), but other `details` fields receive raw data. No automated PII scrubber at the formatter level. |
| **Priority** | **HIGH** |

```python
# Add PII redaction to JSONFormatter (shared/logging.py or logging_config.py):
import re
from typing import Any

_PII_PATTERNS = [
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL_REDACTED]'),
    (re.compile(r'\b\d{13,16}\b'), '[NID_REDACTED]'),  # Iraqi NID is 14 digits
    (re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'), '[PHONE_REDACTED]'),
    (re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'), '[IP_REDACTED]'),  # optional: keep for security logs
]

class PIIRedactingJSONFormatter(JSONFormatter):
    """JSON formatter that redacts PII from log records."""

    def _redact_pii(self, value: str) -> str:
        for pattern, replacement in _PII_PATTERNS:
            value = pattern.sub(replacement, value)
        return value

    def format(self, record: logging.LogRecord) -> str:
        record.msg = self._redact_pii(record.msg)
        if record.args:
            record.args = tuple(
                self._redact_pii(str(a)) if isinstance(a, str) else a
                for a in record.args
            )
        return super().format(record)
```

---

## 18. AI Guardrails `backend/app/ai/`

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | **AI = Suggest, Human = Approve, System = Enforce** — fundamental safety pattern; `_ABSOLUTELY_BLOCKED` set (10 operations permanently blocked); immutable `AISuggestion` dataclass (frozen, always `is_approved=False` at creation); `AIGuardrailViolation` exception (must not be silently caught); sandbox with explicit operation whitelist (`_REGISTRY`); all sandbox handlers are read-only (no DB writes); `requires_doctor_review` flag on flagged outputs; clinical operations are rules-based (deterministic, not ML) |
| **What's missing** | No AI model output validation layer to detect hallucinations; no context window limits; no rate limiting on AI calls per lab; no adversarial prompt detection at the API boundary |
| **Priority** | **MEDIUM** |

```python
# Add output validation layer (backend/app/ai/output_validator.py):
from __future__ import annotations

class AIOutputValidator:
    """Validate AI output before it reaches any API response."""

    _ALLOWED_KEYS_BY_OPERATION: dict[str, set[str]] = {
        "suggest_interpretation": {"test_name", "value", "unit", "flag", "status",
                                    "interpretation", "interpretation_ar", "advice",
                                    "advice_ar", "display_only", "requires_doctor_review"},
    }

    @classmethod
    def validate(cls, operation: str, output: dict) -> dict:
        """Strip unexpected keys and enforce constraints."""
        allowed = cls._ALLOWED_KEYS_BY_OPERATION.get(operation)
        if allowed:
            output = {k: v for k, v in output.items() if k in allowed}
        # Enforce that nothing clinical gets through without display_only
        if output.get("display_only") is not False:
            output.setdefault("display_only", True)
        return output
```

---

## 19. Session Management `backend/app/security/auth.py`, `routes/login.py`, `security/session.py`

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **PASS** |
| **What works** | JWT access tokens (default 30-min expiry); refresh tokens (default 30-day expiry); Redis JTI blacklist (fast revocation); permission version bump as DB-level invalidation safety net (survives Redis restart) — via `bump_perm_version()`; 2-layer logout (Redis blacklist + DB perm_version bump); httpOnly + SameSite=Strict + Secure cookies; warm_perm_version on login for fast path; dual-key permission cache (Redis + DB fallback) |
| **What's missing** | No refresh token rotation (old token remains valid after refresh — use attack window); no absolute session timeout (e.g., force re-login every 24 hours); no concurrent session limit (user can have unlimited active sessions); no geolocation/IP-based session validation |
| **Priority** | **MEDIUM** |

```python
# Add refresh token rotation in login.py:
@router.post("/auth/refresh")
def refresh_token(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    # Decode current refresh token
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    payload = decode_refresh_token(raw_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # BLACKLIST the old refresh token (rotation)
    old_jti = payload.get("jti")
    if old_jti:
        blacklist_token(old_jti, REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    # Issue new tokens
    user = db.query(LabUser).filter(LabUser.id == payload["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    base_payload = build_token_payload(user)
    new_token = create_token(base_payload)
    new_refresh = create_refresh_token(base_payload)

    # Set cookies
    response.set_cookie(key="access_token", value=new_token, ...)
    response.set_cookie(key="refresh_token", value=new_refresh, ...)

    return {"token": new_token, "refresh_token": new_refresh}
```

---

## 20. Intrusion Detection

| <!-- --> | <!-- --> |
|----------|---------|
| **Status** | **WARNING** |
| **What works** | Rate-limit dynamic IP block (5× threshold triggers expire-based block); failed-login audit logging with email HMAC; circuit breaker for DB/Redis detects infrastructure failure; health watchdog alerts on grade transitions; Sentry for error tracking |
| **What's missing** | **No brute-force account lockout** at user level (only IP-level rate limiting); no anomaly detection for unusual access patterns (e.g., user accessing from 3 different cities in 10 minutes); no SIEM integration; no endpoint for security events stream; no automated incident response; no IDS/IPS integration documented |
| **Priority** | **HIGH** |

```python
# Add anomaly detection module (backend/app/security/anomaly.py):
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

from .redis_client import cache


@dataclass
class AnomalyEvent:
    event_type: str
    user_id: int | None
    ip: str
    details: dict
    timestamp: float


class AnomalyDetector:
    """Lightweight anomaly detection using Redis counters."""

    def check_login_velocity(self, user_id: int, ip: str) -> bool:
        """Flag if user logs in from >3 distinct IPs in 1 hour."""
        key = f"anomaly:login_ips:{user_id}:{int(time.time() / 3600)}"
        cache.sadd(key, ip)
        cache.expire(key, 7200)
        if cache.scard(key) > 3:
            return True  # Anomaly detected
        return False

    def check_geo_anomaly(self, user_id: int, geo: str) -> bool:
        """Flag if user accesses from different geography rapidly."""
        prev = cache.get(f"anomaly:geo:{user_id}")
        if prev and prev != geo:
            return True
        cache.set(f"anomaly:geo:{user_id}", geo, ex=300)
        return False

    def report(self, event: AnomalyEvent) -> None:
        """Write anomaly event to alert system."""
        logger.warning(
            "[ANOMALY] type=%s user=%s ip=%s details=%s",
            event.event_type, event.user_id, event.ip, event.details
        )
        # Could also push to webhook or SIEM here
```

---

# Overall Security Score

| Dimension | Status | Weight | Score |
|-----------|--------|--------|-------|
| 1. Authentication | PASS | 10% | 9/10 |
| 2. Authorization | PASS | 10% | 10/10 |
| 3. Secrets Management | PASS | 8% | 9/10 |
| 4. Encryption | PASS | 8% | 9/10 |
| 5. TLS | WARNING | 5% | 6/10 |
| 6. Security Headers | WARNING | 5% | 6/10 |
| 7. CORS | PASS | 3% | 10/10 |
| 8. Rate Limiting | PASS | 5% | 9/10 |
| 9. SQL Injection | PASS | 5% | 10/10 |
| 10. XSS | WARNING | 5% | 5/10 |
| 11. CSRF | NOT_IMPLEMENTED | 5% | 0/10 |
| 12. SSRF | NOT_IMPLEMENTED | 5% | 0/10 |
| 13. RCE | PASS | 5% | 10/10 |
| 14. Path Traversal | PASS | 2% | 10/10 |
| 15. File Upload | PASS | 3% | 8/10 |
| 16. Audit Trail | PASS | 8% | 9/10 |
| 17. Logging | WARNING | 5% | 5/10 |
| 18. AI Guardrails | PASS | 5% | 9/10 |
| 19. Session Management | PASS | 5% | 8/10 |
| 20. Intrusion Detection | WARNING | 3% | 4/10 |

**Weighted Score: 7.6 / 10 (C grade — Good but needs hardening)**

---

# Top 10 Fixes (Ranked by Impact)

| # | Fix | Dimension | Priority | Effort |
|---|-----|-----------|----------|--------|
| 1 | **Implement SSRF guard** — validate all external API URLs against allowlist + block private IPs/metadata endpoints | SSRF | CRITICAL | 2 days |
| 2 | **Add CSRF middleware** — Double-Submit Cookie pattern for unsafe methods | CSRF | HIGH | 1 day |
| 3 | **Remove `'unsafe-inline'` from CSP `script-src`** — use nonce-based or `strict-dynamic` | XSS / Security Headers | HIGH | 1 day |
| 4 | **Add PII redaction to JSON logging formatter** — emails, NIDs, phone numbers | Logging | HIGH | 1 day |
| 5 | **Implement account lockout after N failed login attempts** (user-level, not just IP) | Authentication / Intrusion Detection | HIGH | 1 day |
| 6 | **Add refresh token rotation** — blacklist old refresh token on each refresh | Session Management | MEDIUM | 1 day |
| 7 | **Add key-version tagging to encrypted values** — enable `ENCRYPTION_KEY` rotation without data loss | Encryption | MEDIUM | 2 days |
| 8 | **Add periodic audit-chain verification** as background task | Audit Trail | MEDIUM | 1 day |
| 9 | **Add EXIF stripping on image uploads** and consider ClamAV integration | File Upload | MEDIUM | 1 day |
| 10 | **Add brute-force anomaly detection** — geo-velocity, multi-IP per user patterns | Intrusion Detection | MEDIUM | 2 days |

**Total estimated effort: ~13 days**
