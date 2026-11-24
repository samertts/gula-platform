"""Stable domain/operation vocabulary shared by every contract module.

Keeping this vocabulary in one dependency-free module lets the schema,
authorization and report layers agree on exactly which operations exist, without
any module importing a router or a service.
"""

from __future__ import annotations

from enum import StrEnum


class ContractDomain(StrEnum):
    """The synthetic-only domains described by this contract family."""

    PRACTITIONER = "practitioner"
    ORGANIZATION = "organization"
    FACILITY = "facility"
    MEDICAL_RECORD = "medical_record"
    ENCOUNTER = "encounter"
    DIAGNOSIS = "diagnosis"
    OBSERVATION = "observation"
    LAB_ORDER = "lab_order"
    SPECIMEN = "specimen"
    LAB_RESULT = "lab_result"
    RESULT_VERIFICATION = "result_verification"


class ContractOperation(StrEnum):
    """Every operation that must declare an authorization boundary.

    Naming follows the lowercase ``<resource>.<action>`` convention used by the
    shared event vocabulary. Each domain exposes a create and a read operation;
    no operation is implicitly public.
    """

    PRACTITIONER_CREATE = "practitioner.create"
    PRACTITIONER_READ = "practitioner.read"
    ORGANIZATION_CREATE = "organization.create"
    ORGANIZATION_READ = "organization.read"
    FACILITY_CREATE = "facility.create"
    FACILITY_READ = "facility.read"
    MEDICAL_RECORD_CREATE = "medical_record.create"
    MEDICAL_RECORD_READ = "medical_record.read"
    ENCOUNTER_CREATE = "encounter.create"
    ENCOUNTER_READ = "encounter.read"
    DIAGNOSIS_CREATE = "diagnosis.create"
    DIAGNOSIS_READ = "diagnosis.read"
    OBSERVATION_CREATE = "observation.create"
    OBSERVATION_READ = "observation.read"
    LAB_ORDER_CREATE = "lab_order.create"
    LAB_ORDER_READ = "lab_order.read"
    SPECIMEN_CREATE = "specimen.create"
    SPECIMEN_READ = "specimen.read"
    LAB_RESULT_CREATE = "lab_result.create"
    LAB_RESULT_READ = "lab_result.read"
    RESULT_VERIFICATION_CREATE = "result_verification.create"
    RESULT_VERIFICATION_READ = "result_verification.read"


#: Operations grouped by the domain they belong to (used by schema catalogue tests).
DOMAIN_OPERATIONS: dict[ContractDomain, tuple[ContractOperation, ContractOperation]] = {
    ContractDomain.PRACTITIONER: (
        ContractOperation.PRACTITIONER_CREATE,
        ContractOperation.PRACTITIONER_READ,
    ),
    ContractDomain.ORGANIZATION: (
        ContractOperation.ORGANIZATION_CREATE,
        ContractOperation.ORGANIZATION_READ,
    ),
    ContractDomain.FACILITY: (
        ContractOperation.FACILITY_CREATE,
        ContractOperation.FACILITY_READ,
    ),
    ContractDomain.MEDICAL_RECORD: (
        ContractOperation.MEDICAL_RECORD_CREATE,
        ContractOperation.MEDICAL_RECORD_READ,
    ),
    ContractDomain.ENCOUNTER: (
        ContractOperation.ENCOUNTER_CREATE,
        ContractOperation.ENCOUNTER_READ,
    ),
    ContractDomain.DIAGNOSIS: (
        ContractOperation.DIAGNOSIS_CREATE,
        ContractOperation.DIAGNOSIS_READ,
    ),
    ContractDomain.OBSERVATION: (
        ContractOperation.OBSERVATION_CREATE,
        ContractOperation.OBSERVATION_READ,
    ),
    ContractDomain.LAB_ORDER: (
        ContractOperation.LAB_ORDER_CREATE,
        ContractOperation.LAB_ORDER_READ,
    ),
    ContractDomain.SPECIMEN: (
        ContractOperation.SPECIMEN_CREATE,
        ContractOperation.SPECIMEN_READ,
    ),
    ContractDomain.LAB_RESULT: (
        ContractOperation.LAB_RESULT_CREATE,
        ContractOperation.LAB_RESULT_READ,
    ),
    ContractDomain.RESULT_VERIFICATION: (
        ContractOperation.RESULT_VERIFICATION_CREATE,
        ContractOperation.RESULT_VERIFICATION_READ,
    ),
}
