"""Serialise frozen Health Core entities into small, valid FHIR R4 resources.

Fields that FHIR R4 models natively are mapped to their standard elements.
Synthetic-only facts (tenant, exact internal lifecycle state, idempotency keys,
corrections) are carried in explicitly named local extensions and validated on
the way back in. No resource, name, identity link or clinical meaning is
invented to fill a FHIR field.
"""

from __future__ import annotations

from typing import Final

from app.health_core.clinical.entities import (
    Diagnosis,
    Encounter,
    Facility,
    Observation,
    Organization,
    Practitioner,
)
from app.health_core.fhir.errors import InvalidFhirResourceError
from app.health_core.fhir.support import (
    BARCODE_SYSTEM,
    CODE_SYSTEM,
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
    ORDER_STATUS_TO_FHIR,
    SPECIMEN_STATUS_TO_FHIR,
    SPECIMEN_TYPE_TEXT,
    TEST_CODE_SYSTEM,
    UCUM_SYSTEM,
    FhirResource,
    extension_boolean,
    extension_code,
    extension_datetime,
    extension_decimal,
    extension_integer,
    extension_nested,
    extension_quantity,
    extension_string,
    make_identifier,
    make_reference,
    profile_for,
    require_synthetic_value,
    resource_type_for,
)
from app.health_core.lab.models import LabOrder, LabResult, Specimen

__all__ = ["serialize_entity"]

_ENCOUNTER_CLASS: Final[dict[str, object]] = {
    "system": CODE_SYSTEM,
    "code": "synthetic-encounter",
    "display": "Synthetic encounter",
}
_OBSERVATION_CATEGORY: Final[list[dict[str, object]]] = [
    {"coding": [{"system": CODE_SYSTEM, "code": "synthetic-vital-sign"}]}
]
_REPORT_CATEGORY: Final[list[dict[str, object]]] = [
    {"coding": [{"system": CODE_SYSTEM, "code": "synthetic-laboratory"}]}
]


def _base(
    resource_type: str,
    entity_id: str,
    tenant_id: str,
    *,
    version: int,
    id_prefix: str,
    extras: list[dict[str, object]] | None = None,
) -> FhirResource:
    """Build the common, validated spine of every supported resource."""
    if version < 1:
        raise InvalidFhirResourceError(
            "synthetic version must be a positive integer", details={"version": version}
        )
    clean_id = require_synthetic_value(entity_id, field="id", prefix=id_prefix)
    clean_tenant = require_synthetic_value(tenant_id, field="tenant")
    extensions: list[dict[str, object]] = [extension_code(EXT_TENANT, clean_tenant)]
    if extras:
        extensions.extend(extras)
    return {
        "resourceType": resource_type,
        "id": clean_id,
        "meta": {
            "profile": [profile_for(resource_type)],
            "versionId": str(version),
        },
        "identifier": [
            make_identifier(clean_id, field="identifier", expected_prefix=id_prefix)
        ],
        "extension": extensions,
    }


def serialize_practitioner(entity: Practitioner) -> FhirResource:
    """Map a synthetic practitioner; role is a local extension, not a name."""
    resource = _base(
        "Practitioner",
        entity.practitioner_id,
        entity.tenant_id,
        version=1,
        id_prefix="SYN-PRC-",
        extras=[extension_code(EXT_PRACTITIONER_ROLE, entity.role.value)],
    )
    resource["active"] = bool(entity.active)
    resource["qualification"] = [{"code": {"text": entity.qualification}}]
    return resource


def serialize_organization(entity: Organization) -> FhirResource:
    """Map a synthetic organisation (synthetic label, no real registry data)."""
    resource = _base(
        "Organization",
        entity.organization_id,
        entity.tenant_id,
        version=1,
        id_prefix="SYN-ORG-",
    )
    resource["active"] = bool(entity.active)
    resource["name"] = entity.label
    return resource


def serialize_facility(entity: Facility) -> FhirResource:
    """Map a synthetic facility to FHIR ``Location`` within the same tenant."""
    resource = _base(
        "Location",
        entity.facility_id,
        entity.tenant_id,
        version=1,
        id_prefix="SYN-FAC-",
    )
    resource["active"] = bool(entity.active)
    resource["name"] = entity.label
    resource["mode"] = "instance"
    resource["type"] = [{"text": entity.facility_type.value}]
    resource["managingOrganization"] = make_reference(
        "Organization", entity.organization_id, field="managingOrganization"
    )
    return resource


