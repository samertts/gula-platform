from __future__ import annotations

import logging
import os
import secrets
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.config.loader import AppConfig

logger = logging.getLogger("gula.config")

# ─── Environment ─────────────────────────────────────────────────────────────
ENV = os.getenv("ENV", "production")
IS_PRODUCTION = ENV == "production"

# ─── Runtime Isolation ───────────────────────────────────────────────────────
# RUNTIME_MODE controls what kind of process this is:
#   "api"     — FastAPI HTTP server. Must NOT run maintenance loops.
#   "worker"  — Background worker process. Runs OutboxWorker, RecoveryWorker,
#               health watchdog, adaptive concurrency, auto-repair. Has access
#               to edge_* tables.
#   "test"    — Test runtime. NEVER spawns threads, tasks, or background loops.
#   "cli"     — One-shot scripts (alembic, seeders). No background tasks.
#
# FEATURE_BACKGROUND_TASKS is the master kill-switch. When false, NO background
# coroutines are launched even if RUNTIME_MODE allows it. Defaults to false in
# anything other than the worker runtime so the API process stays cleanly
# isolated by default.
RUNTIME_MODE = os.getenv("RUNTIME_MODE", "api").lower()
if RUNTIME_MODE not in {"api", "worker", "test", "cli", "migration", "openapi"}:
    sys.exit(1)

IS_WORKER_RUNTIME = RUNTIME_MODE == "worker"
IS_API_RUNTIME = RUNTIME_MODE == "api"
IS_TEST_RUNTIME = RUNTIME_MODE == "test" or ENV == "test"
IS_CLI_RUNTIME = RUNTIME_MODE == "cli"

# Master switch for background tasks. Defaults to True only inside the worker
# runtime; everywhere else it must be explicitly enabled to spawn anything.
_DEFAULT_BG = "true" if IS_WORKER_RUNTIME else "false"
FEATURE_BACKGROUND_TASKS = os.getenv("FEATURE_BACKGROUND_TASKS", _DEFAULT_BG).lower() == "true"

# Hard rule: tests must never spawn background tasks regardless of env vars.
if IS_TEST_RUNTIME:
    FEATURE_BACKGROUND_TASKS = False


def background_tasks_enabled() -> bool:
    """Return True if this process is allowed to spawn background coroutines.

    A task is allowed only when BOTH conditions hold:
      1. FEATURE_BACKGROUND_TASKS=true (explicit opt-in)
      2. RUNTIME_MODE=worker          (correct process type)

    This double-gate prevents an API or test process from accidentally
    launching maintenance loops if the env var is misconfigured.
    """
    return FEATURE_BACKGROUND_TASKS and IS_WORKER_RUNTIME


# ─── App Info ────────────────────────────────────────────────────────────────
APP_NAME = "GULA Platform"
APP_VERSION = "1.0.0"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
PLATFORM_NAME_AR = "منصة غولا الصحية"

# ─── Database ────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    if IS_PRODUCTION:
        sys.exit(1)
    # Dev-only fallback: use local postgres without hardcoded password
    DATABASE_URL = "postgresql://postgres@localhost:5432/gula"
    logger.warning(
        "DATABASE_URL not set — using local dev default. Set DATABASE_URL in .env for production.",
    )

# ─── Weak-secret detection helper ────────────────────────────────────────────
_WEAK_PATTERNS = (
    "default",
    "change",
    "secret",
    "example",
    "test",
    "demo",
    "gula_default",
    "changeme",
    "password",
    "12345",
    "abcdef",
    "admin",
    "qwerty",
    "letmein",
    "welcome",
    "pass",
    "00000",
    "11111",
)


def _is_weak_secret(value: str) -> bool:
    lower = value.lower()
    return any(pat in lower for pat in _WEAK_PATTERNS)


# ─── JWT Access Token ────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if IS_PRODUCTION:
        sys.exit(1)
    SECRET_KEY = secrets.token_urlsafe(64)
    logger.warning("SECRET_KEY not set - using random key. Sessions won't survive restarts.")
