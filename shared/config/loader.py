from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

_WEAK_PATTERNS: list[re.Pattern] = [
    re.compile(r"^(change|secret|password|key|test|weak|default)", re.IGNORECASE),
    re.compile(r"^(abc|123|qwerty)", re.IGNORECASE),
    re.compile(r"^[a-z]{1,8}$", re.IGNORECASE),
    re.compile(r"^\d{1,16}$"),
]


def _is_weak_secret(value: str | None) -> bool:
    if not value or len(value) < 16:
        return True
    for pattern in _WEAK_PATTERNS:
        if pattern.match(value):
            return True
    return False


@dataclass
class DatabaseConfig:
    url: str = ""
    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True
    statement_timeout: int = 30000


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


@dataclass
class SNDHSConfig:
    enable_visits: bool = False
    enable_national_id: bool = False


@dataclass
class NotificationConfig:
    fcm_server_key: str = ""
    apns_key: str = ""


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

    cfg.database.url = _env_str("DATABASE_URL", "")
    cfg.database.pool_size = _env_int("DB_POOL_SIZE", 5)
    cfg.database.max_overflow = _env_int("DB_MAX_OVERFLOW", 10)

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
    cfg.ai.groq_api_key = _env_str("GROQ_API_KEY", "")
    cfg.ai.ollama_base_url = _env_str("OLLAMA_BASE_URL", "")

    cfg.sndhs.enable_visits = _env_bool("SNDHS_ENABLE_VISITS", False)
    cfg.sndhs.enable_national_id = _env_bool("SNDHS_ENABLE_NATIONAL_ID", False)

    cfg.notification.fcm_server_key = _env_str("FCM_SERVER_KEY", "")
    cfg.notification.apns_key = _env_str("APNS_KEY", "")

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
