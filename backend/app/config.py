import os
import secrets

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/gula"
)

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(64))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24  # 24 hours (healthcare standard)

# App
APP_NAME = "GULA Platform"
APP_VERSION = "1.0.0"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Result link settings
RESULT_TOKEN_LENGTH = 32
RESULT_LINK_EXPIRE_DAYS = 30
