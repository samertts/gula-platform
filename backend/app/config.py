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

# ─── JWT Access Token ────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if IS_PRODUCTION:
        print("[GULA FATAL] SECRET_KEY must be set in production.", file=sys.stderr)
        sys.exit(1)
    SECRET_KEY = secrets.token_urlsafe(64)
    logger.warning("SECRET_KEY not set - using random key. Sessions won't survive restarts.")

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "8"))

# ─── JWT Refresh Token ───────────────────────────────────────────────────────
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", "")
if not REFRESH_TOKEN_SECRET:
    # Derive from SECRET_KEY if not set separately (acceptable for single-server setup)
    REFRESH_TOKEN_SECRET = f"refresh_{SECRET_KEY}"
    if IS_PRODUCTION:
        logger.warning("REFRESH_TOKEN_SECRET not set - derived from SECRET_KEY.")

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# ─── Encryption ──────────────────────────────────────────────────────────────
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
if not ENCRYPTION_KEY:
    if IS_PRODUCTION:
        print("[GULA FATAL] ENCRYPTION_KEY must be set in production.", file=sys.stderr)
        sys.exit(1)
    logger.warning("ENCRYPTION_KEY not set. Set it in .env for production.")

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
