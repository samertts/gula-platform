from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.kernel.config.secrets import SecretsLoader
from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.control_plane.config.secrets")


class SecretsManager:
    def __init__(self):
        self._loader: SecretsLoader | None = None
        self._rotation_history: list[dict[str, Any]] = []

    def _get_loader(self) -> SecretsLoader:
        if self._loader is None:
            kernel = get_kernel()
            config_reg = kernel.get_component("config_registry")
            if config_reg and hasattr(config_reg, "secrets"):
                self._loader = config_reg.secrets
            else:
                self._loader = SecretsLoader()
        return self._loader

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._get_loader().get(key, default)

    def get_required(self, key: str) -> str:
        return self._get_loader().get_required(key)

    def load_from_env(self, prefix: str = "SECRET_") -> int:
        loader = self._get_loader()
        before = len(loader._secrets)
        loader.load_from_env(prefix)
        after = len(loader._secrets)
        loaded = after - before
        logger.info("Loaded %d secrets with prefix '%s'", loaded, prefix)
        return loaded

    def rotate(self, key: str, new_value: str) -> bool:
        loader = self._get_loader()
        old_value = loader._secrets.get(key)
        if old_value is None:
            return False
        self._rotation_history.append({
            "key": key,
            "rotated_at": datetime.now(UTC).isoformat(),
            "len_old": len(old_value),
            "len_new": len(new_value),
        })
        loader._secrets[key] = new_value
        logger.info("Secret rotated: %s", key)
        return True

    def access_audit_log(self, key: str, user_id: int | None = None) -> dict[str, Any]:
        import uuid
        return {
            "event_id": str(uuid.uuid4()),
            "action": "secret_access",
            "secret_key": key,
            "user_id": user_id,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def list_secrets(self) -> list[str]:
        loader = self._get_loader()
        return list(loader._secrets.keys())

    def rotation_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._rotation_history[-limit:]