elif IS_PRODUCTION and _is_weak_secret(SECRET_KEY):
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
        sys.exit(1)
    # Dev fallback: generate an independent random key
    REFRESH_TOKEN_SECRET = secrets.token_urlsafe(64)
    logger.warning(
        "REFRESH_TOKEN_SECRET not set - using random key. Set it in .env for production.",
    )

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# ─── Encryption ──────────────────────────────────────────────────────────────
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
if not ENCRYPTION_KEY:
    if IS_PRODUCTION:
        sys.exit(1)
    logger.warning("ENCRYPTION_KEY not set. Set it in .env for production.")
elif IS_PRODUCTION and _is_weak_secret(ENCRYPTION_KEY):
    sys.exit(1)

# ─── National ID HMAC ────────────────────────────────────────────────────────
# Must NOT change in production or existing lookups will break
NID_HMAC_KEY = os.getenv("NID_HMAC_KEY", "")
if not NID_HMAC_KEY:
    if IS_PRODUCTION:
        sys.exit(1)
    NID_HMAC_KEY = ENCRYPTION_KEY or SECRET_KEY
    logger.warning("NID_HMAC_KEY not set. Set a stable key in .env for production.")

# ─── Audit Anchor HMAC ──────────────────────────────────────────────────────
# Separate key from NID_HMAC_KEY for key separation best practice.
AUDIT_ANCHOR_KEY = os.getenv("AUDIT_ANCHOR_KEY", "")
if not AUDIT_ANCHOR_KEY:
    if IS_PRODUCTION:
        sys.exit(1)
    AUDIT_ANCHOR_KEY = NID_HMAC_KEY
    logger.warning("AUDIT_ANCHOR_KEY not set. Set in .env for production.")

# ─── Result Links ────────────────────────────────────────────────────────────
RESULT_TOKEN_LENGTH = 32
RESULT_LINK_EXPIRE_DAYS = 90

# ─── Upload Limits ───────────────────────────────────────────────────────────
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "2"))
MAX_REQUEST_BODY_MB = int(os.getenv("MAX_REQUEST_BODY_MB", "10"))

# ─── Rate Limiting ───────────────────────────────────────────────────────────
RATE_LIMIT_AUTH = int(os.getenv("RATE_LIMIT_AUTH", "10"))
RATE_LIMIT_PUBLIC = int(os.getenv("RATE_LIMIT_PUBLIC", "30"))

# ─── Startup Guard Timeout ───────────────────────────────────────────────────
# Maximum seconds the startup guard waits for all validation steps before
# switching to partial-readiness mode. In partial mode, the /health/ready probe
# passes but some dependencies (e.g. kernel) may still be initializing.
# Default: 120 seconds (covers DB backoff + Redis + migrations + kernel boot).
STARTUP_TIMEOUT_SECONDS = int(os.getenv("STARTUP_TIMEOUT_SECONDS", "120"))

# ─── Redis (optional — MVP deployments run without Redis; in-memory fallback ──
# is used automatically by redis_client.py when REDIS_URL is absent.
# For full cross-process session invalidation and rate limiting, set REDIS_URL.
REDIS_URL = os.getenv("REDIS_URL", "")
if not REDIS_URL:
    logger.warning(
        "REDIS_URL not set — using in-memory store (not shared across workers). "
        "Set REDIS_URL for full rate-limiting and cross-process session invalidation.",
    )

# ─── Redis Sentinel / Cluster (HA mode) ──────────────────────────────────────
# When set, overrides REDIS_URL with Sentinel-managed HA Redis.
REDIS_SENTINEL_HOSTS = os.getenv("REDIS_SENTINEL_HOSTS", "")
REDIS_SENTINEL_MASTER = os.getenv("REDIS_SENTINEL_MASTER", "gula-redis-primary")
REDIS_CLUSTER_NODES = os.getenv("REDIS_CLUSTER_NODES", "")

