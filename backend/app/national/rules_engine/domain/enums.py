from __future__ import annotations

from enum import Enum


class RuleCategory(Enum):
    CLINICAL = "clinical"
    ADMINISTRATIVE = "administrative"
    FINANCIAL = "financial"
    SECURITY = "security"
    POLICY = "policy"
    COMPLIANCE = "compliance"
    QUALITY = "quality"
    SAFETY = "safety"


class RuleSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    BLOCKER = "blocker"


class RuleStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class RuleExecutionMode(Enum):
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    SIMULATION = "simulation"
    AUDIT_ONLY = "audit_only"


class Operator(Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    MATCHES = "matches"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class RuleTrigger(Enum):
    ON_CREATE = "on_create"
    ON_UPDATE = "on_update"
    ON_DELETE = "on_delete"
    ON_READ = "on_read"
    ON_EVENT = "on_event"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class RuleOutcome(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"
    BLOCK = "block"
    FLAG = "flag"
    NOTIFY = "notify"
    ESCALATE = "escalate"
