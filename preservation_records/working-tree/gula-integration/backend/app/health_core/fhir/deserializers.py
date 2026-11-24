"""Deserialise FHIR R4 JSON dicts back into validated frozen Health Core entities.

Deserialisation is deliberately strict. Missing required fields, unknown
profiles, real-looking identifiers, malformed references, wrong target types,
inconsistent lifecycle states and unsupported resource types all raise a
structured Health Core error. Nothing is silently defaulted or coerced.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from app.health_core.clinical.entities import (
    Diagnosis,
    DiagnosisStatus,
    Encounter,
    EncounterStatus,
    Facility,
    FacilityType,
    Observation,
    Organization,
    Practitioner,
    PractitionerRole,
    Severity,
)
from app.health_core.clinical.validation import (
    require_icd_code,
    require_loinc_code,
    require_unit,
)
from app.health_core.common import is_synthetic_id, reject_national_identifier
from app.health_core.fhir.errors import InvalidFhirResourceError, UnsupportedFhirResourceError
from app.health_core.fhir.support import (
    BARCODE_SYSTEM,
    ENCOUNTER_STATUS_TO_FHIR,
    EXT_AMENDMENT,
    EXT_AMENDMENT_ACTOR,
    EXT_AMENDMENT_AT,
    EXT_AMENDMENT_ID,
    EXT_AMENDMENT_NEW,
    EXT_AMENDMENT_PREVIOUS,
    EXT_AMENDMENT_REASON,
    EXT_AMENDMENT_VERSION,
    EXT_ENCOUNTER_STATUS,
    EXT_ORDER_CANCELLATION_REASON,
    EXT_ORDER_CANCELLED_AT,
    EXT_ORDER_IDEMPOTENCY,
    EXT_ORDER_STATUS,
    EXT_PATIENT_LABEL,
    EXT_PRACTITIONER_ROLE,
    EXT_RESULT_CRITICAL,
    EXT_RESULT_IDEMPOTENCY,
    EXT_RESULT_RANGE,
    EXT_RESULT_VALUE,
    EXT_SPECIMEN_REJECTION_REASON,
    EXT_SPECIMEN_STATUS,
    EXT_TENANT,
    IDENTIFIER_SYSTEM,
    ORDER_STATUS_TO_FHIR,
    SPECIMEN_STATUS_TO_FHIR,
    SPECIMEN_TYPE_TEXT,
    SUPPORTED_FHIR_RESOURCE_TYPES,
    UCUM_SYSTEM,
    FhirResource,
    entity_type_for,
    find_extension,
    profile_for,
    require_bool,
    require_dict,
    require_extension,
    require_extension_code,
    require_extension_string,
    require_finite,
    require_int,
    require_list,
    require_str,
    require_synthetic_value,
    validate_identifier,
    validate_reference,
)
from app.health_core.identity.port import PatientRef
from app.health_core.lab.models import (
    LabOrder,
    LabOrderStatus,
    LabResult,
    Priority,
    ResultAmendment,
    Specimen,
    SpecimenStatus,
)

__all__ = ["deserialize_resource"]

_OBSERVATION_CATEGORY_CODE: Final[str] = "synthetic-vital-sign"
_REPORT_CATEGORY_CODE: Final[str] = "synthetic-laboratory"


def _parse_enum[T: Enum](enumeration: type[T], value: str, *, field: str) -> T:
    """Parse a local extension or coded value without accepting fuzzy matches."""
    try:
        return enumeration(value)
    except ValueError as exc:
        raise InvalidFhirResourceError(
            f"{field} is not a permitted synthetic value",
            details={"field": field, "value": value},
        ) from exc


def _read_meta(resource: FhirResource, *, expected_type: str) -> int:
    """Validate the synthetic profile and return a positive version number."""
    meta = require_dict(resource.get("meta"), field="meta")
    profiles = require_list(meta.get("profile"), field="meta.profile")
    expected_profile = profile_for(expected_type)
    if len(profiles) != 1 or profiles[0] != expected_profile:
        raise InvalidFhirResourceError(
            "meta.profile does not match the synthetic resource profile",
            details={"expected": expected_profile, "actual": profiles},
        )
    raw_version = require_str(meta.get("versionId"), field="meta.versionId")
    if not raw_version.isdigit() or int(raw_version) < 1:
        raise InvalidFhirResourceError(
            "meta.versionId must be a positive integer string",
            details={"versionId": raw_version},
        )
    return int(raw_version)


def _read_tenant(resource: FhirResource) -> str:
    """Read and validate the synthetic tenant extension."""
    extension = require_extension(resource, EXT_TENANT, field="tenant")
    return require_synthetic_value(
        require_extension_code(extension, field="tenant"), field="tenant"
    )


def _read_patient(resource: FhirResource, *, tenant: str, field: str) -> PatientRef:
    """Rebuild a real ``PatientRef`` from a validated reference and local label.

    No identity link is invented: the reference must be ``Patient/SYN-PAT-...``,
    the label must be a bounded synthetic string, and the patient's tenant must
    equal the enclosing resource's synthetic tenant.
    """
    ref = _read_reference(resource.get(field), expected_type="Patient", field=field)
    label_extension = require_extension(resource, EXT_PATIENT_LABEL, field="patient_label")
    label = require_extension_string(label_extension, field="patient_label")
    reject_national_identifier(label, field="patient_label")
    if len(label) > 64 or not is_synthetic_id(ref):
        raise InvalidFhirResourceError(
            "patient label or reference is not a bounded synthetic value",
            details={"field": "patient_label"},
        )
    return PatientRef(ref=ref, tenant_id=tenant, label=label)


def _read_common(
    resource: FhirResource, *, expected_type: str, id_prefix: str
) -> tuple[str, str]:
    """Validate resourceType, id, profile, tenant and primary identifier."""
    actual_type = resource.get("resourceType")
    if actual_type != expected_type:
        if isinstance(actual_type, str) and actual_type in SUPPORTED_FHIR_RESOURCE_TYPES:
            raise InvalidFhirResourceError(
                "resourceType does not match the requested adapter mapping",
                details={"expected": expected_type, "actual": actual_type},
            )
        raise UnsupportedFhirResourceError(
            "resourceType is not a supported synthetic FHIR resource",
            details={
                "resourceType": actual_type if isinstance(actual_type, str) else type(actual_type).__name__
            },
        )
    _read_meta(resource, expected_type=expected_type)
    entity_id = require_synthetic_value(resource.get("id"), field="id", prefix=id_prefix)
    tenant = _read_tenant(resource)
    identifiers = require_list(resource.get("identifier"), field="identifier")
    if not identifiers:
        raise InvalidFhirResourceError(
            "identifier is required", details={"field": "identifier"}
        )
    primary = validate_identifier(
        identifiers[0],
        expected_system=IDENTIFIER_SYSTEM,
        field="identifier",
        expected_prefix=id_prefix,
    )
    if primary != entity_id:
        raise InvalidFhirResourceError(
            "identifier value does not match the resource id",
            details={"identifier": primary, "id": entity_id},
        )
    return entity_id, tenant


def _read_reference(value: object, *, expected_type: str, field: str) -> str:
    """Read one direct FHIR reference."""
    return validate_reference(value, expected_type=expected_type, field=field)


def _read_reference_list(value: object, *, expected_type: str, field: str) -> str:
    """Read exactly one reference from a FHIR reference array."""
    references = require_list(value, field=field)
    if len(references) != 1:
        raise InvalidFhirResourceError(
            f"{field} must contain exactly one reference", details={"field": field}
        )
    return _read_reference(references[0], expected_type=expected_type, field=field)


def _read_codings(value: object, *, field: str) -> list[dict[str, object]]:
    """Read the coding list of a FHIR CodeableConcept."""
    concept = require_dict(value, field=field)
    codings = require_list(concept.get("coding"), field=f"{field}.coding")
    if not codings:
        raise InvalidFhirResourceError(
            f"{field}.coding must not be empty", details={"field": field}
        )
    return [require_dict(item, field=f"{field}.coding[]") for item in codings]


def _read_coding_code(value: object, *, field: str) -> str:
    """Read the code of the first coding of a FHIR CodeableConcept."""
    return require_str(_read_codings(value, field=field)[0].get("code"), field=f"{field}.code")


def _read_single_concept_coding_code(value: object, *, field: str) -> str:
    """Read the code of the only CodeableConcept in a 1..1 concept array."""
    concepts = require_list(value, field=field)
    if len(concepts) != 1:
        raise InvalidFhirResourceError(
            f"{field} must contain exactly one concept", details={"field": field}
        )
    return _read_coding_code(concepts[0], field=f"{field}[0]")


def _read_concept_text(value: object, *, field: str) -> str:
    """Read the human-readable text of a FHIR CodeableConcept."""
    concept = require_dict(value, field=field)
    return require_str(concept.get("text"), field=f"{field}.text")


def _read_finite_text(value: object, *, field: str) -> float:
    """Parse a finite decimal number carried in a local string extension."""
    text = require_str(value, field=field)
    try:
        number = float(text)
    except ValueError as exc:
        raise InvalidFhirResourceError(
            f"{field} must be a finite number", details={"field": field}
        ) from exc
    return require_finite(number, field=field)


def _read_text_list(value: object, *, field: str) -> str:
    """Read exactly one CodeableConcept and return its text."""
    concepts = require_list(value, field=field)
    if len(concepts) != 1:
        raise InvalidFhirResourceError(
            f"{field} must contain exactly one concept", details={"field": field}
        )
    return _read_concept_text(concepts[0], field=f"{field}[0]")


def _read_nested_extension(
    extension: dict[str, object], url: str, *, field: str
) -> dict[str, object]:
    """Read one named child of a nested local extension."""
    children = require_list(extension.get("extension"), field=f"{field}.extension")
    for child in children:
        item = require_dict(child, field=f"{field}.extension[]")
        if item.get("url") == url:
            return item
    raise InvalidFhirResourceError(
        f"{field} is missing a required child extension",
        details={"field": field, "url": url},
    )


def _check_fhir_status(internal: str, actual: str, expected: str, *, field: str) -> None:
    """Ensure the FHIR status agrees with the exact synthetic state extension."""
    if expected != actual:
        raise InvalidFhirResourceError(
            f"{field} disagrees with the synthetic state extension",
            details={"field": field, "fhirStatus": actual, "syntheticStatus": internal},
        )


def deserialize_practitioner(resource: FhirResource) -> Practitioner:
    """Deserialise a synthetic ``Practitioner``."""
    entity_id, tenant = _read_common(
        resource, expected_type="Practitioner", id_prefix="SYN-PRC-"
    )
    role_extension = require_extension(resource, EXT_PRACTITIONER_ROLE, field="role")
    role = _parse_enum(
        PractitionerRole,
        require_extension_code(role_extension, field="role"),
        field="role",
    )
    qualifications = require_list(resource.get("qualification"), field="qualification")
    if len(qualifications) != 1:
        raise InvalidFhirResourceError(
            "qualification must contain exactly one entry",
            details={"field": "qualification"},
        )
    qualification = _read_concept_text(
        require_dict(qualifications[0], field="qualification[0]").get("code"),
        field="qualification.code",
    )
    return Practitioner(
        practitioner_id=entity_id,
        tenant_id=tenant,
        role=role,
        qualification=qualification,
        active=require_bool(resource.get("active"), field="active"),
    )


def deserialize_organization(resource: FhirResource) -> Organization:
    """Deserialise a synthetic ``Organization``."""
    entity_id, tenant = _read_common(
        resource, expected_type="Organization", id_prefix="SYN-ORG-"
    )
    return Organization(
        organization_id=entity_id,
        tenant_id=tenant,
        label=require_str(resource.get("name"), field="name", max_length=120),
        active=require_bool(resource.get("active"), field="active"),
    )


def deserialize_facility(resource: FhirResource) -> Facility:
    """Deserialise a synthetic ``Location`` into its internal ``Facility``."""
    entity_id, tenant = _read_common(resource, expected_type="Location", id_prefix="SYN-FAC-")
    if resource.get("mode") != "instance":
        raise InvalidFhirResourceError(
            "Location.mode must be 'instance' for a synthetic facility",
            details={"mode": resource.get("mode")},
        )
    return Facility(
        facility_id=entity_id,
        tenant_id=tenant,
        organization_id=_read_reference(
            resource.get("managingOrganization"),
            expected_type="Organization",
            field="managingOrganization",
        ),
        label=require_str(resource.get("name"), field="name", max_length=120),
        facility_type=_parse_enum(
            FacilityType, _read_text_list(resource.get("type"), field="type"), field="facility_type"
        ),
        active=require_bool(resource.get("active"), field="active"),
    )


def deserialize_encounter(resource: FhirResource) -> Encounter:
    """Deserialise a synthetic ``Encounter``."""
    entity_id, tenant = _read_common(resource, expected_type="Encounter", id_prefix="SYN-ENC-")
    version = _read_meta(resource, expected_type="Encounter")
    state_extension = require_extension(resource, EXT_ENCOUNTER_STATUS, field="status")
    internal_status = _parse_enum(
        EncounterStatus,
        require_extension_code(state_extension, field="status"),
        field="status",
    )
    _check_fhir_status(
        internal_status.value,
        require_str(resource.get("status"), field="status"),
        ENCOUNTER_STATUS_TO_FHIR[internal_status],
        field="status",
    )
    participant = require_list(resource.get("participant"), field="participant")
    if len(participant) != 1:
        raise InvalidFhirResourceError(
            "participant must contain exactly one practitioner",
            details={"field": "participant"},
        )
    practitioner = _read_reference(
        require_dict(participant[0], field="participant[0]").get("individual"),
        expected_type="Practitioner",
        field="participant.individual",
    )
    locations = require_list(resource.get("location"), field="location")
    if len(locations) != 1:
        raise InvalidFhirResourceError(
            "location must contain exactly one facility",
            details={"field": "location"},
        )
    facility_id = _read_reference(
        require_dict(locations[0], field="location[0]").get("location"),
        expected_type="Location",
        field="location.location",
    )
    period = require_dict(resource.get("period"), field="period")
    return Encounter(
        encounter_id=entity_id,
        tenant_id=tenant,
        patient_ref=_read_reference(resource.get("subject"), expected_type="Patient", field="subject"),
        practitioner_id=practitioner,
        facility_id=facility_id,
        status=internal_status,
        reason=_read_text_list(resource.get("reasonCode"), field="reasonCode"),
        version=version,
        created_at=require_str(period.get("start"), field="period.start"),
    )


def deserialize_diagnosis(resource: FhirResource) -> Diagnosis:
    """Deserialise a synthetic ``Condition``."""
    entity_id, tenant = _read_common(resource, expected_type="Condition", id_prefix="SYN-DIA-")
    version = _read_meta(resource, expected_type="Condition")
    status = _parse_enum(
        DiagnosisStatus,
        _read_coding_code(resource.get("clinicalStatus"), field="clinicalStatus"),
        field="status",
    )
    severity = _parse_enum(
        Severity, _read_concept_text(resource.get("severity"), field="severity"), field="severity"
    )
    code = require_icd_code(
        _read_coding_code(resource.get("code"), field="code"), field="code"
    )
    resolved_at = resource.get("abatementDateTime")
    if resolved_at is not None and not isinstance(resolved_at, str):
        raise InvalidFhirResourceError(
            "abatementDateTime must be a string when present",
            details={"field": "abatementDateTime"},
        )
    return Diagnosis(
        diagnosis_id=entity_id,
        tenant_id=tenant,
        patient_ref=_read_reference(resource.get("subject"), expected_type="Patient", field="subject"),
        encounter_id=_read_reference(
            resource.get("encounter"), expected_type="Encounter", field="encounter"
        ),
        code=code,
        description=_read_concept_text(resource.get("code"), field="code"),
        severity=severity,
        status=status,
        asserted_at=require_str(resource.get("recordedDate"), field="recordedDate"),
        resolved_at=resolved_at,
        version=version,
    )


def deserialize_observation(resource: FhirResource) -> Observation:
    """Deserialise a synthetic ``Observation``."""
    entity_id, tenant = _read_common(resource, expected_type="Observation", id_prefix="SYN-OBS-")
    if resource.get("status") != "final":
        raise InvalidFhirResourceError(
            "synthetic Observation.status must be 'final'",
            details={"status": resource.get("status")},
        )
    if (
        _read_single_concept_coding_code(resource.get("category"), field="category")
        != _OBSERVATION_CATEGORY_CODE
    ):
        raise InvalidFhirResourceError(
            "Observation.category is not the synthetic vital-sign category",
            details={"field": "category"},
        )
    codings = _read_codings(resource.get("code"), field="code")
    if len(codings) != 1:
        raise InvalidFhirResourceError(
            "Observation.code must carry exactly one coding",
            details={"field": "code"},
        )
    code = require_loinc_code(require_str(codings[0].get("code"), field="code.code"), field="code")
    display = require_str(codings[0].get("display"), field="code.display", max_length=200)
    quantity = require_dict(resource.get("valueQuantity"), field="valueQuantity")
    if quantity.get("system") != UCUM_SYSTEM:
        raise InvalidFhirResourceError(
            "valueQuantity.system must be the UCUM system",
            details={"field": "valueQuantity.system"},
        )
    unit = require_str(quantity.get("unit"), field="valueQuantity.unit", max_length=24)
    if quantity.get("code") != unit:
        raise InvalidFhirResourceError(
            "valueQuantity.code disagrees with valueQuantity.unit",
            details={"field": "valueQuantity.code"},
        )
    return Observation(
        observation_id=entity_id,
        tenant_id=tenant,
        patient_ref=_read_reference(resource.get("subject"), expected_type="Patient", field="subject"),
        encounter_id=_read_reference(
            resource.get("encounter"), expected_type="Encounter", field="encounter"
        ),
        code=code,
        display=display,
        value=require_finite(quantity.get("value"), field="valueQuantity.value"),
        unit=require_unit(code, unit),
        recorded_at=require_str(resource.get("effectiveDateTime"), field="effectiveDateTime"),
    )


def deserialize_order(resource: FhirResource) -> LabOrder:
    """Deserialise a synthetic ``ServiceRequest`` into a ``LabOrder``."""
    entity_id, tenant = _read_common(
        resource, expected_type="ServiceRequest", id_prefix="SYN-ORD-"
    )
    state_extension = require_extension(resource, EXT_ORDER_STATUS, field="status")
    internal_status = _parse_enum(
        LabOrderStatus,
        require_extension_code(state_extension, field="status"),
        field="status",
    )
    _check_fhir_status(
        internal_status.value,
        require_str(resource.get("status"), field="status"),
        ORDER_STATUS_TO_FHIR[internal_status],
        field="status",
    )
    if resource.get("intent") != "order":
        raise InvalidFhirResourceError(
            "ServiceRequest.intent must be 'order'", details={"intent": resource.get("intent")}
        )
    codes = tuple(
        require_str(item.get("code"), field="code.coding[].code")
        for item in _read_codings(resource.get("code"), field="code")
    )
    if not codes:
        raise InvalidFhirResourceError("code.coding must not be empty", details={"field": "code"})
    key_extension = require_extension(resource, EXT_ORDER_IDEMPOTENCY, field="idempotency_key")
    idempotency_key = require_synthetic_value(
        require_extension_string(key_extension, field="idempotency_key"),
        field="idempotency_key",
    )
    cancelled_at_extension = find_extension(resource, EXT_ORDER_CANCELLED_AT)
    reason_extension = find_extension(resource, EXT_ORDER_CANCELLATION_REASON)
    cancelled_at = (
        require_str(
            cancelled_at_extension.get("valueDateTime"), field="cancelled_at"
        )
        if cancelled_at_extension is not None
        else None
    )
    cancellation_reason = (
        require_extension_string(reason_extension, field="cancellation_reason")
        if reason_extension is not None
        else None
    )
    if internal_status is not LabOrderStatus.CANCELLED and (
        cancelled_at is not None or cancellation_reason is not None
    ):
        raise InvalidFhirResourceError(
            "cancellation details require a cancelled synthetic order",
            details={"field": "status"},
        )
    return LabOrder(
        order_id=entity_id,
        idempotency_key=idempotency_key,
        patient=_read_patient(resource, tenant=tenant, field="subject"),
        tenant_id=tenant,
        test_codes=codes,
        priority=_parse_enum(
            Priority, require_str(resource.get("priority"), field="priority"), field="priority"
        ),
        status=internal_status,
        created_at=require_str(resource.get("occurrenceDateTime"), field="occurrenceDateTime"),
        cancelled_at=cancelled_at,
        cancellation_reason=cancellation_reason,
    )


def deserialize_specimen(resource: FhirResource) -> Specimen:
    """Deserialise a synthetic ``Specimen``."""
    entity_id, tenant = _read_common(resource, expected_type="Specimen", id_prefix="SYN-SPC-")
    identifiers = require_list(resource.get("identifier"), field="identifier")
    if len(identifiers) != 2:
        raise InvalidFhirResourceError(
            "Specimen.identifier must carry the id and the barcode",
            details={"field": "identifier"},
        )
    barcode = validate_identifier(
        identifiers[1],
        expected_system=BARCODE_SYSTEM,
        field="barcode",
        expected_prefix="SYN-BAR-",
    )
    state_extension = require_extension(resource, EXT_SPECIMEN_STATUS, field="status")
    internal_status = _parse_enum(
        SpecimenStatus,
        require_extension_code(state_extension, field="status"),
        field="status",
    )
    _check_fhir_status(
        internal_status.value,
        require_str(resource.get("status"), field="status"),
        SPECIMEN_STATUS_TO_FHIR[internal_status],
        field="status",
    )
    if _read_concept_text(resource.get("type"), field="type") != SPECIMEN_TYPE_TEXT:
        raise InvalidFhirResourceError(
            "Specimen.type is not the synthetic specimen type",
            details={"field": "type"},
        )
    rejection_extension = find_extension(resource, EXT_SPECIMEN_REJECTION_REASON)
    rejection_reason = (
        require_extension_string(rejection_extension, field="rejection_reason")
        if rejection_extension is not None
        else None
    )
    if rejection_reason is not None and internal_status is not SpecimenStatus.REJECTED:
        raise InvalidFhirResourceError(
            "rejection reason requires a rejected synthetic specimen",
            details={"field": "status"},
        )
    return Specimen(
        specimen_id=entity_id,
        barcode=barcode,
        order_id=_read_reference_list(
            resource.get("request"), expected_type="ServiceRequest", field="request"
        ),
        tenant_id=tenant,
        patient=_read_patient(resource, tenant=tenant, field="subject"),
        status=internal_status,
        registered_at=require_str(resource.get("receivedTime"), field="receivedTime"),
        rejection_reason=rejection_reason,
    )


def deserialize_result(resource: FhirResource) -> LabResult:
    """Deserialise a synthetic ``DiagnosticReport`` into a ``LabResult``."""
    entity_id, tenant = _read_common(
        resource, expected_type="DiagnosticReport", id_prefix="SYN-RES-"
    )
    version = _read_meta(resource, expected_type="DiagnosticReport")
    expected_status = "corrected" if version > 1 else "final"
    if resource.get("status") != expected_status:
        raise InvalidFhirResourceError(
            "DiagnosticReport.status disagrees with the synthetic version",
            details={"expected": expected_status, "actual": resource.get("status")},
        )
    if (
        _read_single_concept_coding_code(resource.get("category"), field="category")
        != _REPORT_CATEGORY_CODE
    ):
        raise InvalidFhirResourceError(
            "DiagnosticReport.category is not the synthetic laboratory category",
            details={"field": "category"},
        )
    test_code = _read_coding_code(resource.get("code"), field="code")
    effective = require_str(resource.get("effectiveDateTime"), field="effectiveDateTime")
    issued = require_str(resource.get("issued"), field="issued")
    if effective != issued:
        raise InvalidFhirResourceError(
            "effectiveDateTime and issued must agree for a synthetic result",
            details={"field": "issued"},
        )
    if require_list(resource.get("result"), field="result"):
        raise InvalidFhirResourceError(
            "synthetic results do not emit separate Observation references",
            details={"field": "result"},
        )
    value_extension = require_extension(resource, EXT_RESULT_VALUE, field="value")
    value_quantity = require_dict(
        value_extension.get("valueQuantity"), field="value.valueQuantity"
    )
    value = require_finite(value_quantity.get("value"), field="value.valueQuantity.value")
    range_extension = require_extension(resource, EXT_RESULT_RANGE, field="reference_range")
    range_text = require_extension_string(range_extension, field="reference_range")
    bounds = range_text.split("|")
    if len(bounds) != 2:
        raise InvalidFhirResourceError(
            "reference range must carry exactly two bounds",
            details={"field": "reference_range"},
        )
    reference_low = _read_finite_text(bounds[0], field="reference_low")
    reference_high = _read_finite_text(bounds[1], field="reference_high")
    if reference_low >= reference_high:
        raise InvalidFhirResourceError(
            "reference_low must be smaller than reference_high",
            details={"field": "reference_range"},
        )
    critical_extension = require_extension(resource, EXT_RESULT_CRITICAL, field="critical_flag")
    key_extension = require_extension(resource, EXT_RESULT_IDEMPOTENCY, field="idempotency_key")
    amendments = tuple(
        _read_amendment(item, result_id=entity_id, tenant_id=tenant)
        for item in require_list(resource.get("extension"), field="extension")
        if isinstance(item, dict) and item.get("url") == EXT_AMENDMENT
    )
    return LabResult(
        result_id=entity_id,
        idempotency_key=require_synthetic_value(
            require_extension_string(key_extension, field="idempotency_key"),
            field="idempotency_key",
        ),
        order_id=_read_reference_list(
            resource.get("basedOn"), expected_type="ServiceRequest", field="basedOn"
        ),
        specimen_id=_read_reference_list(
            resource.get("specimen"), expected_type="Specimen", field="specimen"
        ),
        patient=_read_patient(resource, tenant=tenant, field="subject"),
        tenant_id=tenant,
        test_code=test_code,
        value=value,
        unit=_read_result_unit(resource),
        reference_low=reference_low,
        reference_high=reference_high,
        critical_flag=require_bool(
            critical_extension.get("valueBoolean"), field="critical_flag.valueBoolean"
        ),
        recorded_at=effective,
        version=version,
        amendments=amendments,
    )


def _read_result_unit(resource: FhirResource) -> str:
    """Read the value unit from a synthetic result extension."""
    value_extension = require_extension(resource, EXT_RESULT_VALUE, field="value")
    quantity = require_dict(value_extension.get("valueQuantity"), field="value.valueQuantity")
    if quantity.get("system") != UCUM_SYSTEM or quantity.get("code") != quantity.get("unit"):
        raise InvalidFhirResourceError(
            "result valueQuantity must use a consistent UCUM-style unit",
            details={"field": "value.valueQuantity"},
        )
    return require_str(quantity.get("unit"), field="value.valueQuantity.unit", max_length=24)


def _read_amendment(
    value: object, *, result_id: str, tenant_id: str
) -> ResultAmendment:
    """Deserialise one nested amendment extension into its frozen record."""
    extension = require_dict(value, field="amendment")
    amendment_id = require_str(
        _read_nested_extension(extension, EXT_AMENDMENT_ID, field="amendment.id").get(
            "valueString"
        ),
        field="amendment.id",
    )
    previous_value = require_finite(
        _read_nested_extension(extension, EXT_AMENDMENT_PREVIOUS, field="amendment.previous").get(
            "valueDecimal"
        ),
        field="amendment.previous",
    )
    new_value = require_finite(
        _read_nested_extension(extension, EXT_AMENDMENT_NEW, field="amendment.new").get(
            "valueDecimal"
        ),
        field="amendment.new",
    )
    reason = require_str(
        _read_nested_extension(extension, EXT_AMENDMENT_REASON, field="amendment.reason").get(
            "valueString"
        ),
        field="amendment.reason",
    )
    actor_id = require_synthetic_value(
        _read_nested_extension(extension, EXT_AMENDMENT_ACTOR, field="amendment.actor").get(
            "valueString"
        ),
        field="amendment.actor",
    )
    occurred_at = require_str(
        _read_nested_extension(extension, EXT_AMENDMENT_AT, field="amendment.at").get(
            "valueDateTime"
        ),
        field="amendment.at",
    )
    version = require_int(
        _read_nested_extension(extension, EXT_AMENDMENT_VERSION, field="amendment.version").get(
            "valueInteger"
        ),
        field="amendment.version",
    )
    return ResultAmendment(
        amendment_id=amendment_id,
        result_id=result_id,
        tenant_id=tenant_id,
        previous_value=previous_value,
        new_value=new_value,
        reason=reason,
        actor_id=actor_id,
        occurred_at=occurred_at,
        version=version,
    )


def deserialize_resource(resource: FhirResource) -> object:
    """Deserialise one supported FHIR R4 resource into a frozen entity."""
    if not isinstance(resource, dict):
        raise InvalidFhirResourceError(
            "resource must be a JSON object", details={"field": "resource"}
        )
    resource_type = resource.get("resourceType")
    entity_type_for(resource_type)
    if not isinstance(resource_type, str):
        raise InvalidFhirResourceError(
            "resourceType must be a string", details={"field": "resourceType"}
        )
    if resource_type == "Practitioner":
        return deserialize_practitioner(resource)
    if resource_type == "Organization":
        return deserialize_organization(resource)
    if resource_type == "Location":
        return deserialize_facility(resource)
    if resource_type == "Encounter":
        return deserialize_encounter(resource)
    if resource_type == "Condition":
        return deserialize_diagnosis(resource)
    if resource_type == "Observation":
        return deserialize_observation(resource)
    if resource_type == "ServiceRequest":
        return deserialize_order(resource)
    if resource_type == "Specimen":
        return deserialize_specimen(resource)
    if resource_type == "DiagnosticReport":
        return deserialize_result(resource)
    raise UnsupportedFhirResourceError(
        "resource type has no deserialiser", details={"resourceType": resource_type}
    )
