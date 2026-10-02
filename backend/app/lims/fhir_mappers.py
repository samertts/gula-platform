"""FHIR R4 Mappers for National LIMS entities.

Maps LIMS domain objects to FHIR R4 resources:
  - Specimen → FHIR Specimen
  - Result → FHIR Observation
  - LabReport → FHIR DiagnosticReport
  - Order → FHIR ServiceRequest
  - Instrument → FHIR Device

Uses the existing FHIR primitives from app.national.fhir.base
where possible.
"""

from __future__ import annotations

from typing import Any


def _fhir_coding(system: str, code: str, display: str = "") -> dict:
    return {"system": system, "code": code, "display": display}


def _fhir_codeable_concept(coding: list[dict], text: str = "") -> dict:
    return {"coding": coding, "text": text}


def _fhir_reference(reference: str, display: str = "") -> dict:
    return {"reference": reference, "display": display}


def _fhir_quantity(value: float, unit: str, system: str = "http://unitsofmeasure.org") -> dict:
    return {"value": value, "unit": unit, "system": system, "code": unit}


def _fhir_period(start: str | None, end: str | None = None) -> dict:
    result = {}
    if start:
        result["start"] = start
    if end:
        result["end"] = end
    return result


# ── Specimen → FHIR Specimen ─────────────────────────────────────────


def specimen_to_fhir(specimen) -> dict:
    """Map LIMS Specimen to FHIR R4 Specimen resource."""
    resource: dict[str, Any] = {
        "resourceType": "Specimen",
        "id": specimen.fhir_id or f"lims-spec-{specimen.id}",
        "identifier": [{"system": "urn:gula:lims:specimen", "value": specimen.barcode}],
        "status": _map_specimen_status(specimen.status),
        "type": _fhir_codeable_concept(
            [_fhir_coding("http://gula.iq/CodeSystem/specimen-type", specimen.specimen_type)],
        ),
        "collection": {},
        "receivedTime": specimen.received_at.isoformat() if specimen.received_at else None,
    }

    if specimen.collection_time:
        resource["collection"]["collectedDateTime"] = specimen.collection_time.isoformat()
    if specimen.collected_by:
        resource["collection"]["collector"] = _fhir_reference(
            f"Practitioner/{specimen.collected_by}",
        )
    if specimen.collection_site:
        resource["collection"]["bodySite"] = _fhir_codeable_concept(
            [_fhir_coding("http://snomed.info/sct", specimen.collection_site)],
        )
    if specimen.volume_ml:
        resource["collection"]["quantity"] = _fhir_quantity(specimen.volume_ml, "mL")

    if specimen.container_type:
        resource["container"] = [{
            "type": _fhir_codeable_concept(
                [_fhir_coding("http://gula.iq/CodeSystem/container-type", specimen.container_type)],
            ),
        }]

    if specimen.storage_id:
        resource["note"] = [{"text": f"Storage: {specimen.storage_id}"}]

    return {k: v for k, v in resource.items() if v is not None}


def _map_specimen_status(status: str) -> str:
    mapping = {
        "ordered": "available",
        "collected": "available",
        "received": "available",
        "accepted": "available",
        "rejected": "unavailable",
        "analyzing": "available",
        "analyzed": "available",
        "verified": "available",
        "validated": "available",
        "released": "available",
        "archived": "entered-in-error",
        "disposed": "entered-in-error",
    }
    return mapping.get(status, "available")


# ── Result → FHIR Observation ─────────────────────────────────────────