# ─── Multi-Level Cache Configuration ─────────────────────────────────────────
# Controls the L1 (in-memory) + L2 (Redis) cache coordinator in core/cache_manager.py
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_L1_TTL = int(os.getenv("CACHE_L1_TTL", "60"))  # default L1 TTL (seconds)
CACHE_L2_TTL = int(os.getenv("CACHE_L2_TTL", "300"))  # default L2 TTL (seconds)
CACHE_L1_MAX_SIZE = int(os.getenv("CACHE_L1_MAX_SIZE", "10000"))
CACHE_METRICS_ENABLED = os.getenv("CACHE_METRICS_ENABLED", "true").lower() == "true"

# ─── Read Replica Database ───────────────────────────────────────────────────
# When set, read queries are routed to this URL instead of DATABASE_URL.
# Requires PgBouncer or similar connection pooler in front of replicas.
READ_REPLICA_URL = os.getenv("READ_REPLICA_URL", "")
READ_REPLICA_ENABLED = (
    bool(READ_REPLICA_URL) or os.getenv("READ_REPLICA_ENABLED", "false").lower() == "true"
)

# ─── AI Providers ────────────────────────────────────────────────────────────
# All optional — platform functions without any AI key (rules-based fallback).
# Google AI Studio (Gemini): free tier (1 500 req/day, 15 req/min).
# Get a free key at https://aistudio.google.com/apikey
# SDK: pip install google-generativeai>=0.8.0  (raw HTTP fallback if not installed)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_CLINICAL_MODEL = os.getenv("GEMINI_CLINICAL_MODEL", "gemini-2.0-flash")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "")

# ─── Mobile / Notifications ─────────────────────────────────────────────────
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")  # Firebase Cloud Messaging
APNS_KEY = os.getenv("APNS_KEY", "")  # Apple Push Notifications

# ─── Email (Resend — production email provider) ─────────────────────────────
# The Resend API key must come ONLY from the environment (.env for local
# development, Secrets/Environment Variables on the hosting platform).
# It is NEVER hardcoded, logged, or committed to the repository.
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@gula-platform.org")
RESEND_TIMEOUT_SECONDS = int(os.getenv("RESEND_TIMEOUT_SECONDS", "30"))
RESEND_MAX_RETRIES = int(os.getenv("RESEND_MAX_RETRIES", "3"))
RESEND_ENABLED = bool(RESEND_API_KEY)

# ─── Telegram Bot (production notification provider) ─────────────────────────
# The bot token must come ONLY from the environment (.env for local dev,
# Secrets/Environment Variables on the hosting platform). It is NEVER
# hardcoded, logged, or committed. chat_id is NOT configured here — it is
# supplied dynamically per notification.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_NOTIFICATIONS_ENABLED = os.getenv("TELEGRAM_NOTIFICATIONS_ENABLED", "true").lower() == "true"
TELEGRAM_TIMEOUT_SECONDS = int(os.getenv("TELEGRAM_TIMEOUT_SECONDS", "30"))
TELEGRAM_MAX_RETRIES = int(os.getenv("TELEGRAM_MAX_RETRIES", "3"))

# ─── Telegram enterprise (PROGRAM-COMM-002A) ─────────────────────────────────
# Webhook mode: when TELEGRAM_WEBHOOK_URL is set the provider registers a
# webhook and the platform serves /webhooks/telegram/update. When empty, the
# bot runs in polling mode. TELEGRAM_WEBHOOK_SECRET_TOKEN is returned by
# Telegram in the X-Telegram-Bot-Api-Secret-Token header and validated
# constant-time on every update — keep it secret, like the bot token.
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")
TELEGRAM_WEBHOOK_SECRET_TOKEN = os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN", "")
TELEGRAM_WEBHOOK_MAX_CONNECTIONS = int(os.getenv("TELEGRAM_WEBHOOK_MAX_CONNECTIONS", "40"))
TELEGRAM_MODE = os.getenv("TELEGRAM_MODE", "auto")  # polling | webhook | auto
# Outbound rate limiting (smooth token bucket) + per-chat flood guard.
TELEGRAM_RATE_PER_MINUTE = int(os.getenv("TELEGRAM_RATE_PER_MINUTE", "30"))
TELEGRAM_MAX_PER_CHAT = int(os.getenv("TELEGRAM_MAX_PER_CHAT", "0"))

