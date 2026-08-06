import logging
from collections.abc import Callable
from typing import Any


class DIContainer:
    def __init__(self):
        self._logger = logging.getLogger("gula.kernel.di")
        self._instances: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}
        self._scoped_instances: dict[str, dict[str, Any]] = {}
        self._singletons: set[str] = set()

    def register_instance(self, name: str, instance: Any) -> None:
        self._instances[name] = instance
        self._singletons.add(name)

    def register_factory(self, name: str, factory: Callable[[], Any], singleton: bool = True) -> None:
        self._factories[name] = factory
        if singleton:
            self._singletons.add(name)

    def register_scoped(self, name: str, factory: Callable[[], Any]) -> None:
        self._factories[name] = factory

    def resolve(self, name: str, scope: str | None = None) -> Any:
        if scope and scope in self._scoped_instances and name in self._scoped_instances[scope]:
            return self._scoped_instances[scope][name]
        if name in self._instances:
            return self._instances[name]
        if name in self._factories:
            instance = self._factories[name]()
            if name in self._singletons:
                self._instances[name] = instance
            elif scope:
                if scope not in self._scoped_instances:
                    self._scoped_instances[scope] = {}
                self._scoped_instances[scope][name] = instance
            return instance
        raise KeyError(f"Dependency '{name}' not registered in container")

    def get(self, name: str, default: Any = None) -> Any:
        try:
            return self.resolve(name)
        except KeyError:
            return default

    def create_scope(self, scope: str) -> None:
        if scope not in self._scoped_instances:
            self._scoped_instances[scope] = {}

    def dispose_scope(self, scope: str) -> None:
        if scope in self._scoped_instances:
            del self._scoped_instances[scope]

    def clear(self) -> None:
        self._instances.clear()
        self._factories.clear()
        self._scoped_instances.clear()
        self._singletons.clear()
