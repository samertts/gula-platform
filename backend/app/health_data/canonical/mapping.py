from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.health_data.canonical.models import (
    ConditionCanonical,
    EncounterCanonical,
    ObservationCanonical,
    PatientCanonical,
)


def _parse_date(val: Any) -> date | None:
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        try:
            return date.fromisoformat(val.split("T")[0])
        except (ValueError, IndexError):
            return None
    return None


def _parse_datetime(val: Any) -> datetime | None:
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
    return None


def _get_coding(fhir_resource: dict, path: list[str]) -> dict | None:
    node = fhir_resource
    for key in path:
        if isinstance(node, dict):
            node = node.get(key)
        else:
            return None
    if isinstance(node, dict):
        return node
    if isinstance(node, list) and node:
        return node[0]
    return None


def _get_code(fhir_resource: dict, path: list[str]) -> str | None:
    coding = _get_coding(fhir_resource, path)
    if coding:
        return coding.get("code")
    return None


def _get_display(fhir_resource: dict, path: list[str]) -> str | None:
    coding = _get_coding(fhir_resource, path)
    if coding:
        return coding.get("display")
    return None


def map_patient(fhir: dict[str, Any]) -> PatientCanonical:
    identifiers = fhir.get("identifier", [])
    nid_hash = None
    health_number = None
    for ident in identifiers:
        system = ident.get("system", "")
        if "national-id" in system:
            nid_hash = ident.get("value")
        elif "health-number" in system:
            health_number = ident.get("value")

    names = fhir.get("name", [])
    if names:
        name = names[0]
        given = name.get("given", [])
        given[0] if given else ""
        name.get("family", "")

    telecoms = fhir.get("telecom", [])
    gender = fhir.get("gender")

    birth_date = _parse_date(fhir.get("birthDate"))
    deceased_bool = fhir.get("deceasedBoolean", False)
    deceased_dt = _parse_datetime(fhir.get("deceasedDateTime"))

    addresses = fhir.get("address", [])
    marital_status = None
    ms = fhir.get("maritalStatus")
    if ms:
        marital_status = ms.get("text") or _get_display(ms, ["coding"])

    managing_org = None
    org = fhir.get("managingOrganization")
    if org:
        managing_org = org.get("reference")

    gps = []
    for gp in fhir.get("generalPractitioner", []):
        ref = gp.get("reference")
        if ref:
            gps.append(ref)

    return PatientCanonical(
        id=fhir.get("id", ""),
        identifiers=identifiers,
        names=names,
        telecoms=telecoms,
        gender=gender,
        birth_date=birth_date,
        deceased=deceased_bool,
        deceased_datetime=deceased_dt,
        addresses=addresses,
        marital_status=marital_status,
        general_practitioners=gps,
        managing_organization=managing_org,
        national_id_hash=nid_hash,
        health_number=health_number,
        source_system="fhir",
        source_id=fhir.get("id"),
    )


def map_encounter(fhir: dict[str, Any]) -> EncounterCanonical:
    period = fhir.get("period", {}) or {}
    participant_list = fhir.get("participant", [])
    diagnosis_list = fhir.get("diagnosis", [])

    reason_code = None
    reason_description = None
    reason = fhir.get("reasonCode")
    if reason:
        reason_code = _get_code(reason, ["coding"])
        reason_description = reason.get("text") or _get_display(reason, ["coding"])

    return EncounterCanonical(
        id=fhir.get("id", ""),
        patient_id=_extract_patient_ref(fhir.get("subject")),
        status=fhir.get("status", "planned"),
        encounter_class=fhir.get("class", {}).get("code")
        if isinstance(fhir.get("class"), dict)
        else None,
        encounter_type=_get_display(fhir, ["type", "coding"])
        or _get_code(fhir, ["type", "coding"]),
        period_start=_parse_datetime(period.get("start")),
        period_end=_parse_datetime(period.get("end")),
        service_provider=_extract_ref(fhir.get("serviceProvider")),
        participants=participant_list,
        diagnoses=diagnosis_list,
        reason_code=reason_code,
        reason_description=reason_description,
        source_system="fhir",
        source_id=fhir.get("id"),
    )


def map_observation(fhir: dict[str, Any]) -> ObservationCanonical:
    value_qty = fhir.get("valueQuantity")
    value_str = fhir.get("valueString")
    value_cc = fhir.get("valueCodeableConcept")

    ref_range = fhir.get("referenceRange", [])
    interpretations = fhir.get("interpretation", [])

    code_obj = fhir.get("code", {})
    code = _get_code(code_obj, ["coding"]) if isinstance(code_obj, dict) else None
    display = _get_display(code_obj, ["coding"]) if isinstance(code_obj, dict) else None

    return ObservationCanonical(
        id=fhir.get("id", ""),
        patient_id=_extract_ref(fhir.get("subject")),
        encounter_id=_extract_ref(fhir.get("encounter")),
        status=fhir.get("status", "final"),
        category=_get_display(fhir, ["category", "coding"]),
        code=code,
        code_display=display,
        value_quantity=value_qty,
        value_string=value_str,
        value_concept=value_cc,
        interpretation=interpretations if isinstance(interpretations, list) else [],
        reference_range=ref_range,
        issued=_parse_datetime(fhir.get("issued")),
        effective_datetime=_parse_datetime(fhir.get("effectiveDateTime")),
        source_system="fhir",
        source_id=fhir.get("id"),
    )


def map_condition(fhir: dict[str, Any]) -> ConditionCanonical:
    code_obj = fhir.get("code", {})
    code = _get_code(code_obj, ["coding"]) if isinstance(code_obj, dict) else None
    display = _get_display(code_obj, ["coding"]) if isinstance(code_obj, dict) else None

    body_site = None
    body_sites = fhir.get("bodySite", [])
    if body_sites:
        body_site = (
            _get_display(body_sites[0], ["coding"]) if isinstance(body_sites[0], dict) else None
        )

    severity = None
    sev = fhir.get("severity")
    if sev:
        severity = _get_display(sev, ["coding"]) or sev.get("text")

    return ConditionCanonical(
        id=fhir.get("id", ""),
        patient_id=_extract_ref(fhir.get("subject")),
        encounter_id=_extract_ref(fhir.get("encounter")),
        status=fhir.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "active")
        if isinstance(fhir.get("clinicalStatus"), dict)
        else "active",
        severity=severity,
        code=code,
        code_display=display,
        body_site=body_site,
        onset_datetime=_parse_datetime(fhir.get("onsetDateTime")),
        abatement_datetime=_parse_datetime(fhir.get("abatementDateTime")),
        recorded_date=_parse_datetime(fhir.get("recordedDate")),
        clinical_status=fhir.get("clinicalStatus", {}).get("coding", [{}])[0].get("code")
        if isinstance(fhir.get("clinicalStatus"), dict)
        else None,
        verification_status=fhir.get("verificationStatus", {}).get("coding", [{}])[0].get("code")
        if isinstance(fhir.get("verificationStatus"), dict)
        else None,
        source_system="fhir",
        source_id=fhir.get("id"),
    )


def _extract_ref(ref: Any) -> str | None:
    if isinstance(ref, dict):
        full = ref.get("reference", "")
        if "/" in full:
            return full.split("/")[-1]
        return full or None
    return None


def _extract_patient_ref(subject: Any) -> str | None:
    return _extract_ref(subject)