def result_to_fhir(result) -> dict:
    """Map LIMS Result to FHIR R4 Observation resource."""
    resource: dict[str, Any] = {
        "resourceType": "Observation",
        "id": result.fhir_id or f"lims-obs-{result.id}",
        "status": _map_result_status(result.validation_status),
        "code": _fhir_codeable_concept(
            [_fhir_coding("http://loinc.org", result.loinc_code or result.test_code, result.test_name)],
        ),
        "subject": _fhir_reference(f"Patient/{result.specimen.order.patient_id}" if hasattr(result, "specimen") and hasattr(result.specimen, "order") else "unknown"),
        "specimen": _fhir_reference(f"Specimen/lims-spec-{result.specimen_id}"),
    }

    if result.value_numeric is not None and result.unit:
        resource["valueQuantity"] = _fhir_quantity(result.value_numeric, result.unit)
    elif result.value_text:
        resource["valueString"] = result.value_text
    elif result.value_numeric is not None:
        resource["valueQuantity"] = {"value": result.value_numeric}

    if result.ref_range_low is not None or result.ref_range_high is not None:
        low = result.ref_range_low if result.ref_range_low is not None else 0
        high = result.ref_range_high if result.ref_range_high is not None else float("inf")
        resource["referenceRange"] = [{
            "low": {"value": low, "unit": result.unit or ""},
            "high": {"value": high, "unit": result.unit or ""},
        }]

    if result.flag:
        interpretation = _map_flag_to_interpretation(result.flag)
        if interpretation:
            resource["interpretation"] = [_fhir_codeable_concept([interpretation])]

    if result.performed_at:
        resource["effectiveDateTime"] = result.performed_at.isoformat()

    if result.instrument_id:
        resource["device"] = _fhir_reference(f"Device/lims-inst-{result.instrument_id}")

    return {k: v for k, v in resource.items() if v is not None}


def _map_result_status(status: str) -> str:
    mapping = {
        "pending": "preliminary",
        "auto_validated": "final",
        "validated": "final",
        "flagged": "preliminary",
        "rejected": "cancelled",
    }
    return mapping.get(status, "preliminary")


