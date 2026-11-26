"""Synthetic FHIR R4 projection for released laboratory results.

This module composes the existing structural FHIR validator and the read-only
synthetic exchange contract. It does not create a new FHIR endpoint, database,
or write path.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app._compat import UTC
from app.integration.fhir_r4_exchange import (
    SYNTHETIC_TAG_CODE,
    SYNTHETIC_TAG_SYSTEM,
    FHIRContractError,
    validate_synthetic_bundle,
)
from app.lab_slice.models import (
    RELEASE_RELEASED,
    ReleaseDecision,
    SyntheticOrder,
    SyntheticPatient,
    SyntheticResult,
    SyntheticSpecimen,
)
from app.lab_slice.terminology_bindings import BINDING_UNMAPPED, TerminologyBinding
from app.national.fhir.validation import FHIRValidationEngine


def _meta() -> dict[str, Any]:
    return {
        "source": "urn:gula:synthetic-lab-slice",
        "tag": [{"system": SYNTHETIC_TAG_SYSTEM, "code": SYNTHETIC_TAG_CODE}],
    }


def _resource_id(prefix: str, source_id: str) -> str:
    return f"{prefix}-{source_id}"


def build_bundle(
    *,
    patient: SyntheticPatient,
    order: SyntheticOrder,
    specimen: SyntheticSpecimen,
    result: SyntheticResult,
    decision: ReleaseDecision,
    binding: TerminologyBinding,
) -> dict[str, Any]:
    """Build and validate a synthetic-only FHIR Bundle after manual release."""
    if decision.status != RELEASE_RELEASED or decision.reviewer is None:
        raise FHIRContractError("only manually released synthetic results can be projected")
    if binding.status == BINDING_UNMAPPED:
        raise FHIRContractError("unmapped terminology cannot be projected")
    if order.patient_id != patient.patient_id or specimen.patient_id != patient.patient_id:
        raise FHIRContractError("synthetic references must belong to the same patient")
    if result.order_id != order.order_id or result.specimen_id != specimen.specimen_id:
        raise FHIRContractError("synthetic result references are inconsistent")

    now = datetime.now(UTC).isoformat()
    concept = binding.codeable_concept()
    patient_ref = {"reference": f"Patient/{patient.patient_id}"}
    request_ref = {"reference": f"ServiceRequest/{order.order_id}"}
    specimen_ref = {"reference": f"Specimen/{specimen.specimen_id}"}
    observation_ref = {"reference": f"Observation/{result.result_id}"}

    resources: list[dict[str, Any]] = [
        {
            "resourceType": "Patient",
            "id": patient.patient_id,
            "meta": _meta(),
            "active": True,
            "gender": patient.gender,
        },
        {
            "resourceType": "Organization",
            "id": "synthetic-facility-001",
            "meta": _meta(),
            "active": True,
            "name": "Synthetic GULA Facility",
        },
        {
            "resourceType": "ServiceRequest",
            "id": order.order_id,
            "meta": _meta(),
            "status": "active",
            "intent": "order",
            "priority": order.priority,
            "subject": patient_ref,
            "code": concept,
        },
        {
            "resourceType": "Specimen",
            "id": specimen.specimen_id,
            "meta": _meta(),
            "status": "available",
            "subject": patient_ref,
            "request": [request_ref],
            "type": {"text": specimen.specimen_type},
        },
        {
            "resourceType": "Observation",
            "id": result.result_id,
            "meta": _meta(),
            "status": "final",
            "code": concept,
            "subject": patient_ref,
            "specimen": specimen_ref,
            "issued": now,
            "effectiveDateTime": now,
            "valueQuantity": {
                "value": result.value,
                "unit": result.unit,
                "system": "http://unitsofmeasure.org",
                "code": result.unit,
            },
            "referenceRange": [
                {
                    "low": {"value": result.reference_low, "unit": result.unit},
                    "high": {"value": result.reference_high, "unit": result.unit},
                },
            ],
        },
        {
            "resourceType": "DiagnosticReport",
            "id": _resource_id("synthetic-report", result.result_id),
            "meta": _meta(),
            "status": "final",
            "code": {"text": "Synthetic laboratory report"},
            "subject": patient_ref,
            "specimen": [specimen_ref],
            "result": [observation_ref],
            "issued": now,
        },
        {
            "resourceType": "Provenance",
            "id": _resource_id("synthetic-provenance", result.result_id),
            "meta": _meta(),
            "target": [observation_ref],
            "recorded": now,
            "activity": {"text": "synthetic manual release"},
        },
    ]

    bundle: dict[str, Any] = {
        "resourceType": "Bundle",
        "id": _resource_id("synthetic-bundle", result.result_id),
        "type": "collection",
        "meta": _meta(),
        "entry": [
            {"fullUrl": f"urn:uuid:{resource['id']}", "resource": resource}
            for resource in resources
        ],
    }

    errors: list[str] = []
    validator = FHIRValidationEngine()
    for resource in resources:
        validation = validator.validate(resource)
        errors.extend(f"{resource['resourceType']}: {error}" for error in validation.errors)
    errors.extend(validate_synthetic_bundle(bundle))
    if errors:
        raise FHIRContractError("; ".join(errors))
    return bundle
