from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class ReadinessState(StrEnum):
    DISCOVERED = "DISCOVERED"
    DESIGNING = "DESIGNING"
    BUILDING = "BUILDING"
    INTEGRATING = "INTEGRATING"
    REPAIRING = "REPAIRING"
    TESTING = "TESTING"
    IMPROVING = "IMPROVING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    READY_FOR_STAGING = "READY_FOR_STAGING"
    READY_FOR_PRODUCTION = "READY_FOR_PRODUCTION"
    EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"


@dataclass(frozen=True)
class WriteSafetyRequirements:
    authorization: bool = True
    object_authorization: bool = True
    tenant_isolation: bool = True
    audit: bool = True
    idempotency: bool = True
    concurrency: bool = True
    rate_limit: bool = True
    error_contract: bool = True


@dataclass(frozen=True)
class ContractDefinition:
    contract_id: str
    domain: str
    states: tuple[str, ...]
    transitions: Mapping[str, tuple[str, ...]]
    write_safety: WriteSafetyRequirements = field(default_factory=WriteSafetyRequirements)
    external_dependencies: tuple[str, ...] = ()

    def allows(self, current: str, requested: str) -> bool:
        return requested in self.transitions.get(current, ())


@dataclass(frozen=True)
class ContractEvidence:
    domain_model: bool = False
    state_machine: bool = False
    backend_contract: bool = False
    authorization: bool = False
    object_authorization: bool = False
    tenant_isolation: bool = False
    audit: bool = False
    idempotency: bool = False
    concurrency: bool = False
    rate_limits: bool = False
    error_contract: bool = False
    frontend_states: bool = False
    rtl_accessibility: bool = False
    offline_policy: bool = False
    unit_tests: bool = False
    integration_tests: bool = False
    contract_tests: bool = False
    security_tests: bool = False
    e2e_tests: bool = False
    performance_tests: bool = False
    remote_ci: bool = False
    staging: bool = False
    rollback: bool = False
    external_dependencies_ready: bool = False

    def missing(self, contract: ContractDefinition | None = None) -> tuple[str, ...]:
        required = [
            "domain_model", "state_machine", "backend_contract", "authorization",
            "object_authorization", "tenant_isolation", "audit", "rate_limits",
            "error_contract", "frontend_states", "rtl_accessibility", "offline_policy",
            "unit_tests", "integration_tests", "contract_tests", "security_tests",
            "e2e_tests", "performance_tests", "remote_ci", "staging", "rollback",
        ]
        if contract is None or contract.write_safety.idempotency:
            required.append("idempotency")
        if contract is None or contract.write_safety.concurrency:
            required.append("concurrency")
        missing = [name for name in required if not getattr(self, name)]
        if contract is not None and contract.external_dependencies and not self.external_dependencies_ready:
            missing.append("external_dependencies_ready")
        return tuple(missing)

    def readiness(self, contract: ContractDefinition) -> ReadinessState:
        if contract.external_dependencies and not self.external_dependencies_ready:
            return ReadinessState.EXTERNAL_DEPENDENCY
        missing = self.missing(contract)
        if not missing:
            return ReadinessState.READY_FOR_PRODUCTION
        review_gate = (
            self.domain_model
            and self.state_machine
            and self.backend_contract
            and self.authorization
            and self.object_authorization
            and self.tenant_isolation
            and self.audit
            and self.contract_tests
        )
        if review_gate:
            return ReadinessState.READY_FOR_REVIEW
        if self.state_machine or self.domain_model:
            return ReadinessState.BUILDING
        return ReadinessState.DISCOVERED


