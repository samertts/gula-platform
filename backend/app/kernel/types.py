from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar

T = TypeVar("T")


class ServiceLifecycle(Enum):
    TRANSIENT = auto()
    SCOPED = auto()
    SINGLETON = auto()


class LogLevel(Enum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class ServiceDescriptor:
    name: str
    interface: type | None
    implementation: type
    lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    lazy: bool = False


@dataclass
class CapabilityDescriptor:
    name: str
    version: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    required: bool = False
    enabled: bool = True


@dataclass
class PluginDescriptor:
    name: str
    version: str
    path: str
    entry_point: str
    dependencies: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class ModuleDescriptor:
    name: str
    version: str
    path: str
    dependencies: dict[str, str] = field(default_factory=dict)
    entry_points: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class EventDescriptor:
    name: str
    version: int = 1
    schema: dict | None = None


@dataclass
class TenantDescriptor:
    id: str
    name: str
    slug: str
    plan: str = "free"
    features: dict[str, bool] = field(default_factory=dict)
    quotas: dict[str, int] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    active: bool = True
