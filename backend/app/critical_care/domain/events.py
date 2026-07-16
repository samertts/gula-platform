from __future__ import annotations

from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class ICUAdmissionCreated(NationalDomainEvent):
    event_type: str = "criticalcare.admission.created"
    aggregate_type: str = "ICUAdmission"
    admission_id: str = ""
    patient_id: str = ""
    icu_type: str = ""


@dataclass
class ICUDischarged(NationalDomainEvent):
    event_type: str = "criticalcare.admission.discharged"
    aggregate_type: str = "ICUAdmission"
    admission_id: str = ""
    discharge_reason: str = ""


@dataclass
class VitalSignsRecorded(NationalDomainEvent):
    event_type: str = "criticalcare.vitals.recorded"
    aggregate_type: str = "VitalSignsRecord"
    record_id: str = ""
    patient_id: str = ""


@dataclass
class VentilatorSettingsChanged(NationalDomainEvent):
    event_type: str = "criticalcare.ventilator.changed"
    aggregate_type: str = "VentilatorSetting"
    setting_id: str = ""
    patient_id: str = ""
    mode: str = ""


@dataclass
class EarlyWarningScoreCalculated(NationalDomainEvent):
    event_type: str = "criticalcare.ews.calculated"
    aggregate_type: str = "EarlyWarningScore"
    score_id: str = ""
    patient_id: str = ""
    score_value: int = 0
    score_system: str = ""


@dataclass
class SepsisAlertTriggered(NationalDomainEvent):
    event_type: str = "criticalcare.sepsis.alert"
    aggregate_type: str = "CriticalAlert"
    patient_id: str = ""
    alert_type: str = "sepsis"
    severity: str = ""


@dataclass
class CriticalAlertRaised(NationalDomainEvent):
    event_type: str = "criticalcare.alert.raised"
    aggregate_type: str = "CriticalAlert"
    alert_id: str = ""
    patient_id: str = ""
    alert_type: str = ""
    severity: str = ""


@dataclass
class FluidBalanceRecorded(NationalDomainEvent):
    event_type: str = "criticalcare.fluid_balance.recorded"
    aggregate_type: str = "FluidBalance"
    record_id: str = ""
    patient_id: str = ""
    net_balance_ml: float = 0.0


@dataclass
class InfusionStarted(NationalDomainEvent):
    event_type: str = "criticalcare.infusion.started"
    aggregate_type: str = "ContinuousInfusion"
    infusion_id: str = ""
    patient_id: str = ""
    medication: str = ""
    rate: str = ""


@dataclass
class DeviceDataReceived(NationalDomainEvent):
    event_type: str = "criticalcare.device.data_received"
    aggregate_type: str = "DeviceIntegration"
    patient_id: str = ""
    device_type: str = ""
    data_type: str = ""