# ─── API Documentation ───────────────────────────────────────────────────────
# Enable API docs in production for government testers (controlled by env var)
ENABLE_API_DOCS = os.getenv("ENABLE_API_DOCS", "false").lower() == "true"


# ─── SNDHS-lite Phase 1 deployment-wide flags ────────────────────────────────
# These gate the rollout of new visit-centric and national-ID surfaces.
# They are off by default so a fresh deploy of this branch behaves
# identically to the previous release until ops flips them on.
# The authoritative readers live in backend/app/core/sndhs_flags.py.
SNDHS_ENABLE_VISITS = os.getenv("SNDHS_ENABLE_VISITS", "false").lower() == "true"
SNDHS_ENABLE_NATIONAL_ID = os.getenv("SNDHS_ENABLE_NATIONAL_ID", "false").lower() == "true"


# ─── External Adapter Mode (stub | live | shadow) ────────────────────────────
# See backend/app/gateways/mode.py for resolution rules.
#   GULA_ADAPTER_MODE            — global default (fallback: "stub")
#   GULA_ADAPTER_MODE_NID        — overrides global for gov-NID adapter
#   GULA_ADAPTER_MODE_INSURANCE  — overrides for NHI insurance adapter
#   GULA_ADAPTER_MODE_RESIDENCY  — overrides for MoI residency adapter
#   GULA_ADAPTER_MODE_CLOUDFLARE — overrides for Cloudflare control plane
ADAPTER_MODE_DEFAULT = os.getenv("GULA_ADAPTER_MODE", "stub").lower()
ADAPTER_MODE_NID = os.getenv("GULA_ADAPTER_MODE_NID", ADAPTER_MODE_DEFAULT).lower()
ADAPTER_MODE_INSURANCE = os.getenv("GULA_ADAPTER_MODE_INSURANCE", ADAPTER_MODE_DEFAULT).lower()
ADAPTER_MODE_RESIDENCY = os.getenv("GULA_ADAPTER_MODE_RESIDENCY", ADAPTER_MODE_DEFAULT).lower()
ADAPTER_MODE_CLOUDFLARE = os.getenv("GULA_ADAPTER_MODE_CLOUDFLARE", ADAPTER_MODE_DEFAULT).lower()

# ─── Iraqi government endpoints (optional — LIVE mode only) ──────────────────
# Leave empty to keep the adapter in STUB mode. When present, the adapter
# runs against the real API. Credentials must NEVER be committed.
MOI_NID_API_URL = os.getenv("MOI_NID_API_URL", "")
MOI_NID_API_KEY = os.getenv("MOI_NID_API_KEY", "")
INSURANCE_API_URL = os.getenv("INSURANCE_API_URL", "")
INSURANCE_API_KEY = os.getenv("INSURANCE_API_KEY", "")
RESIDENCY_API_URL = os.getenv("RESIDENCY_API_URL", "")
RESIDENCY_API_KEY = os.getenv("RESIDENCY_API_KEY", "")

# ─── Cloudflare control plane (optional — LIVE mode only) ────────────────────
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "")
CF_ZONE_ID = os.getenv("CF_ZONE_ID", "")
CF_R2_BUCKET = os.getenv("CF_R2_BUCKET", "gula-reports")

# ─── Supabase (optional — for projects migrating to Supabase Postgres) ───────
# When set, health/diagnostic scripts surface the Supabase project. Primary
# DATABASE_URL is still authoritative for runtime connections.
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# ─── Render / DigitalOcean (informational — set by their platforms) ──────────
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID", "")
DIGITALOCEAN_APP_ID = os.getenv("DIGITALOCEAN_APP_ID", "")

