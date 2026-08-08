from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModuleState(Enum):
    DISCOVERED = "discovered"
    RESOLVED = "resolved"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class ModuleManifest:
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    optional_dependencies: list[str] = field(default_factory=list)
    events_published: list[str] = field(default_factory=list)
    events_subscribed: list[str] = field(default_factory=list)
    commands_handled: list[str] = field(default_factory=list)
    queries_handled: list[str] = field(default_factory=list)
    permissions_required: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] | None = None
    health_check_interval: float = 30.0


class Module:
    def __init__(self, manifest: ModuleManifest):
        self._manifest = manifest
        self._state = ModuleState.DISCOVERED
        self._services: dict[str, Any] = {}

    @property
    def manifest(self) -> ModuleManifest:
        return self._manifest

    @property
    def state(self) -> ModuleState:
        return self._state

    @property
    def name(self) -> str:
        return self._manifest.name

    async def initialize(self) -> None:
        self._state = ModuleState.INITIALIZING
        await self.on_initialize()
        self._state = ModuleState.INITIALIZED

    async def start(self) -> None:
        self._state = ModuleState.STARTING
        await self.on_start()
        self._state = ModuleState.RUNNING

    async def stop(self) -> None:
        self._state = ModuleState.STOPPING
        await self.on_stop()
        self._state = ModuleState.STOPPED

    def register_service(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get_service(self, name: str) -> Any:
        return self._services.get(name)

    async def on_initialize(self) -> None:
        pass

    async def on_start(self) -> None:
        pass

    async def on_stop(self) -> None:
        pass
