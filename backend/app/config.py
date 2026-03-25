import os
import sys
import secrets
import logging

logger = logging.getLogger("gula.config")

# ─── Environment ─────────────────────────────────────────────────────────────
ENV = os.getenv("ENV", "production")
IS_PRODUCTION = ENV == "production"

# ─── App Info ────────────────────────────────────────────────────────────────
APP_NAME = "GULA Platform"
APP_VERSION = "2.1.0"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
PLATFORM_NAME_AR = "منصة غولا الصحية"

# ─── Database ────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    if IS_PRODUCTION:
        print("[GULA FATAL] DATABASE_URL must be set in production.", file=sys.stderr)
        sys.exit(1)
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/gula"

# ─── Weak-secret detection helper ────────────────────────────────────────────
_WEAK_PATTERNS = (
    "default", "change", "secret", "example", "test", "demo",
    "gula_default", "changeme", "password", "12345", "abcdef",
)


def _is_weak_secret(value: str) -> bool:
    lower = value.lower()
    return any(pat in lower for pat in _WEAK_PATTERNS)


# ─── JWT Access Token ────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if IS_PRODUCTION:
        print("[GULA FATAL] SECRET_KEY must be set in production.", file=sys.stderr)
        sys.exit(1)
    SECRET_KEY = secrets.token_urlsafe(64)
    logger.warning("SECRET_KEY not set - using random key. Sessions won't survive restarts.")
elif IS_PRODUCTION and _is_weak_secret(SECRET_KEY):
    print(
        "[GULA FATAL] SECRET_KEY contains a weak/default pattern. "
        "Set a strong random value in .env (e.g. `openssl rand -hex 64`).",
        file=sys.stderr,
    )
    sys.exit(1)

JWT_ALGORITHM = "HS256"
# JWT_EXPIRE_MINUTES is the primary setting (default: 30 min).
# JWT_EXPIRE_HOURS is kept for backward compatibility; if both are set, MINUTES wins.
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "0"))
if not JWT_EXPIRE_MINUTES:
    _legacy_hours = int(os.getenv("JWT_EXPIRE_HOURS", "0"))
    JWT_EXPIRE_MINUTES = _legacy_hours * 60 if _legacy_hours else 30
JWT_EXPIRE_HOURS = JWT_EXPIRE_MINUTES // 60 or 1  # kept for cookie max_age calcs

# ─── JWT Refresh Token ───────────────────────────────────────────────────────
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", "")
if not REFRESH_TOKEN_SECRET:
    if IS_PRODUCTION:
        print("[GULA FATAL] REFRESH_TOKEN_SECRET must be set in production.", file=sys.stderr)
        sys.exit(1)
    # Dev fallback: derive from SECRET_KEY (not suitable for production)
    REFRESH_TOKEN_SECRET = f"refresh_{SECRET_KEY}"
    logger.warning("REFRESH_TOKEN_SECRET not set - derived from SECRET_KEY. Set it in .env for production.")

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# ─── Encryption ──────────────────────────────────────────────────────────────
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
if not ENCRYPTION_KEY:
    if IS_PRODUCTION:
        print("[GULA FATAL] ENCRYPTION_KEY must be set in production.", file=sys.stderr)
        sys.exit(1)
    logger.warning("ENCRYPTION_KEY not set. Set it in .env for production.")
elif IS_PRODUCTION and _is_weak_secret(ENCRYPTION_KEY):
    print(
        "[GULA FATAL] ENCRYPTION_KEY contains a weak/default pattern. "
        "Generate with: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"",
        file=sys.stderr,
    )
    sys.exit(1)

# ─── National ID HMAC ────────────────────────────────────────────────────────
# Must NOT change in production or existing lookups will break
NID_HMAC_KEY = os.getenv("NID_HMAC_KEY", "")
if not NID_HMAC_KEY:
    NID_HMAC_KEY = ENCRYPTION_KEY or SECRET_KEY
    logger.warning("NID_HMAC_KEY not set. Set a stable key in .env for production.")

# ─── Result Links ────────────────────────────────────────────────────────────
RESULT_TOKEN_LENGTH = 32
RESULT_LINK_EXPIRE_DAYS = 90

# ─── Upload Limits ───────────────────────────────────────────────────────────
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "2"))
MAX_REQUEST_BODY_MB = int(os.getenv("MAX_REQUEST_BODY_MB", "10"))

# ─── Rate Limiting ───────────────────────────────────────────────────────────
RATE_LIMIT_AUTH = int(os.getenv("RATE_LIMIT_AUTH", "10"))
RATE_LIMIT_PUBLIC = int(os.getenv("RATE_LIMIT_PUBLIC", "30"))

# ─── Redis (optional - for production rate limiting) ─────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "")

# ─── Mobile / Notifications ─────────────────────────────────────────────────
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")  # Firebase Cloud Messaging
APNS_KEY = os.getenv("APNS_KEY", "")              # Apple Push Notifications

# ─── API Documentation ───────────────────────────────────────────────────────
# Enable API docs in production for government testers (controlled by env var)
ENABLE_API_DOCS = os.getenv("ENABLE_API_DOCS", "false").lower() == "true"