# ─── Financial Engine (feature-flagged, OFF by default) ──────────────────────
# The Financial Engine is the provider-billing / ranking / ads / fraud /
# clinical-governance / incentive subsystem. It is shipped progressively
# behind the two flags below. Both default to OFF in every environment so
# that:
#   1. Phase A migrations can land in production without activating any
#      runtime behaviour (tables sit empty until the engine is turned on).
#   2. Rolling back is a single env-var flip — no schema changes required.
#
# ENABLE_FINANCIAL_ENGINE  — master switch for the whole engine. Gates the
#   /financial/* routes, pricing, ranking, transactions, governance and
#   incentive paths. Must stay OFF until Phase B+ code is shipped and
#   validated in staging.
#
# ENABLE_ADS               — sub-flag for the sponsored-listing / ad bidding
#   surface. Has effect ONLY when ENABLE_FINANCIAL_ENGINE is also true.
#   Allows ads to be paused independently of the rest of the engine.
ENABLE_FINANCIAL_ENGINE = os.getenv("ENABLE_FINANCIAL_ENGINE", "false").lower() == "true"
ENABLE_ADS = os.getenv("ENABLE_ADS", "false").lower() == "true"


# ── Bootstrap Configuration ───────────────────────────────────────────────────
# Controls the National Bootstrap Engine.
# ENABLE_BOOTSTRAP — master switch; when false, no bootstrap runs (default: true)
# ENABLE_NATIONAL_BOOTSTRAP — enables national hierarchy (ministry, directorates, etc.)
# ENABLE_DEMO_DATA — generates deterministic demo patients/orders/results
# BOOTSTRAP_COUNTRY — ISO country code (default: IQ)
# BOOTSTRAP_LANGUAGE — default language code (default: ar)
# BOOTSTRAP_TIMEZONE — default timezone (default: Asia/Baghdad)
ENABLE_BOOTSTRAP = os.getenv("ENABLE_BOOTSTRAP", "true").lower() == "true"
ENABLE_NATIONAL_BOOTSTRAP = os.getenv("ENABLE_NATIONAL_BOOTSTRAP", "true").lower() == "true"
ENABLE_DEMO_DATA = os.getenv("ENABLE_DEMO_DATA", "false").lower() == "true"
BOOTSTRAP_COUNTRY = os.getenv("BOOTSTRAP_COUNTRY", "IQ")
BOOTSTRAP_LANGUAGE = os.getenv("BOOTSTRAP_LANGUAGE", "ar")
BOOTSTRAP_TIMEZONE = os.getenv("BOOTSTRAP_TIMEZONE", "Asia/Baghdad")

