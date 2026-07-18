import json
import logging
import os
from typing import Any


class ConfigLoader:
    def __init__(self, paths: list[str] | None = None):
        self._logger = logging.getLogger("gula.kernel.config")
        self._paths = paths or []
        self._config: dict[str, Any] = {}
        self._loaded = False

    async def load(self) -> dict[str, Any]:
        self._config = {}
        for path in self._paths:
            await self._load_file(path)
        self._load_env_overrides()
        self._loaded = True
        self._logger.debug("Configuration loaded: %d keys", len(self._config))
        return self._config

    async def _load_file(self, path: str) -> None:
        if not os.path.exists(path):
            self._logger.debug("Config path not found: %s", path)
            return
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".json":
                with open(path) as f:
                    data = json.load(f)
                self._merge(data)
            elif ext in (".yaml", ".yml"):
                try:
                    import yaml
                    with open(path) as f:
                        data = yaml.safe_load(f)
                    if data:
                        self._merge(data)
                except ImportError:
                    self._logger.warning("PyYAML not available, skipping %s", path)
            else:
                self._logger.debug("Unsupported config format: %s", ext)
        except Exception as e:
            self._logger.error("Error loading config %s: %s", path, e)

    def _load_env_overrides(self) -> None:
        prefix = "GULA_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower().replace("__", ".").replace("_", ".")
                self._set_nested(config_key, value)

    def _merge(self, data: dict[str, Any], prefix: str = "") -> None:
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self._merge(value, full_key)
            else:
                self._set_nested(full_key, value)

    def _set_nested(self, key: str, value: Any) -> None:
        parts = key.split(".")
        current = self._config
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        if not self._loaded:
            return default
        parts = key.split(".")
        current = self._config
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def get_all(self) -> dict[str, Any]:
        return dict(self._config)

    def is_loaded(self) -> bool:
        return self._loaded
