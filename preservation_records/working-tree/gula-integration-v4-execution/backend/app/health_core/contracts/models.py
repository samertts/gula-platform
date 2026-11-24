"""Versioned request/response schemas for synthetic Health Core domains.

CONTRACTS ONLY: this module defines Pydantic models, not FastAPI routers, routes
or handlers. Nothing here is exposed by the running application.

Every identifier is an opaque ``SYN-`` reference validated through the shared
helpers in ``app.health_core.common`` (imported, never redefined). Arabic and
other unicode text is accepted and preserved in the free-text fields; no real
patient data or identifier can be represented.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from app.health_core.common import HealthCoreError, is_synthetic_id, reject_national_identifier
from app.health_core.contracts.catalogue import ContractDomain
from app.health_core.contracts.version import CONTRACT_STATUS, HEALTH_CORE_CONTRACT_VERSION


def _validate_synthetic_ref(value: str) -> str:
    """Validate through shared helpers, surfacing a Pydantic-friendly error.

    The shared ``reject_national_identifier`` raises a ``HealthCoreError`` (a
    plain ``Exception``), which Pydantic does not convert into a validation
    error, so it is translated to ``ValueError`` at this boundary.
    """
    try:
        reject_national_identifier(value, field="reference")
    except HealthCoreError as exc:
        raise ValueError(str(exc)) from exc
    if not is_synthetic_id(value):
        raise ValueError("reference must be a SYN- prefixed synthetic reference")
    return value


SyntheticRef = Annotated[
    str,
    StringConstraints(min_length=9, max_length=96),
    AfterValidator(_validate_synthetic_ref),
]
"""An opaque, locally generated ``SYN-`` reference (never a real identifier)."""

ArabicSafeText = Annotated[str, StringConstraints(min_length=1, max_length=512)]
"""Unicode-safe free text; Arabic (including diacritics) is accepted verbatim."""

CodeValue = Annotated[str, StringConstraints(min_length=1, max_length=64)]
"""A short machine code (e.g. a synthetic test or role code)."""


class ContractModel(BaseModel):
    """Strict base for every contract model: explicit config, immutable, safe."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        use_enum_values=False,
    )


class TenantScopedRequest(ContractModel):
    """Base request carrying the mandatory synthetic tenant scope."""

    tenant_id: SyntheticRef = Field(
        ...,
        description="Opaque SYN- tenant reference; never a real organisation key.",
    )


class SyntheticAggregateResponse(ContractModel):
    """Base response carrying the opaque aggregate reference and contract tag."""

    ref: SyntheticRef = Field(..., description="Opaque SYN- reference to the aggregate.")
    tenant_id: SyntheticRef = Field(..., description="Opaque SYN- tenant reference.")
    contract_version: str = Field(
        default=HEALTH_CORE_CONTRACT_VERSION,
        description="Version of this contract family that produced the payload.",
    )
    contract_status: str = Field(
        default=CONTRACT_STATUS,
        description="Classification of the contract family (local synthetic only).",
    )


# --- Practitioner -----------------------------------------------------------


class PractitionerCreateRequest(TenantScopedRequest):
    display_name: ArabicSafeText = Field(..., description="Synthetic display label.")
    role_code: CodeValue = Field(..., description="Synthetic role code.")
    active: bool = Field(default=True, description="Whether the synthetic practitioner is active.")


class PractitionerResponse(SyntheticAggregateResponse):
    display_name: ArabicSafeText = Field(...)
    role_code: CodeValue = Field(...)
    active: bool = Field(...)


# --- Organization -----------------------------------------------------------


class OrganizationCreateRequest(TenantScopedRequest):
    name: ArabicSafeText = Field(..., description="Synthetic organisation label.")
    organization_type_code: CodeValue = Field(...)


class OrganizationResponse(SyntheticAggregateResponse):
    name: ArabicSafeText = Field(...)
    organization_type_code: CodeValue = Field(...)


# --- Facility ---------------------------------------------------------------


class FacilityCreateRequest(TenantScopedRequest):
    name: ArabicSafeText = Field(...)
    organization_ref: SyntheticRef = Field(...)
    facility_type_code: CodeValue = Field(...)


class FacilityResponse(SyntheticAggregateResponse):
    name: ArabicSafeText = Field(...)
    organization_ref: SyntheticRef = Field(...)
    facility_type_code: CodeValue = Field(...)


# --- Medical Record ---------------------------------------------------------


class MedicalRecordCreateRequest(TenantScopedRequest):
    patient_ref: SyntheticRef = Field(...)
    title: ArabicSafeText = Field(...)
    notes: ArabicSafeText | None = Field(default=None, description="Optional synthetic notes.")


class MedicalRecordResponse(SyntheticAggregateResponse):
    patient_ref: SyntheticRef = Field(...)
    title: ArabicSafeText = Field(...)
    notes: ArabicSafeText | None = Field(default=None)


# --- Encounter --------------------------------------------------------------


class EncounterCreateRequest(TenantScopedRequest):
    patient_ref: SyntheticRef = Field(...)
    practitioner_ref: SyntheticRef = Field(...)
    facility_ref: SyntheticRef = Field(...)
    reason: ArabicSafeText = Field(...)


class EncounterResponse(SyntheticAggregateResponse):
    patient_ref: SyntheticRef = Field(...)
    practitioner_ref: SyntheticRef = Field(...)
    facility_ref: SyntheticRef = Field(...)
    reason: ArabicSafeText = Field(...)
    status: CodeValue = Field(default="planned", description="Synthetic encounter status.")


