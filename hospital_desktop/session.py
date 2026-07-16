from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from config import get_config_path


class SessionManager:
    _instance: SessionManager | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self.user_info: dict[str, Any] = {}
        self.token: str = ""
        self.refresh_token: str = ""
        self._session_path = get_config_path() / "session.enc"
        self._key = self._get_or_create_key()

    def _get_or_create_key(self) -> bytes:
        key_path = get_config_path() / ".session_key"
        if key_path.exists():
            return key_path.read_bytes()
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(b"NHDW_SESSION_SECRET_v1"))
        key_path.write_bytes(key)
        return key

    @property
    def is_authenticated(self) -> bool:
        return bool(self.token) and bool(self.user_info)

    @property
    def role(self) -> str:
        return self.user_info.get("role", "")

    @property
    def user_id(self) -> str:
        return self.user_info.get("id", "")

    @property
    def name(self) -> str:
        return self.user_info.get("name", "")

    @property
    def lab_id(self) -> str:
        return self.user_info.get("lab_id", "")

    @property
    def department(self) -> str:
        return self.user_info.get("department", "")

    @property
    def permissions(self) -> list[str]:
        return self.user_info.get("permissions", [])

    def has_role(self, role: str) -> bool:
        return self.role == role

    def has_any_role(self, roles: list[str]) -> bool:
        return self.role in roles

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions

    def set_session(self, user_info: dict, token: str, refresh_token: str = ""):
        self.user_info = user_info
        self.token = token
        self.refresh_token = refresh_token
        self.save_session()

    def save_session(self):
        data = json.dumps({
            "user_info": self.user_info,
            "token": self.token,
            "refresh_token": self.refresh_token,
        })
        try:
            f = Fernet(self._key)
            encrypted = f.encrypt(data.encode())
            self._session_path.write_bytes(encrypted)
        except Exception:
            pass

    def load_session(self) -> bool:
        if not self._session_path.exists():
            return False
        try:
            encrypted = self._session_path.read_bytes()
            f = Fernet(self._key)
            data = json.loads(f.decrypt(encrypted).decode())
            self.user_info = data.get("user_info", {})
            self.token = data.get("token", "")
            self.refresh_token = data.get("refresh_token", "")
            return True
        except Exception:
            self.clear_session()
            return False

    def clear_session(self):
        self.user_info = {}
        self.token = ""
        self.refresh_token = ""
        if self._session_path.exists():
            self._session_path.unlink()

    def get_dashboard_config(self) -> dict:
        role = self.role
        configs = {
            "doctor": {
                "widgets": ["kpi", "trend", "alerts", "icu_status"],
                "views": ["dashboard", "patients", "clinical", "reports"],
            },
            "nurse": {
                "widgets": ["kpi", "department_occupancy", "alerts", "quick_actions"],
                "views": ["dashboard", "queue", "clinical", "communication"],
            },
            "administrator": {
                "widgets": ["kpi", "department_occupancy", "trend", "alerts", "icu_status",
                            "quick_actions", "admissions_table"],
                "views": ["dashboard", "patients", "admissions", "queue", "clinical",
                          "communication", "resources", "reports", "settings"],
            },
            "receptionist": {
                "widgets": ["kpi", "quick_actions", "admissions_table"],
                "views": ["dashboard", "patients", "admissions", "queue"],
            },
            "technician": {
                "widgets": ["kpi", "alerts"],
                "views": ["dashboard", "patients", "clinical"],
            },
        }
        return configs.get(role, configs["nurse"])
