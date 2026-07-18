from enum import Enum
from typing import Any


class MigrationState(str, Enum):
    MONOLITH = "monolith"
    BRIDGE = "bridge"
    NATIVE = "native"


class ServiceBridge:
    def __init__(self):
        self._routing: dict[str, dict[str, Any]] = {}

    def register(self, service_name: str, monolith_impl: Any | None = None, native_impl: Any | None = None, state: MigrationState = MigrationState.BRIDGE) -> None:
        self._routing[service_name] = {
            "monolith": monolith_impl,
            "native": native_impl,
            "state": state,
        }

    def resolve(self, service_name: str) -> Any:
        entry = self._routing.get(service_name)
        if entry is None:
            raise KeyError(f"Service '{service_name}' not registered in bridge")
        if entry["state"] == MigrationState.NATIVE and entry.get("native"):
            return entry["native"]
        if entry["state"] == MigrationState.MONOLITH and entry.get("monolith"):
            return entry["monolith"]
        return entry.get("native") or entry.get("monolith")

    def set_state(self, service_name: str, state: MigrationState) -> None:
        if service_name in self._routing:
            self._routing[service_name]["state"] = state

    def get_state(self, service_name: str) -> MigrationState | None:
        entry = self._routing.get(service_name)
        if entry:
            return entry["state"]
        return None

    def registered_services(self) -> list[str]:
        return list(self._routing.keys())

    def summary(self) -> dict[str, str]:
        return {name: entry["state"].value for name, entry in self._routing.items()}


class ModelBridge:
    def __init__(self, monolith_adapter=None):
        self._monolith = monolith_adapter
        self._model_cache: dict[str, Any] = {}

    def get_model(self, name: str) -> Any:
        if name not in self._model_cache and self._monolith:
            self._model_cache[name] = self._monolith.get_model(name)
        return self._model_cache.get(name)

    def register_model(self, name: str, model_class: Any) -> None:
        self._model_cache[name] = model_class

    def clear_cache(self) -> None:
        self._model_cache.clear()
