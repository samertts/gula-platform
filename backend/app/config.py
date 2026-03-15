import os
import sys
import secrets
import logging

logger = logging.getLogger("gula.config")

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/gula"
)

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(64)
    print(
        "[GULA WARNING] SECRET_KEY not set in environment. "
        "Using random key - sessions will not survive restarts. "
        "Set SECRET_KEY in .env for production.",
        file=sys.stderr,
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24  # 24 hours (healthcare standard)

# App
APP_NAME = "GULA Platform"
APP_VERSION = "1.1.0"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Encryption
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
if not ENCRYPTION_KEY:
    print(
        "[GULA WARNING] ENCRYPTION_KEY not set. Set it in .env for production.",
        file=sys.stderr,
    )

# Result link settings
RESULT_TOKEN_LENGTH = 32
RESULT_LINK_EXPIRE_DAYS = 90
