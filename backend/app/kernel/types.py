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



class CapabilityMaturity(Enum):
    """How far a capability has been proven, independently of whether it is on.

    PROGRAM-EXT-001. `CapabilityStatus` says what the platform does with a
    capability; maturity says how much evidence stands behind it. They move
    independently: a capability can be ACTIVE and still EXPERIMENTAL, and
    promoting one is not promoting the other.
    """

    PROPOSED = "proposed"
    DESIGNED = "designed"
    EXPERIMENTAL = "experimental"
    INTERNAL = "internal"
    PILOT = "pilot"
    VALIDATED = "validated"
    PRODUCTION = "production"
    NATIONAL = "national"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class TenantScope(Enum):
    """Whose data a capability reads and writes.

    Declared rather than inferred, because the tenancy rule is the one thing a
    reviewer cannot read off a signature. NATIONAL_REFERENCE means reference
    data shared by every tenant (terminology, code systems); it is not an
    exemption from tenant isolation, it is a statement that the data has no
    tenant.
    """

    TENANT = "tenant"
    ORGANIZATION = "organization"
    FACILITY = "facility"
    NATIONAL_REFERENCE = "national_reference"
    PLATFORM = "platform"


class FeatureFlagClass(Enum):
    """What a flag's audience is — never what a caller is allowed to do.

    A flag decides whether a capability is present. Authorization decides
    whether this actor may use it. The two are enforced in different places and
    a flag must never stand in for the second; `test_a_feature_flag_is_never_an
    _authorization_decision` holds that line.
    """

    EXPERIMENTAL = "experimental"
    INTERNAL = "internal"
    PILOT = "pilot"
    PRODUCTION = "production"
    NATIONAL = "national"
    DEPRECATED = "deprecated"


@dataclass
class CapabilityDeprecation:
    """What happens to consumers when a capability goes away.

    An empty deprecation is the normal state. A capability whose maturity is
    DEPRECATED or RETIRED must carry a populated one, which is the only way a
    consumer learns what to move to and by when.
    """

    since_version: str = ""
    removal_version: str = ""
    replacement: str = ""
    migration_notes: str = ""

    def is_declared(self) -> bool:
        return bool(self.since_version and self.removal_version and self.replacement)


@dataclass
class CapabilityAudit:
    """The audit obligations a capability accepts.

    `writes_audit` is a claim that the capability records its own mutations;
    `data_classification` is what a reviewer needs in order to decide how much
    that matters. A capability touching CLINICAL_SENSITIVE data that does not
    write audit is a finding, not a configuration.
    """

    writes_audit: bool = False
    audit_service: str = ""
    data_classification: str = "INTERNAL"
    retention_days: int = 0


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
    # ── PROGRAM-EXT-001: the metadata a future capability must declare ───────
    # Every field below is additive with a default, so the 52 descriptors that
    # predate this contract still construct. What changes is that new ones are
    # measured against it: tests/test_extensibility_guards.py refuses a
    # descriptor that leaves the normative set empty.
    maturity: CapabilityMaturity = CapabilityMaturity.PRODUCTION
    tenant_scope: TenantScope = TenantScope.TENANT
    required_context: list[str] = field(default_factory=list)
    required_permissions: list[str] = field(default_factory=list)
    audit: CapabilityAudit = field(default_factory=CapabilityAudit)
    feature_flag: str = ""
    flag_class: FeatureFlagClass = FeatureFlagClass.PRODUCTION
    configuration: dict[str, Any] = field(default_factory=dict)
    fhir_mappings: dict[str, str] = field(default_factory=dict)
    deprecation: CapabilityDeprecation = field(default_factory=CapabilityDeprecation)
    data_contracts: list[str] = field(default_factory=list)


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
