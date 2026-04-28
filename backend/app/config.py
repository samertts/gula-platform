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
    if IS_PRODUCTION:
        print("[GULA FATAL] NID_HMAC_KEY must be set in production.", file=sys.stderr)
        sys.exit(1)
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

# ─── Redis (optional — MVP deployments run without Redis; in-memory fallback ──
# is used automatically by redis_client.py when REDIS_URL is absent.
# For full cross-process session invalidation and rate limiting, set REDIS_URL.
REDIS_URL = os.getenv("REDIS_URL", "")
if not REDIS_URL:
    logger.warning(
        "REDIS_URL not set — using in-memory store (not shared across workers). "
        "Set REDIS_URL for full rate-limiting and cross-process session invalidation."
    )

# ─── AI Providers ────────────────────────────────────────────────────────────
# All optional — platform functions without any AI key (rules-based fallback).
# Google AI Studio (Gemini): free tier (1 500 req/day, 15 req/min).
# Get a free key at https://aistudio.google.com/apikey
# SDK: pip install google-generativeai>=0.8.0  (raw HTTP fallback if not installed)
GEMINI_API_KEY       = os.getenv("GEMINI_API_KEY", "")
GEMINI_CLINICAL_MODEL = os.getenv("GEMINI_CLINICAL_MODEL", "gemini-2.0-flash")
GEMINI_CHAT_MODEL     = os.getenv("GEMINI_CHAT_MODEL",     "gemini-2.0-flash")
GROQ_API_KEY         = os.getenv("GROQ_API_KEY", "")
OLLAMA_BASE_URL      = os.getenv("OLLAMA_BASE_URL", "")

# ─── Mobile / Notifications ─────────────────────────────────────────────────
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")  # Firebase Cloud Messaging
APNS_KEY = os.getenv("APNS_KEY", "")              # Apple Push Notifications

# ─── API Documentation ───────────────────────────────────────────────────────
# Enable API docs in production for government testers (controlled by env var)
ENABLE_API_DOCS = os.getenv("ENABLE_API_DOCS", "false").lower() == "true"


# ─── External Adapter Mode (stub | live | shadow) ────────────────────────────
# See backend/app/gateways/mode.py for resolution rules.
#   GULA_ADAPTER_MODE            — global default (fallback: "stub")
#   GULA_ADAPTER_MODE_NID        — overrides global for gov-NID adapter
#   GULA_ADAPTER_MODE_INSURANCE  — overrides for NHI insurance adapter
#   GULA_ADAPTER_MODE_RESIDENCY  — overrides for MoI residency adapter
#   GULA_ADAPTER_MODE_CLOUDFLARE — overrides for Cloudflare control plane
ADAPTER_MODE_DEFAULT    = os.getenv("GULA_ADAPTER_MODE", "stub").lower()
ADAPTER_MODE_NID        = os.getenv("GULA_ADAPTER_MODE_NID",        ADAPTER_MODE_DEFAULT).lower()
ADAPTER_MODE_INSURANCE  = os.getenv("GULA_ADAPTER_MODE_INSURANCE",  ADAPTER_MODE_DEFAULT).lower()
ADAPTER_MODE_RESIDENCY  = os.getenv("GULA_ADAPTER_MODE_RESIDENCY",  ADAPTER_MODE_DEFAULT).lower()
ADAPTER_MODE_CLOUDFLARE = os.getenv("GULA_ADAPTER_MODE_CLOUDFLARE", ADAPTER_MODE_DEFAULT).lower()

# ─── Iraqi government endpoints (optional — LIVE mode only) ──────────────────
# Leave empty to keep the adapter in STUB mode. When present, the adapter
# runs against the real API. Credentials must NEVER be committed.
MOI_NID_API_URL       = os.getenv("MOI_NID_API_URL", "")
MOI_NID_API_KEY       = os.getenv("MOI_NID_API_KEY", "")
INSURANCE_API_URL     = os.getenv("INSURANCE_API_URL", "")
INSURANCE_API_KEY     = os.getenv("INSURANCE_API_KEY", "")
RESIDENCY_API_URL     = os.getenv("RESIDENCY_API_URL", "")
RESIDENCY_API_KEY     = os.getenv("RESIDENCY_API_KEY", "")

# ─── Cloudflare control plane (optional — LIVE mode only) ────────────────────
CF_API_TOKEN   = os.getenv("CF_API_TOKEN", "")
CF_ACCOUNT_ID  = os.getenv("CF_ACCOUNT_ID", "")
CF_ZONE_ID     = os.getenv("CF_ZONE_ID", "")
CF_R2_BUCKET   = os.getenv("CF_R2_BUCKET", "gula-reports")

# ─── Supabase (optional — for projects migrating to Supabase Postgres) ───────
# When set, health/diagnostic scripts surface the Supabase project. Primary
# DATABASE_URL is still authoritative for runtime connections.
SUPABASE_URL         = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY    = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# ─── Render / DigitalOcean (informational — set by their platforms) ──────────
RENDER_SERVICE_ID        = os.getenv("RENDER_SERVICE_ID", "")
DIGITALOCEAN_APP_ID      = os.getenv("DIGITALOCEAN_APP_ID", "")
