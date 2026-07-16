from __future__ import annotations

from dataclasses import dataclass

from app.national.events.base import NationalDomainEvent


@dataclass
class DeviceRegistered(NationalDomainEvent):
    event_type: str = "biomedical.device.registered"
    aggregate_type: str = "MedicalDevice"
    device_id: str = ""
    udi: str = ""
    device_category: str = ""


@dataclass
class WorkOrderCreated(NationalDomainEvent):
    event_type: str = "biomedical.work_order.created"
    aggregate_type: str = "WorkOrder"
    work_order_id: str = ""
    device_id: str = ""
    maintenance_type: str = ""


@dataclass
class WorkOrderCompleted(NationalDomainEvent):
    event_type: str = "biomedical.work_order.completed"
    aggregate_type: str = "WorkOrder"
    work_order_id: str = ""
    device_id: str = ""
    result: str = ""


@dataclass
class CalibrationPerformed(NationalDomainEvent):
    event_type: str = "biomedical.calibration.performed"
    aggregate_type: str = "CalibrationRecord"
    calibration_id: str = ""
    device_id: str = ""
    result: str = ""


@dataclass
class CalibrationFailed(NationalDomainEvent):
    event_type: str = "biomedical.calibration.failed"
    aggregate_type: str = "CalibrationRecord"
    calibration_id: str = ""
    device_id: str = ""
    deviation: str = ""


@dataclass
class DeviceIncidentReported(NationalDomainEvent):
    event_type: str = "biomedical.incident.reported"
    aggregate_type: str = "DeviceIncident"
    incident_id: str = ""
    device_id: str = ""
    severity: str = ""


@dataclass
class DeviceRecallIssued(NationalDomainEvent):
    event_type: str = "biomedical.recall.issued"
    aggregate_type: str = "DeviceRecall"
    recall_id: str = ""
    device_id: str = ""
    recall_class: str = ""


@dataclass
class DeviceDecommissioned(NationalDomainEvent):
    event_type: str = "biomedical.device.decommissioned"
    aggregate_type: str = "MedicalDevice"
    device_id: str = ""
    reason: str = ""


@dataclass
class MaintenanceDue(NationalDomainEvent):
    event_type: str = "biomedical.maintenance.due"
    aggregate_type: str = "MedicalDevice"
    device_id: str = ""
    maintenance_type: str = ""
    due_date: str = ""


@dataclass
class SparePartUsed(NationalDomainEvent):
    event_type: str = "biomedical.spare_part.used"
    aggregate_type: str = "SparePart"
    part_id: str = ""
    work_order_id: str = ""
    quantity: int = 0
