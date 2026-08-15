"""Small, deterministic HL7 v2 parser for synthetic gateway messages.

The parser intentionally supports the safe ORU^R01 subset needed by GULA's
simulated laboratory flows. It does not persist the raw message and does not
open a network/device connection.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


class HL7ConversionError(ValueError):
    pass


@dataclass(frozen=True)
class HL7Message:
    message_type: str
    control_id: str | None
    sender: str | None
    receiver: str | None
    patient_identifier: str | None
    patient_name: str | None
    service_code: str | None
    observed_at: str | None
    observations: list[dict[str, str | None]]


def _field(segment: list[str], number: int) -> str | None:
    value = segment[number] if number < len(segment) else ""
    return value or None


def _component(value: str | None, index: int = 0) -> str | None:
    if not value:
        return None
    return value.split("^", maxsplit=3)[index] or None


def _segments(raw_message: str) -> tuple[str, list[list[str]]]:
    raw = raw_message.replace("\r\n", "\r").replace("\n", "\r").strip("\r")
    if not raw or not raw.startswith("MSH") or len(raw) < 4:
        raise HL7ConversionError("HL7 message must start with an MSH segment")
    field_separator = raw[3]
    segments = [segment.split(field_separator) for segment in raw.split("\r") if segment]
    if not segments or segments[0][0] != "MSH":
        raise HL7ConversionError("HL7 message has no valid MSH segment")
    return field_separator, segments


def parse_oru_r01(raw_message: str) -> HL7Message:
    _separator, segments = _segments(raw_message)
    msh = next((segment for segment in segments if segment[0] == "MSH"), None)
    if msh is None:
        raise HL7ConversionError("MSH segment is required")
    message_type = _component(_field(msh, 8))
    if message_type != "ORU":
        raise HL7ConversionError("Only ORU messages are supported by the synthetic converter")
    trigger = _component(_field(msh, 8), 1)
    if trigger != "R01":
        raise HL7ConversionError("Only ORU^R01 messages are supported by the synthetic converter")

    pid = next((segment for segment in segments if segment[0] == "PID"), [])
    obr = next((segment for segment in segments if segment[0] == "OBR"), [])
    observations: list[dict[str, str | None]] = []
    for segment in segments:
        if segment[0] != "OBX":
            continue
        observations.append(
            {
                "code": _component(_field(segment, 3)),
                "display": _component(_field(segment, 3), 1),
                "value": _field(segment, 5),
                "unit": _component(_field(segment, 6)),
                "reference_range": _field(segment, 7),
                "interpretation": _component(_field(segment, 8)),
                "status": _field(segment, 11) or "final",
            },
        )
    if not observations:
        raise HL7ConversionError("ORU^R01 message must contain at least one OBX segment")
    return HL7Message(
        message_type="ORU^R01",
        control_id=_field(msh, 9),
        sender=_field(msh, 2),
        receiver=_field(msh, 4),
        patient_identifier=_component(_field(pid, 3)),
        patient_name=" ".join(filter(None, (_component(_field(pid, 5), 1), _component(_field(pid, 5), 0)))) or None,
        service_code=_component(_field(obr, 4)),
        observed_at=_field(obr, 7),
        observations=observations,
    )


def _observation_value(observation: dict[str, str | None]) -> dict:
    value = observation.get("value")
    unit = observation.get("unit")
    numeric: float | None = None
    if value is not None:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = None
    if numeric is not None:
        return {"valueQuantity": {"value": numeric, "unit": unit} if unit else {"value": numeric}}
    return {"valueString": value or ""}


def to_fhir_bundle(message: HL7Message) -> dict:
    patient_id = message.patient_identifier or "synthetic-patient"
    report_id = f"report-{message.control_id or 'synthetic'}"
    entries: list[dict] = [
        {
            "resourceType": "Patient",
            "id": patient_id,
            "identifier": [{"value": patient_id}],
            "name": [{"text": message.patient_name}] if message.patient_name else [],
        },
    ]
    observation_ids: list[str] = []
    for index, item in enumerate(message.observations, start=1):
        observation_id = f"obs-{message.control_id or 'synthetic'}-{index}"
        observation_ids.append(observation_id)
        code = item.get("code") or "unknown"
        resource = {
            "resourceType": "Observation",
            "id": observation_id,
            "status": item.get("status") or "final",
            "code": {"coding": [{"code": code, "display": item.get("display")} ]},
            "subject": {"reference": f"Patient/{patient_id}"},
            **_observation_value(item),
        }
        if item.get("reference_range"):
            resource["referenceRange"] = [{"text": item["reference_range"]}]
        if item.get("interpretation"):
            resource["interpretation"] = [{"text": item["interpretation"]}]
        entries.append(resource)
    entries.append(
        {
            "resourceType": "DiagnosticReport",
            "id": report_id,
            "status": "final",
            "code": {"coding": [{"code": message.service_code or "laboratory-panel"}]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "result": [{"reference": f"Observation/{item_id}"} for item_id in observation_ids],
        },
    )
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": resource} for resource in entries],
        "meta": {
            "tag": [{"system": "https://gula.example/simulation", "code": "synthetic-only"}],
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
        },
    }