# --- Diagnosis --------------------------------------------------------------


class DiagnosisCreateRequest(TenantScopedRequest):
    encounter_ref: SyntheticRef = Field(...)
    code_system: CodeValue = Field(...)
    code: CodeValue = Field(...)
    display: ArabicSafeText = Field(...)


class DiagnosisResponse(SyntheticAggregateResponse):
    encounter_ref: SyntheticRef = Field(...)
    code_system: CodeValue = Field(...)
    code: CodeValue = Field(...)
    display: ArabicSafeText = Field(...)


# --- Observation ------------------------------------------------------------


class ObservationCreateRequest(TenantScopedRequest):
    patient_ref: SyntheticRef = Field(...)
    encounter_ref: SyntheticRef | None = Field(default=None)
    code: CodeValue = Field(...)
    value_text: ArabicSafeText = Field(...)
    unit: CodeValue | None = Field(default=None)


class ObservationResponse(SyntheticAggregateResponse):
    patient_ref: SyntheticRef = Field(...)
    encounter_ref: SyntheticRef | None = Field(default=None)
    code: CodeValue = Field(...)
    value_text: ArabicSafeText = Field(...)
    unit: CodeValue | None = Field(default=None)


# --- Lab Order --------------------------------------------------------------


class LabOrderCreateRequest(TenantScopedRequest):
    patient_ref: SyntheticRef = Field(...)
    practitioner_ref: SyntheticRef = Field(...)
    facility_ref: SyntheticRef = Field(...)
    test_code: CodeValue = Field(...)


class LabOrderResponse(SyntheticAggregateResponse):
    patient_ref: SyntheticRef = Field(...)
    practitioner_ref: SyntheticRef = Field(...)
    facility_ref: SyntheticRef = Field(...)
    test_code: CodeValue = Field(...)
    status: CodeValue = Field(default="placed", description="Synthetic order status.")


# --- Specimen ---------------------------------------------------------------


class SpecimenCreateRequest(TenantScopedRequest):
    order_ref: SyntheticRef = Field(...)
    specimen_type_code: CodeValue = Field(...)
    collection_site: ArabicSafeText | None = Field(default=None)


class SpecimenResponse(SyntheticAggregateResponse):
    order_ref: SyntheticRef = Field(...)
    specimen_type_code: CodeValue = Field(...)
    collection_site: ArabicSafeText | None = Field(default=None)
    status: CodeValue = Field(default="registered", description="Synthetic specimen status.")


# --- Lab Result -------------------------------------------------------------


class LabResultCreateRequest(TenantScopedRequest):
    order_ref: SyntheticRef = Field(...)
    specimen_ref: SyntheticRef = Field(...)
    test_code: CodeValue = Field(...)
    value_text: ArabicSafeText = Field(...)
    unit: CodeValue | None = Field(default=None)
    abnormal_flag: bool = Field(default=False)


class LabResultResponse(SyntheticAggregateResponse):
    order_ref: SyntheticRef = Field(...)
    specimen_ref: SyntheticRef = Field(...)
    test_code: CodeValue = Field(...)
    value_text: ArabicSafeText = Field(...)
    unit: CodeValue | None = Field(default=None)
    abnormal_flag: bool = Field(default=False)
    status: CodeValue = Field(default="preliminary", description="Synthetic result status.")


# --- Result Verification ----------------------------------------------------


class ResultVerificationCreateRequest(TenantScopedRequest):
    result_ref: SyntheticRef = Field(...)
    verifier_ref: SyntheticRef = Field(...)
    verification_note: ArabicSafeText | None = Field(default=None)


class ResultVerificationResponse(SyntheticAggregateResponse):
    result_ref: SyntheticRef = Field(...)
    verifier_ref: SyntheticRef = Field(...)
    verified_at: str = Field(..., description="UTC ISO-8601 timestamp of synthetic verification.")
    verification_note: ArabicSafeText | None = Field(default=None)


#: One (request, response) schema pair per contract domain.
DOMAIN_SCHEMAS: dict[
    ContractDomain, tuple[type[TenantScopedRequest], type[SyntheticAggregateResponse]]
] = {
    ContractDomain.PRACTITIONER: (PractitionerCreateRequest, PractitionerResponse),
    ContractDomain.ORGANIZATION: (OrganizationCreateRequest, OrganizationResponse),
    ContractDomain.FACILITY: (FacilityCreateRequest, FacilityResponse),
    ContractDomain.MEDICAL_RECORD: (MedicalRecordCreateRequest, MedicalRecordResponse),
    ContractDomain.ENCOUNTER: (EncounterCreateRequest, EncounterResponse),
    ContractDomain.DIAGNOSIS: (DiagnosisCreateRequest, DiagnosisResponse),
    ContractDomain.OBSERVATION: (ObservationCreateRequest, ObservationResponse),
    ContractDomain.LAB_ORDER: (LabOrderCreateRequest, LabOrderResponse),
    ContractDomain.SPECIMEN: (SpecimenCreateRequest, SpecimenResponse),
    ContractDomain.LAB_RESULT: (LabResultCreateRequest, LabResultResponse),
    ContractDomain.RESULT_VERIFICATION: (
        ResultVerificationCreateRequest,
        ResultVerificationResponse,
    ),
}