def _map_flag_to_interpretation(flag: str) -> dict | None:
    mapping = {
        "high": _fhir_coding("http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "H", "High"),
        "low": _fhir_coding("http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "L", "Low"),
        "critical_high": _fhir_coding("http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "HH", "Critical high"),
        "critical_low": _fhir_coding("http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "LL", "Critical low"),
        "normal": _fhir_coding("http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "N", "Normal"),
        "panic": _fhir_coding("http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "A", "Abnormal"),
    }
    return mapping.get(flag)


# ── LabReport → FHIR DiagnosticReport ────────────────────────────────


def report_to_fhir_diagnostic(report, results: list | None = None) -> dict:
    """Map LIMS LabReport to FHIR R4 DiagnosticReport resource."""
    resource: dict[str, Any] = {
        "resourceType": "DiagnosticReport",
        "id": report.fhir_id or f"lims-dr-{report.id}",
        "status": _map_report_status(report.status),
        "code": _fhir_codeable_concept(
            [_fhir_coding("http://gula.iq/CodeSystem/lab-report", report.report_number)],
        ),
        "issued": report.generated_at.isoformat() if report.generated_at else None,
        "result": [],
    }

    if report.title:
        resource["code"]["text"] = report.title

    if results:
        resource["result"] = [
            _fhir_reference(f"Observation/lims-obs-{r.id}") for r in results
        ]

    return {k: v for k, v in resource.items() if v is not None}


def _map_report_status(status: str) -> str:
    mapping = {
        "draft": "preliminary",
        "final": "final",
        "amended": "amended",
        "corrected": "amended",
        "cancelled": "cancelled",
    }
    return mapping.get(status, "preliminary")


# ── Order → FHIR ServiceRequest ──────────────────────────────────────


def _map_order_status(status: str | None) -> str:
    """Map a LIMS order state onto FHIR ServiceRequest.status.

    The source vocabulary is ``lims/state_machine._ORDER_TRANSITIONS``, which is
    authoritative for this column; the twelve states below are its keys. They are
    mapped onto FHIR's own codes rather than an invented set:

      in flight, still to be acted upon            -> "active"
      the requested service was performed          -> "completed"
      withdrawn ("cancelled" is not a code here)   -> "revoked"

    An unrecognised state resolves to "unknown" — FHIR's own code for "the source
    system does not know which status applies" — and deliberately not to
    "active". "active" asserts the request is in force and ready to be acted
    upon, so defaulting to it would invite a consumer to act on a request that
    may have been withdrawn. That is the unsafe direction here, exactly as
    claiming "final" was for an Observation.
    """
    mapping = {
        "pending": "active",
        "accessioned": "active",
        "collecting": "active",
        "collected": "active",
        "in_transport": "active",
        "received": "active",
        "in_progress": "active",
        "completed": "completed",
        "validated": "completed",
        "released": "completed",
        "corrected": "completed",
        "cancelled": "revoked",
    }
    return mapping.get((status or "").strip().casefold(), "unknown")


def order_to_fhir_service_request(order, *, patient_id: int | None) -> dict:
    """Map LIMS Order to FHIR R4 ServiceRequest resource.

    ``patient_id`` is keyword-only with no default on purpose. It used to be
    absent and the subject was built as ``Patient/{order.order_id}`` — but
    ``lims_orders.order_id`` is a foreign key to ``lab_orders.id``, not a
    patient, so every ServiceRequest named a Patient resource by an *order*
    primary key. Measured on PostgreSQL: six requests for patient 22 published
    ``subject: Patient/36`` through ``Patient/41``. Where the two id ranges
    overlap that resolves to a different real person, attributing a laboratory
    request to the wrong patient. ``result_to_fhir`` in this same module already
    reaches the patient correctly through ``specimen.order.patient_id``, and 18
    of the 19 Patient references in the codebase use a patient id — this was the
    single outlier.

    No default is the control: a call site that forgets the argument fails
    loudly rather than silently publishing a wrong-patient reference.
    """
    if patient_id is None:
        # ServiceRequest.subject is 1..1, so there is no honest resource to build
        # without it — and an order-derived or fabricated reference is precisely
        # what this signature exists to prevent. lims_orders.order_id is NOT NULL
        # with ON DELETE CASCADE, so the parent order and its patient always
        # exist; reaching here means a caller did not resolve them.
        raise ValueError(
            f"cannot build ServiceRequest for LIMS order {order.id}: the patient "
            "could not be resolved, and a Patient reference must not be guessed",
        )
    resource: dict[str, Any] = {
        "resourceType": "ServiceRequest",
        "id": order.fhir_id or f"lims-sr-{order.id}",
        "status": _map_order_status(order.order_status),
        "intent": "order",
        "code": _fhir_codeable_concept(
            [_fhir_coding("http://gula.iq/CodeSystem/accession-number", order.accession_number)],
        ),
        "subject": _fhir_reference(f"Patient/{patient_id}"),
    }

    if order.priority == "urgent":
        resource["priority"] = "urgent"
    elif order.priority == "stat":
        resource["priority"] = "stat"
    else:
        resource["priority"] = "routine"

    if order.ordered_at:
        resource["authoredOn"] = order.ordered_at.isoformat()

    if order.ordered_by:
        resource["requester"] = _fhir_reference(f"Practitioner/{order.ordered_by}")

    return {k: v for k, v in resource.items() if v is not None}


# ── Instrument → FHIR Device ─────────────────────────────────────────


def instrument_to_fhir_device(instrument) -> dict:
    """Map LIMS Instrument to FHIR R4 Device resource."""
    resource: dict[str, Any] = {
        "resourceType": "Device",
        "id": instrument.fhir_id or f"lims-inst-{instrument.id}",
        "status": _map_device_status(instrument.status),
        "serialNumber": instrument.serial_number or "",
        "deviceName": [{
            "name": instrument.instrument_code,
            "type": "user-friendly-name",
        }],
    }

    if instrument.model:
        resource["modelNumber"] = instrument.model.model_code if hasattr(instrument.model, "model_code") else ""
        if hasattr(instrument.model, "manufacturer") and instrument.model.manufacturer:
            resource["manufacturer"] = instrument.model.manufacturer.name

    if instrument.software_version:
        resource["version"] = [{"value": instrument.software_version}]

    return {k: v for k, v in resource.items() if v is not None}


def _map_device_status(status: str) -> str:
    mapping = {
        "online": "active",
        "offline": "inactive",
        "maintenance": "inactive",
        "error": "entered-in-error",
        "disabled": "entered-in-error",
    }
    return mapping.get(status, "unknown")