# Bootstrap admin accounts — passwords must come ONLY from environment variables
MINISTRY_ADMIN_EMAIL = os.getenv("MINISTRY_ADMIN_EMAIL", "ministry@gula-platform.org")
MINISTRY_ADMIN_PASSWORD = os.getenv("MINISTRY_ADMIN_PASSWORD", "")
MINISTRY_ADMIN_PASSWORD_HASH = os.getenv("MINISTRY_ADMIN_PASSWORD_HASH", "")
ORGANIZATION_ADMIN_EMAIL = os.getenv("ORGANIZATION_ADMIN_EMAIL", "org-admin@gula-platform.org")
ORGANIZATION_ADMIN_PASSWORD = os.getenv("ORGANIZATION_ADMIN_PASSWORD", "")
ORGANIZATION_ADMIN_PASSWORD_HASH = os.getenv("ORGANIZATION_ADMIN_PASSWORD_HASH", "")
DIRECTORATE_ADMIN_EMAIL = os.getenv(
    "DIRECTORATE_ADMIN_EMAIL", "directorate-admin@gula-platform.org",
)
DIRECTORATE_ADMIN_PASSWORD = os.getenv("DIRECTORATE_ADMIN_PASSWORD", "")
DIRECTORATE_ADMIN_PASSWORD_HASH = os.getenv("DIRECTORATE_ADMIN_PASSWORD_HASH", "")
LAB_MANAGER_EMAIL = os.getenv("LAB_MANAGER_EMAIL", "lab-manager@gula-platform.org")
LAB_MANAGER_PASSWORD = os.getenv("LAB_MANAGER_PASSWORD", "")
LAB_MANAGER_PASSWORD_HASH = os.getenv("LAB_MANAGER_PASSWORD_HASH", "")
AUDITOR_EMAIL = os.getenv("AUDITOR_EMAIL", "auditor@gula-platform.org")
AUDITOR_PASSWORD = os.getenv("AUDITOR_PASSWORD", "")
AUDITOR_PASSWORD_HASH = os.getenv("AUDITOR_PASSWORD_HASH", "")
SECURITY_OFFICER_EMAIL = os.getenv("SECURITY_OFFICER_EMAIL", "security@gula-platform.org")
SECURITY_OFFICER_PASSWORD = os.getenv("SECURITY_OFFICER_PASSWORD", "")
SECURITY_OFFICER_PASSWORD_HASH = os.getenv("SECURITY_OFFICER_PASSWORD_HASH", "")

# ── Kernel Env Vars ──────────────────────────────────────────────────────────
# The Kernel is the permanent runtime foundation. Every future module must
# depend on the Kernel. Nothing should bypass the Kernel.
#
# These flags control which Kernel subsystems are enabled at deploy time.
# All default to "true" so the Kernel is fully active out of the box.
#
# KERNEL_KILL_SWITCH       — emergency stop: blocks autonomous kernel actions
# KERNEL_DEGRADED          — puts kernel into degraded mode (no plugin/module loading)
# KERNEL_ENABLE_PLUGINS    — enable the plugin system
# KERNEL_ENABLE_EVENT_BUS  — enable the internal event bus
# KERNEL_ENABLE_BACKGROUND — enable background task processing
# KERNEL_ENABLE_FEATURES   — enable feature flag management
# KERNEL_ENABLE_CONFIG     — enable configuration engine
# KERNEL_ENABLE_TENANT     — enable multi-tenant engine
# KERNEL_ENABLE_GATEWAY    — enable internal API gateway
KERNEL_KILL_SWITCH = os.getenv("KERNEL_KILL_SWITCH", "false").lower() == "true"
KERNEL_DEGRADED = os.getenv("KERNEL_DEGRADED", "false").lower() == "true"
KERNEL_ENABLE_PLUGINS = os.getenv("KERNEL_ENABLE_PLUGINS", "true").lower() == "true"
KERNEL_ENABLE_EVENT_BUS = os.getenv("KERNEL_ENABLE_EVENT_BUS", "true").lower() == "true"
KERNEL_ENABLE_BACKGROUND = os.getenv("KERNEL_ENABLE_BACKGROUND", "true").lower() == "true"
KERNEL_ENABLE_FEATURES = os.getenv("KERNEL_ENABLE_FEATURES", "true").lower() == "true"
KERNEL_ENABLE_CONFIG = os.getenv("KERNEL_ENABLE_CONFIG", "true").lower() == "true"
KERNEL_ENABLE_TENANT = os.getenv("KERNEL_ENABLE_TENANT", "true").lower() == "true"
KERNEL_ENABLE_GATEWAY = os.getenv("KERNEL_ENABLE_GATEWAY", "true").lower() == "true"


# ── Canonical Config Accessor ────────────────────────────────────────────────
# Returns the shared AppConfig dataclass for use by new code.
# Legacy globals above remain for backward compatibility.


def get_shared_config() -> AppConfig:
    """Return the canonical AppConfig from shared.config.loader."""
    from shared.config import load_config as _load

    return _load()
