import logging
from typing import Any

from platform.core.kernel import Kernel


class PluginRegistry:
    def __init__(self):
        self._logger = logging.getLogger("gula.plugins.registry")
        self._plugins: dict[str, dict[str, Any]] = {}
        self._hooks: dict[str, list[callable]] = {}

    def register(self, name: str, version: str, module: Any, hooks: dict[str, callable] | None = None) -> None:
        self._plugins[name] = {
            "name": name,
            "version": version,
            "module": module,
            "hooks": hooks or {},
        }
        if hooks:
            for hook_name, handler in hooks.items():
                self._hooks.setdefault(hook_name, []).append(handler)
        self._logger.info("Plugin registered: %s v%s", name, version)

    def unregister(self, name: str) -> None:
        plugin = self._plugins.pop(name, None)
        if plugin:
            for hook_name, handler in plugin.get("hooks", {}).items():
                handlers = self._hooks.get(hook_name, [])
                if handler in handlers:
                    handlers.remove(handler)
            self._logger.info("Plugin unregistered: %s", name)

    def execute_hook(self, hook_name: str, *args, **kwargs) -> list[Any]:
        results = []
        for handler in self._hooks.get(hook_name, []):
            try:
                result = handler(*args, **kwargs)
                if hasattr(result, "__await__"):
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                        result = loop.create_task(result)
                    except RuntimeError:
                        pass
                results.append(result)
            except Exception as e:
                self._logger.error("Hook '%s' handler error: %s", hook_name, e)
                results.append(None)
        return results

    def defined_hooks(self) -> list[str]:
        return list(self._hooks.keys())

    def registered_names(self) -> list[str]:
        return list(self._plugins.keys())

    def get_plugin(self, name: str) -> dict[str, Any] | None:
        return self._plugins.get(name)
