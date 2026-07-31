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


class SecretsManager:
    """Env-backed secret manager for kernel runtime integration.

    Provides the `get_secrets(path)` contract consumed by SecretInjector
    (app.kernel.runtime_security). Paths map to env variables via the
    GULA_VAULT_ prefix, e.g. GULA_VAULT_path__key.
    """

    def __init__(self) -> None:
        self._loader = SecretsLoader()
        self._loader.load_from_env("GULA_VAULT_")

    def get_secrets(self, vault_path: str) -> dict[str, str]:
        prefix = f"GULA_VAULT_{vault_path.strip('/').upper().replace('/', '__')}_"
        resolved: dict[str, str] = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                resolved[key[len(prefix):].lower()] = value
        return resolved
