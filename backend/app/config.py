import os
import sys
import secrets
import logging

logger = logging.getLogger("gula.config")

# Environment
ENV = os.getenv("ENV", "production")
IS_PRODUCTION = ENV == "production"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    if IS_PRODUCTION:
        print("[GULA FATAL] DATABASE_URL must be set in production.", file=sys.stderr)
        sys.exit(1)
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/gula"

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if IS_PRODUCTION:
        print("[GULA FATAL] SECRET_KEY must be set in production.", file=sys.stderr)
        sys.exit(1)
    SECRET_KEY = secrets.token_urlsafe(64)
    logger.warning("SECRET_KEY not set - using random key. Sessions won't survive restarts.")

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "8"))  # 8 hours default (reduced from 24)

# App
APP_NAME = "GULA Platform"
APP_VERSION = "2.0.1"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Encryption
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
if not ENCRYPTION_KEY:
    if IS_PRODUCTION:
        print("[GULA FATAL] ENCRYPTION_KEY must be set in production.", file=sys.stderr)
        sys.exit(1)
    logger.warning("ENCRYPTION_KEY not set. Set it in .env for production.")

# Stable HMAC key for hashing national IDs (must NOT change or lookups break)
NID_HMAC_KEY = os.getenv("NID_HMAC_KEY", "")
if not NID_HMAC_KEY:
    # Fall back to ENCRYPTION_KEY or SECRET_KEY for backwards compatibility
    NID_HMAC_KEY = ENCRYPTION_KEY or SECRET_KEY
    logger.warning("NID_HMAC_KEY not set. Set a stable key in .env for production.")

# Result link settings
RESULT_TOKEN_LENGTH = 32
RESULT_LINK_EXPIRE_DAYS = 90

# Upload limits
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "2"))

# Rate limiting
RATE_LIMIT_AUTH = int(os.getenv("RATE_LIMIT_AUTH", "10"))
RATE_LIMIT_PUBLIC = int(os.getenv("RATE_LIMIT_PUBLIC", "30"))