def serialize_encounter(entity: Encounter) -> FhirResource:
    """Map a synthetic encounter, preserving the exact lifecycle state."""
    resource = _base(
        "Encounter",
        entity.encounter_id,
        entity.tenant_id,
        version=entity.version,
        id_prefix="SYN-ENC-",
        extras=[
            extension_code(EXT_ENCOUNTER_STATUS, entity.status.value),
        ],
    )
    resource["status"] = ENCOUNTER_STATUS_TO_FHIR[entity.status]
    resource["class"] = dict(_ENCOUNTER_CLASS)
    resource["subject"] = make_reference("Patient", entity.patient_ref, field="subject")
    resource["participant"] = [
        {"individual": make_reference("Practitioner", entity.practitioner_id, field="participant")}
    ]
    resource["location"] = [
        {"location": make_reference("Location", entity.facility_id, field="location")}
    ]
    resource["reasonCode"] = [{"text": entity.reason}]
    resource["period"] = {"start": entity.created_at}
    return resource


def serialize_diagnosis(entity: Diagnosis) -> FhirResource:
    """Map a synthetic problem to FHIR ``Condition`` with structural codes."""
    extras: list[dict[str, object]] = []
    resource = _base(
        "Condition",
        entity.diagnosis_id,
        entity.tenant_id,
        version=entity.version,
        id_prefix="SYN-DIA-",
        extras=extras,
    )
    resource["clinicalStatus"] = {
        "coding": [{"system": CODE_SYSTEM, "code": entity.status.value}]
    }
    resource["severity"] = {"text": entity.severity.value}
    resource["code"] = {
        "coding": [{"system": CODE_SYSTEM, "code": entity.code}],
        "text": entity.description,
    }
    resource["subject"] = make_reference("Patient", entity.patient_ref, field="subject")
    resource["encounter"] = make_reference("Encounter", entity.encounter_id, field="encounter")
    resource["recordedDate"] = entity.asserted_at
    if entity.resolved_at is not None:
        resource["abatementDateTime"] = entity.resolved_at
    return resource


def serialize_observation(entity: Observation) -> FhirResource:
    """Map a synthetic coded observation with its UCUM-style quantity."""
    resource = _base(
        "Observation",
        entity.observation_id,
        entity.tenant_id,
        version=1,
        id_prefix="SYN-OBS-",
    )
    resource["status"] = "final"
    resource["category"] = [dict(item) for item in _OBSERVATION_CATEGORY]
    resource["code"] = {
        "coding": [{"system": CODE_SYSTEM, "code": entity.code, "display": entity.display}],
        "text": entity.display,
    }
    resource["subject"] = make_reference("Patient", entity.patient_ref, field="subject")
    resource["encounter"] = make_reference("Encounter", entity.encounter_id, field="encounter")
    resource["effectiveDateTime"] = entity.recorded_at
    resource["valueQuantity"] = {
        "value": float(entity.value),
        "unit": entity.unit,
        "system": UCUM_SYSTEM,
        "code": entity.unit,
    }
    return resource


def serialize_order(entity: LabOrder) -> FhirResource:
    """Map a synthetic lab order to ``ServiceRequest`` with local extras."""
    extras: list[dict[str, object]] = [
        extension_code(EXT_ORDER_STATUS, entity.status.value),
        extension_string(EXT_ORDER_IDEMPOTENCY, entity.idempotency_key),
        extension_string(EXT_PATIENT_LABEL, entity.patient.label),
    ]
    if entity.cancelled_at is not None:
        extras.append(extension_datetime(EXT_ORDER_CANCELLED_AT, entity.cancelled_at))
    if entity.cancellation_reason is not None:
        extras.append(
            extension_string(EXT_ORDER_CANCELLATION_REASON, entity.cancellation_reason)
        )
    resource = _base(
        "ServiceRequest",
        entity.order_id,
        entity.tenant_id,
        version=1,
        id_prefix="SYN-ORD-",
        extras=extras,
    )
    resource["status"] = ORDER_STATUS_TO_FHIR[entity.status]
    resource["intent"] = "order"
    resource["code"] = {
        "coding": [
            {"system": TEST_CODE_SYSTEM, "code": code} for code in entity.test_codes
        ]
    }
    resource["subject"] = make_reference("Patient", entity.patient.ref, field="subject")
    resource["priority"] = entity.priority.value
    resource["occurrenceDateTime"] = entity.created_at
    return resource


def serialize_specimen(entity: Specimen) -> FhirResource:
    """Map a synthetic specimen, carrying its barcode as a second identifier."""
    extras: list[dict[str, object]] = [
        extension_code(EXT_SPECIMEN_STATUS, entity.status.value),
        extension_string(EXT_PATIENT_LABEL, entity.patient.label),
    ]
    if entity.rejection_reason is not None:
        extras.append(
            extension_string(EXT_SPECIMEN_REJECTION_REASON, entity.rejection_reason)
        )
    resource = _base(
        "Specimen",
        entity.specimen_id,
        entity.tenant_id,
        version=1,
        id_prefix="SYN-SPC-",
        extras=extras,
    )
    identifiers = resource["identifier"]
    assert isinstance(identifiers, list)
    identifiers.append(
        make_identifier(
            entity.barcode,
            field="barcode",
            system=BARCODE_SYSTEM,
            expected_prefix="SYN-BAR-",
        )
    )
    resource["status"] = SPECIMEN_STATUS_TO_FHIR[entity.status]
    resource["type"] = {"text": SPECIMEN_TYPE_TEXT}
    resource["subject"] = make_reference("Patient", entity.patient.ref, field="subject")
    resource["request"] = [make_reference("ServiceRequest", entity.order_id, field="request")]
    resource["receivedTime"] = entity.registered_at
    return resource


