from __future__ import annotations

import logging
import os

logger = logging.getLogger("gula.kernel.config.secrets")


class SecretsLoader:
    def __init__(self):
        self._secrets: dict[str, str] = {}

    def load_from_env(self, prefix: str = "SECRET_") -> None:
        for key, value in os.environ.items():
            if key.startswith(prefix):
                self._secrets[key] = value

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._secrets.get(key, default)

    def get_required(self, key: str) -> str:
        value = self._secrets.get(key)
        if value is None:
            raise KeyError(f"Required secret not found: {key}")
        return value