APPOINTMENT = ContractDefinition(
    contract_id="CONTRACT-001",
    domain="appointment",
    states=("REQUESTED", "CONFIRMED", "CHECKED_IN", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW", "RESCHEDULED", "EXPIRED"),
    transitions={
        "REQUESTED": ("CONFIRMED", "CANCELLED", "EXPIRED"),
        "CONFIRMED": ("CHECKED_IN", "CANCELLED", "RESCHEDULED", "NO_SHOW", "EXPIRED"),
        "CHECKED_IN": ("IN_PROGRESS", "NO_SHOW"),
        "IN_PROGRESS": ("COMPLETED",),
        "COMPLETED": (), "CANCELLED": (), "NO_SHOW": (), "RESCHEDULED": ("REQUESTED",), "EXPIRED": (),
    },
)

SESSION = ContractDefinition(
    contract_id="CONTRACT-002",
    domain="session",
    states=("ACTIVE", "EXPIRED", "TERMINATED", "REVOKED"),
    transitions={"ACTIVE": ("EXPIRED", "TERMINATED", "REVOKED"), "EXPIRED": (), "TERMINATED": (), "REVOKED": ()},
    write_safety=WriteSafetyRequirements(idempotency=False),
)

DEVICE = ContractDefinition(
    contract_id="CONTRACT-003",
    domain="device",
    states=("REGISTERED", "TRUSTED", "EXPIRED", "REVOKED"),
    transitions={"REGISTERED": ("TRUSTED", "REVOKED"), "TRUSTED": ("EXPIRED", "REVOKED"), "EXPIRED": ("REVOKED",), "REVOKED": ()},
    write_safety=WriteSafetyRequirements(idempotency=False),
)

PATIENT_ACCESS = ContractDefinition(
    contract_id="CONTRACT-004",
    domain="patient-access",
    states=("REQUESTED", "AUTHORIZED", "DENIED", "EXPIRED", "REVOKED"),
    transitions={"REQUESTED": ("AUTHORIZED", "DENIED", "EXPIRED"), "AUTHORIZED": ("EXPIRED", "REVOKED"), "DENIED": (), "EXPIRED": (), "REVOKED": ()},
)

CONSENT = ContractDefinition(
    contract_id="CONTRACT-005",
    domain="consent-sharing",
    states=("ACTIVE", "EXPIRED", "REVOKED"),
    transitions={"ACTIVE": ("EXPIRED", "REVOKED"), "EXPIRED": (), "REVOKED": ()},
)

ACCESS_HISTORY = ContractDefinition(
    contract_id="CONTRACT-006",
    domain="access-history",
    states=("RECORDED",),
    transitions={"RECORDED": ()},
    write_safety=WriteSafetyRequirements(idempotency=False),
)

DELEGATION = ContractDefinition(
    contract_id="CONTRACT-007",
    domain="delegation",
    states=("REQUESTED", "ACTIVE", "EXPIRED", "REVOKED", "REJECTED"),
    transitions={"REQUESTED": ("ACTIVE", "REJECTED", "REVOKED"), "ACTIVE": ("EXPIRED", "REVOKED"), "EXPIRED": (), "REVOKED": (), "REJECTED": ()},
)

TASK = ContractDefinition(
    contract_id="CONTRACT-008",
    domain="task",
    states=("PENDING", "IN_PROGRESS", "COMPLETED", "SKIPPED", "CANCELLED", "EXPIRED"),
    transitions={"PENDING": ("IN_PROGRESS", "SKIPPED", "CANCELLED", "EXPIRED"), "IN_PROGRESS": ("COMPLETED", "SKIPPED", "CANCELLED", "EXPIRED"), "COMPLETED": (), "SKIPPED": (), "CANCELLED": (), "EXPIRED": ()},
)

ENCOUNTER = ContractDefinition(
    contract_id="CONTRACT-009",
    domain="encounter",
    states=("PLANNED", "CHECKED_IN", "DRAFT", "IN_PROGRESS", "COMPLETED", "SIGNED", "AMENDMENT", "AMENDED", "CANCELLED"),
    transitions={
        "PLANNED": ("CHECKED_IN", "CANCELLED"),
        "CHECKED_IN": ("IN_PROGRESS", "CANCELLED"),
        "DRAFT": ("IN_PROGRESS", "CANCELLED"),
        "IN_PROGRESS": ("COMPLETED",),
        "COMPLETED": ("SIGNED",),
        "SIGNED": ("AMENDMENT", "AMENDED"),
        "AMENDMENT": ("SIGNED",),
        "AMENDED": ("SIGNED",),
        "CANCELLED": (),
    },
)

CLINICAL_NOTE = ContractDefinition(
    contract_id="CONTRACT-010",
    domain="clinical-note",
    states=("DRAFT", "IN_PROGRESS", "COMPLETED", "SIGNED", "AMENDMENT", "AMENDED"),
    transitions={"DRAFT": ("IN_PROGRESS", "COMPLETED"), "IN_PROGRESS": ("COMPLETED",), "COMPLETED": ("SIGNED",), "SIGNED": ("AMENDMENT", "AMENDED"), "AMENDMENT": ("SIGNED",), "AMENDED": ("SIGNED",)},
)

LAB_ORDER = ContractDefinition(
    contract_id="CONTRACT-011",
    domain="lab-order",
    states=("DRAFT", "PLACED", "ACCEPTED", "IN_PROGRESS", "COMPLETED", "REJECTED", "CANCELLED"),
    transitions={"DRAFT": ("PLACED", "CANCELLED"), "PLACED": ("ACCEPTED", "REJECTED", "CANCELLED"), "ACCEPTED": ("IN_PROGRESS", "REJECTED", "CANCELLED"), "IN_PROGRESS": ("COMPLETED", "REJECTED"), "COMPLETED": (), "REJECTED": (), "CANCELLED": ()},
)

SPECIMEN = ContractDefinition(
    contract_id="CONTRACT-012",
    domain="specimen",
    states=("ORDERED", "COLLECTED", "RECEIVED", "PROCESSING", "ANALYZING", "VALIDATED", "REJECTED"),
    transitions={"ORDERED": ("COLLECTED", "REJECTED"), "COLLECTED": ("RECEIVED", "REJECTED"), "RECEIVED": ("PROCESSING", "REJECTED"), "PROCESSING": ("ANALYZING", "REJECTED"), "ANALYZING": ("VALIDATED", "REJECTED"), "VALIDATED": (), "REJECTED": ()},
)

RESULT = ContractDefinition(
    contract_id="CONTRACT-013",
    domain="result",
    states=("DRAFT", "TECHNICALLY_VALIDATED", "CLINICALLY_VALIDATED", "RELEASED", "CORRECTED", "AMENDED"),
    transitions={"DRAFT": ("TECHNICALLY_VALIDATED",), "TECHNICALLY_VALIDATED": ("CLINICALLY_VALIDATED",), "CLINICALLY_VALIDATED": ("RELEASED",), "RELEASED": ("CORRECTED", "AMENDED"), "CORRECTED": ("RELEASED",), "AMENDED": ("RELEASED",)},
)

CRITICAL_RESULT = ContractDefinition(
    contract_id="CONTRACT-014",
    domain="critical-result",
    states=("DETECTED", "NOTIFIED", "ACKNOWLEDGED", "ACTIONED", "ESCALATED", "CLOSED"),
    transitions={"DETECTED": ("NOTIFIED", "ESCALATED"), "NOTIFIED": ("ACKNOWLEDGED", "ESCALATED"), "ACKNOWLEDGED": ("ACTIONED", "ESCALATED"), "ACTIONED": ("CLOSED",), "ESCALATED": ("ACKNOWLEDGED", "ACTIONED", "CLOSED"), "CLOSED": ()},
)

PRESCRIPTION = ContractDefinition(
    contract_id="CONTRACT-016",
    domain="prescription",
    states=("DRAFT", "SIGNED", "AMENDED", "CANCELLED", "COMPLETED"),
    transitions={"DRAFT": ("SIGNED", "CANCELLED"), "SIGNED": ("AMENDED", "COMPLETED"), "AMENDED": ("SIGNED", "COMPLETED"), "COMPLETED": (), "CANCELLED": ()},
)

DISPENSE = ContractDefinition(
    contract_id="CONTRACT-017",
    domain="dispense",
    states=("PREPARED", "PARTIAL", "COMPLETED", "REVERSED"),
    transitions={"PREPARED": ("PARTIAL", "COMPLETED"), "PARTIAL": ("COMPLETED", "REVERSED"), "COMPLETED": (), "REVERSED": ()},
)

IMAGING_ORDER = ContractDefinition(
    contract_id="CONTRACT-018",
    domain="imaging-order",
    states=("DRAFT", "PLACED", "SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"),
    transitions={"DRAFT": ("PLACED", "CANCELLED"), "PLACED": ("SCHEDULED", "CANCELLED"), "SCHEDULED": ("IN_PROGRESS", "CANCELLED"), "IN_PROGRESS": ("COMPLETED",), "COMPLETED": (), "CANCELLED": ()},
)

IMAGING_STUDY = ContractDefinition(
    contract_id="CONTRACT-019",
    domain="imaging-study",
    states=("RECEIVED", "MATCHED", "ACQUIRED", "COMPLETED", "QUARANTINED"),
    transitions={"RECEIVED": ("MATCHED", "QUARANTINED"), "MATCHED": ("ACQUIRED", "COMPLETED", "QUARANTINED"), "ACQUIRED": ("COMPLETED", "QUARANTINED"), "COMPLETED": (), "QUARANTINED": ()},
)

IMAGING_REPORT = ContractDefinition(
    contract_id="CONTRACT-020",
    domain="imaging-report",
    states=("DRAFT", "SIGNED", "RELEASED", "AMENDED"),
    transitions={"DRAFT": ("SIGNED",), "SIGNED": ("RELEASED", "AMENDED"), "RELEASED": ("AMENDED",), "AMENDED": (),},
)

CLINICAL_RECORD = ContractDefinition(
    contract_id="CONTRACT-021",
    domain="clinical-record",
    states=("PROJECTED",),
    transitions={"PROJECTED": ()},
    write_safety=WriteSafetyRequirements(idempotency=False, concurrency=False),
)

HOSPITAL_ADMISSION = ContractDefinition(
    contract_id="CONTRACT-022",
    domain="hospital-admission",
    states=("REQUESTED", "ACCEPTED", "ADMITTED", "IN_CARE", "DISCHARGE_PLANNED", "DISCHARGED", "CANCELLED", "REJECTED", "TRANSFERRED"),
    transitions={
        "REQUESTED": ("ACCEPTED", "REJECTED", "CANCELLED"),
        "ACCEPTED": ("ADMITTED", "REJECTED", "CANCELLED"),
        "ADMITTED": ("IN_CARE", "DISCHARGE_PLANNED", "TRANSFERRED"),
        "IN_CARE": ("DISCHARGE_PLANNED", "TRANSFERRED"),
        "DISCHARGE_PLANNED": ("DISCHARGED", "CANCELLED"),
        "DISCHARGED": (), "CANCELLED": (), "REJECTED": (), "TRANSFERRED": (),
    },
)

HOSPITAL_TASK = ContractDefinition(
    contract_id="CONTRACT-023",
    domain="hospital-task",
    states=("OPEN", "CLAIMED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "DEFERRED"),
    transitions={
        "OPEN": ("CLAIMED", "CANCELLED", "DEFERRED"),
        "CLAIMED": ("IN_PROGRESS", "COMPLETED", "CANCELLED", "DEFERRED"),
        "IN_PROGRESS": ("COMPLETED", "CANCELLED", "DEFERRED"),
        "COMPLETED": (), "CANCELLED": (), "DEFERRED": (),
    },
)

HOSPITAL_EMAR = ContractDefinition(
    contract_id="CONTRACT-024",
    domain="hospital-emar",
    states=("ORDERED", "VERIFIED", "SCHEDULED", "ADMINISTERED", "HELD", "REFUSED", "MISSED", "CANCELLED"),
    transitions={
        "ORDERED": ("VERIFIED", "HELD", "REFUSED", "MISSED", "CANCELLED"),
        "VERIFIED": ("SCHEDULED", "ADMINISTERED", "HELD", "REFUSED", "MISSED", "CANCELLED"),
        "SCHEDULED": ("ADMINISTERED", "HELD", "REFUSED", "MISSED", "CANCELLED"),
        "ADMINISTERED": (), "HELD": (), "REFUSED": (), "MISSED": (), "CANCELLED": (),
    },
)

HOSPITAL_TRANSFER = ContractDefinition(
    contract_id="CONTRACT-025",
    domain="hospital-transfer",
    states=("REQUESTED", "ACCEPTED", "PREPARING", "IN_TRANSIT", "RECEIVED", "COMPLETED", "CANCELLED", "REJECTED"),
    transitions={
        "REQUESTED": ("ACCEPTED", "REJECTED", "CANCELLED"),
        "ACCEPTED": ("PREPARING", "REJECTED", "CANCELLED"),
        "PREPARING": ("IN_TRANSIT", "CANCELLED"),
        "IN_TRANSIT": ("RECEIVED", "CANCELLED"),
        "RECEIVED": ("COMPLETED",),
        "COMPLETED": (), "CANCELLED": (), "REJECTED": (),
    },
)

HOSPITAL_DISCHARGE = ContractDefinition(
    contract_id="CONTRACT-026",
    domain="hospital-discharge",
    states=("PLANNED", "APPROVED", "COMPLETED", "CANCELLED"),
    transitions={"PLANNED": ("APPROVED", "COMPLETED", "CANCELLED"), "APPROVED": ("COMPLETED", "CANCELLED"), "COMPLETED": (), "CANCELLED": ()},
)

EMERGENCY_INCIDENT = ContractDefinition(
    contract_id="CONTRACT-027",
    domain="emergency-incident",
    states=("REPORTED", "TRIAGED", "DISPATCHED", "EN_ROUTE", "ON_SCENE", "TRANSPORTING", "AT_DESTINATION", "HANDOVER_COMPLETE", "CLOSED", "CANCELLED"),
    transitions={
        "REPORTED": ("TRIAGED", "CANCELLED"),
        "TRIAGED": ("DISPATCHED", "CANCELLED"),
        "DISPATCHED": ("EN_ROUTE", "CANCELLED"),
        "EN_ROUTE": ("ON_SCENE", "CANCELLED"),
        "ON_SCENE": ("TRANSPORTING", "AT_DESTINATION", "CANCELLED"),
        "TRANSPORTING": ("AT_DESTINATION", "HANDOVER_COMPLETE", "CANCELLED"),
        "AT_DESTINATION": ("HANDOVER_COMPLETE",),
        "HANDOVER_COMPLETE": ("CLOSED",),
        "CLOSED": (), "CANCELLED": (),
    },
)

EMERGENCY_DISPATCH = ContractDefinition(
    contract_id="CONTRACT-028",
    domain="emergency-dispatch",
    states=("ASSIGNED", "EN_ROUTE", "ON_SCENE", "TRANSPORTING", "AT_DESTINATION", "COMPLETED", "CANCELLED"),
    transitions={
        "ASSIGNED": ("EN_ROUTE", "CANCELLED"),
        "EN_ROUTE": ("ON_SCENE", "CANCELLED"),
        "ON_SCENE": ("TRANSPORTING", "AT_DESTINATION", "CANCELLED"),
        "TRANSPORTING": ("AT_DESTINATION", "CANCELLED"),
        "AT_DESTINATION": ("COMPLETED",),
        "COMPLETED": (), "CANCELLED": (),
    },
)

LIS_ANALYZER = ContractDefinition(
    contract_id="CONTRACT-029",
    domain="lis-analyzer",
    states=("REGISTERED", "VALIDATED", "ACTIVE", "MAINTENANCE", "QUARANTINED", "RETIRED"),
    transitions={"REGISTERED": ("VALIDATED", "QUARANTINED", "RETIRED"), "VALIDATED": ("ACTIVE", "MAINTENANCE", "QUARANTINED", "RETIRED"), "ACTIVE": ("MAINTENANCE", "QUARANTINED", "RETIRED"), "MAINTENANCE": ("ACTIVE", "QUARANTINED", "RETIRED"), "QUARANTINED": ("VALIDATED", "RETIRED"), "RETIRED": ()},
)

LIS_QC = ContractDefinition(
    contract_id="CONTRACT-030",
    domain="lis-qc",
    states=("PENDING", "PASS", "FAILED", "OVERRIDDEN"),
    transitions={"PENDING": ("PASS", "FAILED", "OVERRIDDEN"), "PASS": (), "FAILED": (), "OVERRIDDEN": ()},
)

FINANCIAL_COVERAGE = ContractDefinition(
    contract_id="CONTRACT-031",
    domain="financial-coverage",
    states=("PENDING", "ACTIVE", "EXPIRED", "SUSPENDED", "UNKNOWN", "TERMINATED"),
    transitions={"PENDING": ("ACTIVE", "SUSPENDED", "UNKNOWN", "TERMINATED"), "ACTIVE": ("EXPIRED", "SUSPENDED", "TERMINATED"), "SUSPENDED": ("ACTIVE", "TERMINATED"), "EXPIRED": (), "UNKNOWN": ("ACTIVE", "SUSPENDED", "TERMINATED"), "TERMINATED": ()},
    external_dependencies=("insurance-provider",),
)

FINANCIAL_ELIGIBILITY = ContractDefinition(
    contract_id="CONTRACT-032",
    domain="financial-eligibility",
    states=("REQUESTED", "PROCESSING", "ELIGIBLE", "INELIGIBLE", "UNKNOWN", "FAILED"),
    transitions={"REQUESTED": ("PROCESSING", "UNKNOWN", "FAILED"), "PROCESSING": ("ELIGIBLE", "INELIGIBLE", "UNKNOWN", "FAILED"), "ELIGIBLE": (), "INELIGIBLE": (), "UNKNOWN": (), "FAILED": ()},
    external_dependencies=("insurance-provider",),
)

FINANCIAL_PREAUTH = ContractDefinition(
    contract_id="CONTRACT-033",
    domain="financial-preauthorization",
    states=("REQUESTED", "UNDER_REVIEW", "APPROVED", "PARTIALLY_APPROVED", "DENIED", "EXPIRED", "CANCELLED"),
    transitions={"REQUESTED": ("UNDER_REVIEW", "DENIED", "EXPIRED", "CANCELLED"), "UNDER_REVIEW": ("APPROVED", "PARTIALLY_APPROVED", "DENIED", "EXPIRED", "CANCELLED"), "APPROVED": (), "PARTIALLY_APPROVED": (), "DENIED": (), "EXPIRED": (), "CANCELLED": ()},
    external_dependencies=("insurance-provider",),
)

FINANCIAL_CLAIM = ContractDefinition(
    contract_id="CONTRACT-034",
    domain="financial-claim",
    states=("DRAFT", "SUBMITTED", "RECEIVED", "UNDER_REVIEW", "APPROVED", "PARTIALLY_APPROVED", "DENIED", "PAID", "REJECTED", "APPEALED"),
    transitions={"DRAFT": ("SUBMITTED",), "SUBMITTED": ("RECEIVED", "REJECTED", "UNDER_REVIEW"), "RECEIVED": ("UNDER_REVIEW",), "UNDER_REVIEW": ("APPROVED", "PARTIALLY_APPROVED", "DENIED"), "APPROVED": ("PAID",), "PARTIALLY_APPROVED": ("PAID",), "DENIED": ("APPEALED",), "PAID": (), "REJECTED": (), "APPEALED": ()},
    external_dependencies=("insurance-provider",),
)

FINANCIAL_PAYMENT = ContractDefinition(
    contract_id="CONTRACT-035",
    domain="financial-payment",
    states=("INITIATED", "AUTHORIZED", "CAPTURED", "SETTLED", "FAILED", "CANCELLED", "REFUNDED", "PARTIALLY_REFUNDED", "PENDING"),
    transitions={"INITIATED": ("AUTHORIZED", "CAPTURED", "PENDING", "FAILED", "CANCELLED"), "AUTHORIZED": ("CAPTURED", "PENDING", "FAILED", "CANCELLED"), "PENDING": ("CAPTURED", "FAILED", "CANCELLED"), "CAPTURED": ("SETTLED", "PARTIALLY_REFUNDED", "REFUNDED"), "SETTLED": ("PARTIALLY_REFUNDED", "REFUNDED"), "PARTIALLY_REFUNDED": ("REFUNDED",), "FAILED": (), "CANCELLED": (), "REFUNDED": ()},
    external_dependencies=("payment-provider",),
)

FINANCIAL_REFUND = ContractDefinition(
    contract_id="CONTRACT-036",
    domain="financial-refund",
    states=("REQUESTED", "COMPLETED", "FAILED", "CANCELLED"),
    transitions={"REQUESTED": ("COMPLETED", "FAILED", "CANCELLED"), "COMPLETED": (), "FAILED": (), "CANCELLED": ()},
    external_dependencies=("payment-provider",),
)

FINANCIAL_SETTLEMENT = ContractDefinition(
    contract_id="CONTRACT-037",
    domain="financial-settlement",
    states=("PROPOSED", "APPROVED", "PAID", "CONFLICT", "CANCELLED"),
    transitions={"PROPOSED": ("APPROVED", "CONFLICT", "CANCELLED"), "APPROVED": ("PAID", "CONFLICT", "CANCELLED"), "PAID": (), "CONFLICT": (), "CANCELLED": ()},
    external_dependencies=("payment-provider", "insurance-provider"),
)

PHARMACY_CONTROLLED_POLICY = ContractDefinition(
    contract_id="CONTRACT-038",
    domain="pharmacy-controlled-policy",
    states=("NOT_CONTROLLED", "PENDING_POLICY_REVIEW", "APPROVED_BY_POLICY", "REJECTED_BY_POLICY"),
    transitions={"NOT_CONTROLLED": (), "PENDING_POLICY_REVIEW": ("APPROVED_BY_POLICY", "REJECTED_BY_POLICY"), "APPROVED_BY_POLICY": (), "REJECTED_BY_POLICY": ()},
)

PHARMACY_RECALL = ContractDefinition(
    contract_id="CONTRACT-039",
    domain="pharmacy-recall",
    states=("OPEN", "CLEARED"),
    transitions={"OPEN": ("CLEARED",), "CLEARED": ()},
)

NOTIFICATION = ContractDefinition(
    contract_id="CONTRACT-015",
    domain="notification",
    states=("PENDING", "DELIVERED", "FAILED", "ACKNOWLEDGED", "ESCALATED"),
    transitions={"PENDING": ("DELIVERED", "FAILED", "ESCALATED"), "DELIVERED": ("ACKNOWLEDGED", "ESCALATED"), "FAILED": ("PENDING", "ESCALATED"), "ACKNOWLEDGED": (), "ESCALATED": ("DELIVERED", "ACKNOWLEDGED")},
    write_safety=WriteSafetyRequirements(idempotency=False),
)

CORE_CONTRACTS: tuple[ContractDefinition, ...] = (
    APPOINTMENT, SESSION, DEVICE, PATIENT_ACCESS, CONSENT, ACCESS_HISTORY,
    DELEGATION, TASK, ENCOUNTER, CLINICAL_NOTE, LAB_ORDER, SPECIMEN,
    RESULT, CRITICAL_RESULT, NOTIFICATION, PRESCRIPTION, DISPENSE, IMAGING_ORDER,
    IMAGING_STUDY, IMAGING_REPORT, CLINICAL_RECORD, HOSPITAL_ADMISSION,
    HOSPITAL_TASK, HOSPITAL_EMAR, HOSPITAL_TRANSFER, HOSPITAL_DISCHARGE,
    EMERGENCY_INCIDENT, EMERGENCY_DISPATCH,
    LIS_ANALYZER, LIS_QC, FINANCIAL_COVERAGE, FINANCIAL_ELIGIBILITY,
    FINANCIAL_PREAUTH, FINANCIAL_CLAIM, FINANCIAL_PAYMENT, FINANCIAL_REFUND,
    FINANCIAL_SETTLEMENT, PHARMACY_CONTROLLED_POLICY, PHARMACY_RECALL,
)

CONTRACTS_BY_DOMAIN = {contract.domain: contract for contract in CORE_CONTRACTS}


def get_contract(domain: str) -> ContractDefinition:
    try:
        return CONTRACTS_BY_DOMAIN[domain]
    except KeyError as exc:
        raise KeyError(f"UNKNOWN_CLINICAL_CONTRACT:{domain}") from exc


def require_transition(domain: str, current: str, requested: str) -> None:
    contract = get_contract(domain)
    if not contract.allows(current, requested):
        raise ValueError(f"INVALID_STATE_TRANSITION:{contract.contract_id}:{current}->{requested}")
