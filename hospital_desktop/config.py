from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_API_BASE_URL = "https://api.gula-platform.org/api/v1"
_ALLOWED_HTTPS_HOSTS = frozenset({
    "api.gula-platform.org",
    "staging-api.gula-platform.org",
})
_ALLOWED_LOCAL_HOSTS = frozenset({
    "localhost",
    "127.0.0.1",
    "::1",
    "10.0.2.2",
})


def validate_api_base_url(value: str) -> str:
    """Validate the desktop API endpoint before it can receive credentials."""
    url = value.strip().rstrip("/")
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")

    if parsed.scheme not in {"https", "http"} or not hostname:
        raise ValueError("API URL must use https:// with an approved host")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("API URL must not contain credentials, query, or fragment data")
    if parsed.scheme == "https" and hostname not in _ALLOWED_HTTPS_HOSTS:
        raise ValueError("HTTPS API host is not approved")
    if parsed.scheme == "http" and hostname not in _ALLOWED_LOCAL_HOSTS:
        raise ValueError("Plain HTTP is allowed only for local development")
    if not parsed.path.startswith("/api/v1") and hostname not in _ALLOWED_LOCAL_HOSTS:
        raise ValueError("Production API URL must include the /api/v1 path")
    return url


@dataclass
class AppConfig:
    api_base_url: str = DEFAULT_API_BASE_URL
    theme: str = "dark"
    language: str = "ar"
    cache_enabled: bool = True
    offline_mode: bool = False
    auto_sync_interval: int = 60
    auto_refresh_interval: int = 30
    session_timeout_minutes: int = 480
    notifications_enabled: bool = True
    minimize_to_tray: bool = True
    check_updates: bool = True
    geometry: dict | None = None
    window_state: dict | None = None
    dock_positions: dict | None = None
    feature_flags: dict[str, bool] = field(default_factory=lambda: {
        "admissions": True,
        "discharges": True,
        "transfers": True,
        "queue_management": True,
        "clinical_tasks": True,
        "ward_rounds": True,
        "vital_signs": True,
        "care_plans": True,
        "messaging": True,
        "critical_alerts": True,
        "bed_management": True,
        "equipment_tracking": True,
        "or_schedule": True,
        "reports": True,
        "analytics": True,
        "export_pdf": True,
        "export_excel": True,
        "patient_registration": True,
        "patient_search": True,
    })

    def __post_init__(self):
        self.api_base_url = validate_api_base_url(self.api_base_url)

    def is_feature_enabled(self, flag: str) -> bool:
        return self.feature_flags.get(flag, False)

    def set_feature_flag(self, flag: str, enabled: bool):
        self.feature_flags[flag] = enabled


def get_config_path() -> Path:
    system = platform.system().lower()
    if system == "windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    path = base / "NHDW"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_config() -> AppConfig:
    config_path = get_config_path() / "config.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            return AppConfig(**data)
        except (json.JSONDecodeError, TypeError, KeyError, ValueError):
            pass
    return AppConfig()


def save_config(config: AppConfig):
    config.api_base_url = validate_api_base_url(config.api_base_url)
    config_path = get_config_path() / "config.json"
    config_path.write_text(
        json.dumps(config.__dict__, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
