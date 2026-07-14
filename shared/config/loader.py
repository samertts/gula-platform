from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

_WEAK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(change|secret|password|key|test|weak|default)", re.IGNORECASE),
    re.compile(r"^(abc|123|qwerty)", re.IGNORECASE),
    re.compile(r"^[a-z]{1,8}$", re.IGNORECASE),
    re.compile(r"^\d{1,16}$"),
]


def _is_weak_secret(value: str | None) -> bool:
    if not value or len(value) < 16:
        return True
    return any(pattern.match(value) for pattern in _WEAK_PATTERNS)


@dataclass
class DatabaseConfig:
    url: str = ""
    pool_size: int = 6
    max_overflow: int = 12
    pool_pre_ping: bool = True
    statement_timeout: int = 30000
    pool_timeout: int = 10
    pool_recycle: int = 1800


@dataclass
class JWTConfig:
    secret_key: str = ""
    algorithm: str = "HS256"
    expire_minutes: int = 30
    refresh_secret: str = ""
    refresh_expire_days: int = 30


@dataclass
class EncryptionConfig:
    key: str = ""
    nid_hmac_key: str = ""


@dataclass
class RedisConfig:
    url: str = ""
    enabled: bool = False


@dataclass
class AIConfig:
    gemini_api_key: str = ""
    groq_api_key: str = ""
    ollama_base_url: str = ""
    gemini_clinical_model: str = "gemini-2.0-flash"
    gemini_chat_model: str = "gemini-2.0-flash"


@dataclass
class SNDHSConfig:
    enable_visits: bool = False
    enable_national_id: bool = False


@dataclass
class NotificationConfig:
    fcm_server_key: str = ""
    apns_key: str = ""


@dataclass
class AdapterConfig:
    mode_default: str = "stub"
    mode_nid: str = "stub"
    mode_insurance: str = "stub"
    mode_residency: str = "stub"
    mode_cloudflare: str = "stub"


@dataclass
class GovernmentConfig:
    moi_nid_api_url: str = ""
    moi_nid_api_key: str = ""
    insurance_api_url: str = ""
    insurance_api_key: str = ""
    residency_api_url: str = ""
    residency_api_key: str = ""


@dataclass
class CloudflareConfig:
    api_token: str = ""
    account_id: str = ""
    zone_id: str = ""
    r2_bucket: str = "gula-reports"


@dataclass
class SupabaseConfig:
    url: str = ""
    anon_key: str = ""
    service_key: str = ""


