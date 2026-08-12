from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class DiseaseCaseReported(NationalDomainEvent):
    event_type: str = "public_health.disease_case.reported"
    disease_case_id: str = ""
    disease_code: str = ""
    disease_name: str = ""
    region: str = ""
    severity: str = ""


@dataclass
class OutbreakAlertRaised(NationalDomainEvent):
    event_type: str = "public_health.outbreak.raised"
    outbreak_id: str = ""
    disease: str = ""
    region: str = ""
    confirmed_cases: int = 0
    alert_level: str = ""


@dataclass
class OutbreakStatusChanged(NationalDomainEvent):
    event_type: str = "public_health.outbreak.status_changed"
    outbreak_id: str = ""
    previous_status: str = ""
    new_status: str = ""


@dataclass
class VaccinationRecorded(NationalDomainEvent):
    event_type: str = "public_health.vaccination.recorded"
    vaccination_id: str = ""
    patient_id: str = ""
    vaccine: str = ""
    dose_number: int = 0


@dataclass
class SurveillanceAlertGenerated(NationalDomainEvent):
    event_type: str = "public_health.surveillance.alert"
    alert_id: str = ""
    disease: str = ""
    region: str = ""
    z_score: float = 0.0
    alert_level: str = ""


@dataclass
class PublicHealthReportPublished(NationalDomainEvent):
    event_type: str = "public_health.report.published"
    report_id: str = ""
    report_type: str = ""
    period_start: str = ""
    period_end: str = ""


@dataclass
class MassCasualtyNotified(NationalDomainEvent):
    event_type: str = "public_health.mass_casualty.notified"
    event_id: str = ""
    location: str = ""
    severity: str = ""
    affected_count: int = 0
