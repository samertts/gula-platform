"""Synthetic-first device gateway boundary shared by Hospital and EMS.

No hardware, vendor SDK, network call, GPS, or raw telemetry persistence is
implemented here. The adapter only normalizes an allowlisted reading into the
canonical Hospital Core vital-observation shape; callers still perform the
usual patient/encounter authorization and transactional write.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

SUPPORTED_DEVICE_TYPES = frozenset({"monitor", "defibrillator", "glucometer", "pulse_oximeter", "ventilator", "infusion_pump"})


@dataclass(frozen=True)
class ValidatedDeviceObservation:
    patient_person_id: str
    encounter_id: str
    observer_account_id: str
    device_reference: str
    observed_at: datetime
    vital_type: str
    value_numeric: str
    unit: str
    method: str
    source: str
    validation_status: str
    warning_code: str | None


class DeviceGateway(Protocol):
    name: str
    connected: bool

    def normalize_readings(
        self,
        *,
        patient_person_id: str,
        encounter_id: str,
        observer_account_id: str,
        device_type: str,
        device_reference: str,
        readings: Mapping[str, object],
        observed_at: datetime,
    ) -> list[ValidatedDeviceObservation]:
        """Return validated canonical observations without persisting telemetry."""


class HospitalDeviceGateway(DeviceGateway, Protocol):
    """Future hospital monitor/ventilator/infusion-pump boundary."""


class EMSDeviceGateway(DeviceGateway, Protocol):
    """Future EMS monitor/defibrillator/glucometer/pulse-oximeter boundary."""


class SyntheticDeviceGateway:
    """Deterministic adapter for synthetic fixtures and contract tests only."""

    name = "synthetic-device-gateway"
    connected = False

    _UNITS = {
        "heart_rate": "bpm",
        "respiratory_rate": "breaths/min",
        "oxygen_saturation": "%",
        "blood_pressure_systolic": "mmHg",
        "blood_pressure_diastolic": "mmHg",
        "temperature": "C",
        "glucose": "mg/dL",
        "gcs": "score",
    }
    _RANGES = {
        "heart_rate": (0, 300),
        "respiratory_rate": (0, 100),
        "oxygen_saturation": (0, 100),
        "blood_pressure_systolic": (0, 400),
        "blood_pressure_diastolic": (0, 300),
        "temperature": (20, 45),
        "glucose": (0, 2000),
        "gcs": (3, 15),
    }

    def normalize_readings(
        self,
        *,
        patient_person_id: str,
        encounter_id: str,
        observer_account_id: str,
        device_type: str,
        device_reference: str,
        readings: Mapping[str, object],
        observed_at: datetime,
    ) -> list[ValidatedDeviceObservation]:
        if not patient_person_id or not encounter_id or not observer_account_id:
            raise ValueError("patient, encounter, and observer are required")
        if device_type not in SUPPORTED_DEVICE_TYPES:
            raise ValueError("unsupported synthetic device type")
        if not device_reference or len(device_reference) > 160:
            raise ValueError("device reference is required and bounded")
        timestamp = observed_at.replace(tzinfo=UTC) if observed_at.tzinfo is None else observed_at.astimezone(UTC)
        now = datetime.now(UTC)
        if timestamp > now or (now - timestamp).total_seconds() > 7 * 24 * 3600:
            raise ValueError("observation timestamp is outside the accepted window")
        observations: list[ValidatedDeviceObservation] = []
        for vital_type, raw_value in readings.items():
            if vital_type not in self._UNITS:
                continue
            try:
                value = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"reading {vital_type} is not numeric") from exc
            if value != value or value in (float("inf"), float("-inf")):
                raise ValueError(f"reading {vital_type} is not finite")
            lower, upper = self._RANGES[vital_type]
            warning = None if lower <= value <= upper else "OUTSIDE_EXPECTED_RANGE"
            observations.append(
                ValidatedDeviceObservation(
                    patient_person_id=patient_person_id,
                    encounter_id=encounter_id,
                    observer_account_id=observer_account_id,
                    device_reference=device_reference,
                    observed_at=timestamp,
                    vital_type=vital_type,
                    value_numeric=str(value),
                    unit=self._UNITS[vital_type],
                    method="DEVICE_VALIDATED",
                    source=self.name,
                    validation_status="WARNING" if warning else "VALID",
                    warning_code=warning,
                ),
            )
        if not observations:
            raise ValueError("no allowlisted device readings were supplied")
        return observations


class SyntheticHospitalDeviceGateway(SyntheticDeviceGateway):
    name = "synthetic-hospital-device-gateway"


class SyntheticEMSDeviceGateway(SyntheticDeviceGateway):
    name = "synthetic-ems-device-gateway"


__all__ = [
    "DeviceGateway",
    "EMSDeviceGateway",
    "HospitalDeviceGateway",
    "SyntheticDeviceGateway",
    "SyntheticEMSDeviceGateway",
    "SyntheticHospitalDeviceGateway",
    "ValidatedDeviceObservation",
]
