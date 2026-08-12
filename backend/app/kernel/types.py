from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, TypeVar

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


class CapabilityStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass
class CapabilityEvent:
    name: str
    version: int = 1
    description: str = ""
    type: str = "domain"  # domain, integration, notification


@dataclass
class CapabilityCommand:
    name: str
    description: str = ""
    input_schema: str = ""


@dataclass
class CapabilityQuery:
    name: str
    description: str = ""
    output_schema: str = ""


@dataclass
class CapabilityEntity:
    name: str
    description: str = ""
    fields: list[str] = field(default_factory=list)


@dataclass
class CapabilityDTO:
    name: str
    description: str = ""
    type: str = "request"  # request, response, view


@dataclass
class CapabilityPolicy:
    name: str
    description: str = ""
    severity: str = "info"  # info, warning, error


@dataclass
class CapabilityPermission:
    name: str
    description: str = ""
    resource: str = ""


@dataclass
class CapabilityAPI:
    path: str
    method: str = "GET"
    description: str = ""
    auth_required: bool = True


@dataclass
class CapabilityScore:
    quality: float = 0.0
    security: float = 0.0
    performance: float = 0.0
    reuse: float = 0.0


@dataclass
class CapabilityDescriptor:
    name: str
    version: str
    capability_id: str = ""
    description: str = ""
    owner: str = "platform-team"
    status: CapabilityStatus = CapabilityStatus.ACTIVE
    dependencies: list[str] = field(default_factory=list)
    events: list[CapabilityEvent] = field(default_factory=list)
    commands: list[CapabilityCommand] = field(default_factory=list)
    queries: list[CapabilityQuery] = field(default_factory=list)
    entities: list[CapabilityEntity] = field(default_factory=list)
    dto_types: list[CapabilityDTO] = field(default_factory=list)
    policies: list[CapabilityPolicy] = field(default_factory=list)
    permissions: list[CapabilityPermission] = field(default_factory=list)
    api_endpoints: list[CapabilityAPI] = field(default_factory=list)
    documentation: list[str] = field(default_factory=list)
    test_paths: list[str] = field(default_factory=list)
    adr_paths: list[str] = field(default_factory=list)
    scores: CapabilityScore = field(default_factory=CapabilityScore)
    required: bool = False
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    domain: str = "core"
    layer: str = "application"
    module_path: str = ""
    health_endpoint: str = ""


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