@dataclass
class AppConfig:
    env: str = "production"
    app_name: str = "GULA Platform"
    app_version: str = "2.1.0"
    debug: bool = False
    base_url: str = ""

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    jwt: JWTConfig = field(default_factory=JWTConfig)
    encryption: EncryptionConfig = field(default_factory=EncryptionConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    sndhs: SNDHSConfig = field(default_factory=SNDHSConfig)
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    adapter: AdapterConfig = field(default_factory=AdapterConfig)
    government: GovernmentConfig = field(default_factory=GovernmentConfig)
    cloudflare: CloudflareConfig = field(default_factory=CloudflareConfig)
    supabase: SupabaseConfig = field(default_factory=SupabaseConfig)

    rate_limit_auth: int = 10
    rate_limit_public: int = 30
    max_upload_size_mb: int = 2
    max_request_body_mb: int = 10
    max_concurrent_requests: int = 50

    enable_financial_engine: bool = False
    enable_ads: bool = False
    feature_background_tasks: bool = True
    runtime_mode: str = "api"
    sentry_dsn: str = ""

    platform_name_ar: str = "منصة غولا الصحية"
    enable_api_docs: bool = False


def _env_str(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except (ValueError, TypeError):
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.environ.get(key, "").strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")


def load_config() -> AppConfig:
    cfg = AppConfig()
    cfg.env = _env_str("ENV", "production")
    cfg.app_name = _env_str("APP_NAME", "GULA Platform")
    cfg.app_version = _env_str("APP_VERSION", "2.1.0")
    cfg.debug = cfg.env == "development"
    cfg.base_url = _env_str("BASE_URL", "")
    cfg.platform_name_ar = _env_str("PLATFORM_NAME_AR", "منصة غولا الصحية")
    cfg.enable_api_docs = _env_bool("ENABLE_API_DOCS", False)

    cfg.database.url = _env_str("DATABASE_URL", "")
    cfg.database.pool_size = _env_int("DB_POOL_SIZE", 6)
    cfg.database.max_overflow = _env_int("DB_MAX_OVERFLOW", 12)
    cfg.database.pool_timeout = _env_int("DB_POOL_TIMEOUT", 10)
    cfg.database.pool_recycle = _env_int("DB_POOL_RECYCLE", 1800)

    cfg.jwt.secret_key = _env_str("SECRET_KEY", "")
    cfg.jwt.algorithm = _env_str("JWT_ALGORITHM", "HS256")
    cfg.jwt.expire_minutes = _env_int("JWT_EXPIRE_MINUTES", 30)
    cfg.jwt.refresh_secret = _env_str("REFRESH_TOKEN_SECRET", "")
    cfg.jwt.refresh_expire_days = _env_int("REFRESH_TOKEN_EXPIRE_DAYS", 30)

    cfg.encryption.key = _env_str("ENCRYPTION_KEY", "")
    cfg.encryption.nid_hmac_key = _env_str("NID_HMAC_KEY", "")

    cfg.redis.url = _env_str("REDIS_URL", "")
    cfg.redis.enabled = bool(cfg.redis.url)

    cfg.ai.gemini_api_key = _env_str("GEMINI_API_KEY", "")
    cfg.ai.gemini_clinical_model = _env_str("GEMINI_CLINICAL_MODEL", "gemini-2.0-flash")
    cfg.ai.gemini_chat_model = _env_str("GEMINI_CHAT_MODEL", "gemini-2.0-flash")
    cfg.ai.groq_api_key = _env_str("GROQ_API_KEY", "")
    cfg.ai.ollama_base_url = _env_str("OLLAMA_BASE_URL", "")

    cfg.sndhs.enable_visits = _env_bool("SNDHS_ENABLE_VISITS", False)
    cfg.sndhs.enable_national_id = _env_bool("SNDHS_ENABLE_NATIONAL_ID", False)

    cfg.notification.fcm_server_key = _env_str("FCM_SERVER_KEY", "")
    cfg.notification.apns_key = _env_str("APNS_KEY", "")

    cfg.adapter.mode_default = _env_str("GULA_ADAPTER_MODE", "stub").lower()
    cfg.adapter.mode_nid = _env_str("GULA_ADAPTER_MODE_NID", cfg.adapter.mode_default).lower()
    cfg.adapter.mode_insurance = _env_str("GULA_ADAPTER_MODE_INSURANCE", cfg.adapter.mode_default).lower()
    cfg.adapter.mode_residency = _env_str("GULA_ADAPTER_MODE_RESIDENCY", cfg.adapter.mode_default).lower()
    cfg.adapter.mode_cloudflare = _env_str("GULA_ADAPTER_MODE_CLOUDFLARE", cfg.adapter.mode_default).lower()

    cfg.government.moi_nid_api_url = _env_str("MOI_NID_API_URL", "")
    cfg.government.moi_nid_api_key = _env_str("MOI_NID_API_KEY", "")
    cfg.government.insurance_api_url = _env_str("INSURANCE_API_URL", "")
    cfg.government.insurance_api_key = _env_str("INSURANCE_API_KEY", "")
    cfg.government.residency_api_url = _env_str("RESIDENCY_API_URL", "")
    cfg.government.residency_api_key = _env_str("RESIDENCY_API_KEY", "")

    cfg.cloudflare.api_token = _env_str("CF_API_TOKEN", "")
    cfg.cloudflare.account_id = _env_str("CF_ACCOUNT_ID", "")
    cfg.cloudflare.zone_id = _env_str("CF_ZONE_ID", "")
    cfg.cloudflare.r2_bucket = _env_str("CF_R2_BUCKET", "gula-reports")

    cfg.supabase.url = _env_str("SUPABASE_URL", "")
    cfg.supabase.anon_key = _env_str("SUPABASE_ANON_KEY", "")
    cfg.supabase.service_key = _env_str("SUPABASE_SERVICE_KEY", "")

    cfg.rate_limit_auth = _env_int("RATE_LIMIT_AUTH", 10)
    cfg.rate_limit_public = _env_int("RATE_LIMIT_PUBLIC", 30)
    cfg.max_upload_size_mb = _env_int("MAX_UPLOAD_SIZE_MB", 2)
    cfg.max_request_body_mb = _env_int("MAX_REQUEST_BODY_MB", 10)
    cfg.max_concurrent_requests = _env_int("MAX_CONCURRENT_REQUESTS", 50)

    cfg.enable_financial_engine = _env_bool("ENABLE_FINANCIAL_ENGINE", False)
    cfg.enable_ads = _env_bool("ENABLE_ADS", False)
    cfg.feature_background_tasks = _env_bool("FEATURE_BACKGROUND_TASKS", True)
    cfg.runtime_mode = _env_str("RUNTIME_MODE", "api")
    cfg.sentry_dsn = _env_str("SENTRY_DSN", "")

    return cfg