def serialize_amendment(amendment: object) -> dict[str, object]:
    """Serialise one immutable correction as nested local extensions."""
    fields = (
        (EXT_AMENDMENT_ID, "amendment_id", "string"),
        (EXT_AMENDMENT_PREVIOUS, "previous_value", "decimal"),
        (EXT_AMENDMENT_NEW, "new_value", "decimal"),
        (EXT_AMENDMENT_REASON, "reason", "string"),
        (EXT_AMENDMENT_ACTOR, "actor_id", "string"),
        (EXT_AMENDMENT_AT, "occurred_at", "datetime"),
        (EXT_AMENDMENT_VERSION, "version", "integer"),
    )
    children: list[dict[str, object]] = []
    for url, attribute, kind in fields:
        value = getattr(amendment, attribute)
        if kind == "decimal":
            children.append(extension_decimal(url, float(value)))
        elif kind == "integer":
            children.append(extension_integer(url, int(value)))
        elif kind == "datetime":
            children.append(extension_datetime(url, str(value)))
        else:
            children.append(extension_string(url, str(value)))
    return extension_nested(EXT_AMENDMENT, children)


def serialize_result(entity: LabResult) -> FhirResource:
    """Map a synthetic result to ``DiagnosticReport`` with auditable extras."""
    status = "corrected" if entity.version > 1 else "final"
    extras: list[dict[str, object]] = [
        extension_quantity(EXT_RESULT_VALUE, float(entity.value), entity.unit),
        extension_string(
            EXT_RESULT_RANGE, f"{entity.reference_low}|{entity.reference_high}"
        ),
        extension_boolean(EXT_RESULT_CRITICAL, bool(entity.critical_flag)),
        extension_string(EXT_RESULT_IDEMPOTENCY, entity.idempotency_key),
        extension_string(EXT_PATIENT_LABEL, entity.patient.label),
    ]
    extras.extend(serialize_amendment(item) for item in entity.amendments)
    resource = _base(
        "DiagnosticReport",
        entity.result_id,
        entity.tenant_id,
        version=entity.version,
        id_prefix="SYN-RES-",
        extras=extras,
    )
    resource["status"] = status
    resource["category"] = [dict(item) for item in _REPORT_CATEGORY]
    resource["code"] = {
        "coding": [{"system": TEST_CODE_SYSTEM, "code": entity.test_code}],
        "text": entity.test_code,
    }
    resource["subject"] = make_reference("Patient", entity.patient.ref, field="subject")
    resource["specimen"] = [make_reference("Specimen", entity.specimen_id, field="specimen")]
    resource["basedOn"] = [make_reference("ServiceRequest", entity.order_id, field="basedOn")]
    resource["effectiveDateTime"] = entity.recorded_at
    resource["issued"] = entity.recorded_at
    # No separate FHIR Observation is emitted for a synthetic result; the
    # numeric value and reference range are carried in local extensions.
    resource["result"] = []
    return resource


def serialize_entity(entity: object) -> FhirResource:
    """Serialise one supported frozen entity to a FHIR R4 resource dict."""
    resource_type = resource_type_for(entity)
    if resource_type == "Practitioner" and isinstance(entity, Practitioner):
        return serialize_practitioner(entity)
    if resource_type == "Organization" and isinstance(entity, Organization):
        return serialize_organization(entity)
    if resource_type == "Location" and isinstance(entity, Facility):
        return serialize_facility(entity)
    if resource_type == "Encounter" and isinstance(entity, Encounter):
        return serialize_encounter(entity)
    if resource_type == "Condition" and isinstance(entity, Diagnosis):
        return serialize_diagnosis(entity)
    if resource_type == "Observation" and isinstance(entity, Observation):
        return serialize_observation(entity)
    if resource_type == "ServiceRequest" and isinstance(entity, LabOrder):
        return serialize_order(entity)
    if resource_type == "Specimen" and isinstance(entity, Specimen):
        return serialize_specimen(entity)
    if resource_type == "DiagnosticReport" and isinstance(entity, LabResult):
        return serialize_result(entity)
    raise InvalidFhirResourceError(
        "entity does not match its declared resource mapping",
        details={"resourceType": resource_type, "entity": type(entity).__name__},
    )
