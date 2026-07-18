import logging
import threading
from typing import Any


class PluginSandbox:
    def __init__(self, resource_limits: dict[str, Any] | None = None):
        self._logger = logging.getLogger("gula.plugins.sandbox")
        self._limits = resource_limits or {"max_memory_mb": 256, "max_execution_time": 30}
        self._local = threading.local()

    def execute(self, plugin_name: str, fn: callable, *args, **kwargs) -> Any:
        self._local.active_plugin = plugin_name
        try:
            result = fn(*args, **kwargs)
            return result
        finally:
            self._local.active_plugin = None

    def active_plugin(self) -> str | None:
        return getattr(self._local, "active_plugin", None)
