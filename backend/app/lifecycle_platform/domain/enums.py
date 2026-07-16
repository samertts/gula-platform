from app._compat import StrEnum


class LifecycleStage(StrEnum):
    DEVELOPMENT = "development"
    ALPHA = "alpha"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    END_OF_LIFE = "end_of_life"
    RETIRED = "retired"
    SUNSET = "sunset"


class ReleaseChannel(StrEnum):
    EXPERIMENTAL = "experimental"
    CANARY = "canary"
    BETA = "beta"
    STABLE = "stable"
    LTS = "lts"
    SECURITY_PATCH = "security_patch"


class ReleaseStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComponentType(StrEnum):
    MODULE = "module"
    SERVICE = "service"
    LIBRARY = "library"
    API = "api"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    INFRASTRUCTURE = "infrastructure"


class CompatibilityLevel(StrEnum):
    FULL = "full"
    BACKWARD = "backward"
    BREAKING = "breaking"
    UNKNOWN = "unknown"
    INCOMPATIBLE = "incompatible"


class DeprecationPolicy(StrEnum):
    IMMEDIATE = "immediate"
    NOTICE_30_DAYS = "notice_30_days"
    NOTICE_60_DAYS = "notice_60_days"
    NOTICE_90_DAYS = "notice_90_days"
    NOTICE_180_DAYS = "notice_180_days"
    NOTICE_1_YEAR = "notice_1_year"


class UpgradeSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"
