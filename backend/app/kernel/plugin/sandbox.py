from __future__ import annotations

import logging

logger = logging.getLogger("gula.kernel.plugin.sandbox")


class PluginSandbox:
    def __init__(self):
        self._allowed_modules: set[str] = {
            "json",
            "logging",
            "datetime",
            "uuid",
            "typing",
            "dataclasses",
            "enum",
            "math",
            "re",
            "pathlib",
        }
        self._blocked_modules: set[str] = {
            "os",
            "subprocess",
            "shutil",
            "socket",
            "ctypes",
            "multiprocessing",
            "threading",
            "signal",
        }
        self._allowed_attributes: dict[str, set[str]] = {
            "os": {"path", "environ", "getenv"},
        }

    def is_module_allowed(self, module_name: str) -> bool:
        return module_name not in self._blocked_modules

    def is_attribute_allowed(self, module_name: str, attr: str) -> bool:
        if module_name in self._allowed_attributes:
            return attr in self._allowed_attributes[module_name]
        return True
