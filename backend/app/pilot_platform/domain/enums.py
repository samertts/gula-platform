from app._compat import StrEnum


class PilotPhase(StrEnum):
    INTERNAL_VALIDATION = "internal_validation"
    ALPHA = "alpha"
    BETA = "beta"
    CANARY = "canary"
    REGIONAL_ROLLOUT = "regional_rollout"
    NATIONAL_ROLLOUT = "national_rollout"
    GENERAL_AVAILABILITY = "general_availability"


class PilotStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class ReadinessLevel(StrEnum):
    NOT_READY = "not_ready"
    CONDITIONAL = "conditional"
    READY = "ready"
    CERTIFIED = "certified"


class DeploymentStrategy(StrEnum):
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    BIG_BANG = "big_bang"


class ValidationResult(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    CONDITIONAL_PASS = "conditional_pass"
    NOT_RUN = "not_run"


class CertificationMilestone(StrEnum):
    CODE_FREEZE = "code_freeze"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_BENCHMARK = "performance_benchmark"
    CLINICAL_SAFETY = "clinical_safety"
    FHIR_COMPLIANCE = "fhir_compliance"
    USER_ACCEPTANCE = "user_acceptance"
    REGULATORY_APPROVAL = "regulatory_approval"
    GO_LIVE = "go_live"
