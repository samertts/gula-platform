from __future__ import annotations

import logging
from typing import Any

from app.kernel.config.reload import RuntimeReloader
from app.kernel.config.secrets import SecretsLoader
from app.kernel.config.validation import ConfigurationValidator
from app.kernel.config.versioned import VersionedConfiguration

logger = logging.getLogger("gula.kernel.config.registry")


class ConfigurationRegistry:
    def __init__(self):
        self._config: dict[str, Any] = {}
        self.validator = ConfigurationValidator()
        self.secrets = SecretsLoader()
        self.reloader = RuntimeReloader(self)
        self.versioned = VersionedConfiguration()

    def set(self, key: str, value: Any) -> None:
        self.validator.validate(key, value)
        self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def get_required(self, key: str) -> Any:
        value = self._config.get(key)
        if value is None:
            raise KeyError(f"Required configuration key not found: {key}")
        return value

    def has(self, key: str) -> bool:
        return key in self._config

    def all(self) -> dict[str, Any]:
        return dict(self._config)
