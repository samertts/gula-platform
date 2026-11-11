from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.biomedical.domain.entities import (
    CalibrationRecord,
    DeviceIncident,
    DeviceMaintenanceSchedule,
    DeviceRecall,
    MedicalDevice,
    SafetyInspection,
    Technician,
    Vendor,
    WorkOrder,
)
from app.biomedical.domain.enums import (
    DeviceStatus,
    WorkOrderStatus,
)
from app.biomedical.exceptions import (
    DeviceNotFoundError,
    WorkOrderAlreadyCompletedError,
    WorkOrderNotFoundError,
)
from app.biomedical.infrastructure.models import (
    CalibrationRecordModel,
    DeviceIncidentModel,
    DeviceRecallModel,
    MaintenanceScheduleModel,
    MedicalDeviceModel,
    SafetyInspectionModel,
    TechnicianModel,
    VendorModel,
    WorkOrderModel,
)
from app.national.events.base import NationalDomainEvent


def _generate_wo_number(db: Session) -> str:
    count = db.query(WorkOrderModel).count() + 1
    return f"WO-{datetime.now(UTC).strftime('%Y%m')}-{count:04d}"


def _generate_cal_number(db: Session) -> str:
    count = db.query(CalibrationRecordModel).count() + 1
    return f"CAL-{datetime.now(UTC).strftime('%Y%m')}-{count:04d}"


class BiomedicalService:
    def __init__(self, db: Session, event_bus: Any = None):
        self.db = db
        self.event_bus = event_bus

    def _emit(self, event: NationalDomainEvent) -> None:
        if self.event_bus:
            self.event_bus.emit(event.event_type, event.__dict__)

    # ---- Device Registry ----

    def register_device(self, data: dict[str, Any]) -> MedicalDevice:
        model = MedicalDeviceModel(**{k: v for k, v in data.items() if hasattr(MedicalDeviceModel, k)})
        if data.get("acquisition_date") and data.get("expected_lifetime_years"):
            model.current_value = data.get("purchase_cost", 0)
        if data.get("requires_pm") and not data.get("next_pm_due"):
            freq = data.get("pm_frequency_days", 180)
            model.next_pm_due = datetime.now(UTC) + timedelta(days=freq)
        if data.get("requires_calibration") and not data.get("next_calibration_due"):
            freq = data.get("calibration_frequency_days", 365)
            model.next_calibration_due = datetime.now(UTC) + timedelta(days=freq)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._device_from_model(model)

    def get_device(self, device_id: str) -> MedicalDevice:
        model = self.db.query(MedicalDeviceModel).filter_by(id=device_id).first()
        if not model or model.is_deleted:
            raise DeviceNotFoundError()
        return self._device_from_model(model)

    def list_devices(self, category: str | None = None, status: str | None = None,
                     facility_id: str | None = None, skip: int = 0, limit: int = 100) -> list[MedicalDevice]:
        query = self.db.query(MedicalDeviceModel).filter(MedicalDeviceModel.is_deleted.isnot(True))
        if category:
            query = query.filter_by(category=category)
        if status:
            query = query.filter_by(status=status)
        if facility_id:
            query = query.filter_by(location_facility_id=facility_id)
        query = query.offset(skip).limit(limit)
        return [self._device_from_model(m) for m in query.all()]

    def update_device_status(self, device_id: str, status: str, reason: str = "") -> MedicalDevice:
        model = self.db.query(MedicalDeviceModel).filter_by(id=device_id).with_for_update().first()
        if not model:
            raise DeviceNotFoundError()
        model.status = status
        model.notes = (model.notes or "") + f"\n[{datetime.now(UTC).isoformat()}] Status: {status}. {reason}"
        model.version = (model.version or 0) + 1
        self.db.commit()
        self.db.refresh(model)
        return self._device_from_model(model)

    def devices_due_for_pm(self, days_ahead: int = 30) -> list[dict]:
        now = datetime.now(UTC)
        due = now + timedelta(days=days_ahead)
        models = self.db.query(MedicalDeviceModel).filter(
            MedicalDeviceModel.requires_pm.is_(True),
            MedicalDeviceModel.next_pm_due <= due,
            MedicalDeviceModel.is_deleted.isnot(True),
        ).all()
        return [{"id": m.id, "device_name": m.device_name, "next_pm_due": m.next_pm_due,
                  "status": m.status, "asset_tag": m.asset_tag} for m in models]

    def devices_due_for_calibration(self, days_ahead: int = 30) -> list[dict]:
        now = datetime.now(UTC)
        due = now + timedelta(days=days_ahead)
        models = self.db.query(MedicalDeviceModel).filter(
            MedicalDeviceModel.requires_calibration.is_(True),
            MedicalDeviceModel.next_calibration_due <= due,
            MedicalDeviceModel.is_deleted.isnot(True),
        ).all()
        return [{"id": m.id, "device_name": m.device_name, "next_calibration_due": m.next_calibration_due,
                  "status": m.status, "asset_tag": m.asset_tag} for m in models]

    # ---- Work Orders ----

    def create_work_order(self, data: dict[str, Any]) -> WorkOrder:
        model = WorkOrderModel(**{k: v for k, v in data.items() if hasattr(WorkOrderModel, k)})
        model.work_order_number = _generate_wo_number(self.db)
        self.db.add(model)
        if model.device_id:
            device = self.db.query(MedicalDeviceModel).filter_by(id=model.device_id).with_for_update().first()
            if device:
                device.status = DeviceStatus.UNDER_MAINTENANCE.value
                device.version = (device.version or 0) + 1
        self.db.commit()
        self.db.refresh(model)
        return self._work_order_from_model(model)

    def get_work_order(self, wo_id: str) -> WorkOrder:
        model = self.db.query(WorkOrderModel).filter_by(id=wo_id).first()
        if not model or model.is_deleted:
            raise WorkOrderNotFoundError()
        return self._work_order_from_model(model)

    def list_work_orders(self, device_id: str | None = None, status: str | None = None,
                         maintenance_type: str | None = None, skip: int = 0, limit: int = 100) -> list[WorkOrder]:
        query = self.db.query(WorkOrderModel).filter(WorkOrderModel.is_deleted.isnot(True))
        if device_id:
            query = query.filter_by(device_id=device_id)
        if status:
            query = query.filter_by(status=status)
        if maintenance_type:
            query = query.filter_by(maintenance_type=maintenance_type)
        query = query.order_by(WorkOrderModel.reported_date.desc()).offset(skip).limit(limit)
        return [self._work_order_from_model(m) for m in query.all()]

    def complete_work_order(self, wo_id: str, data: dict[str, Any]) -> WorkOrder:
        model = self.db.query(WorkOrderModel).filter_by(id=wo_id).with_for_update().first()
        if not model:
            raise WorkOrderNotFoundError()
        if model.status == WorkOrderStatus.COMPLETED.value:
            raise WorkOrderAlreadyCompletedError("Work order is already completed")
        model.status = WorkOrderStatus.COMPLETED.value
        model.completed_at = datetime.now(UTC)
        model.action_taken = data.get("action_taken", model.action_taken or "")
        model.problem_found = data.get("problem_found", model.problem_found or "")
        model.result = data.get("result", model.result or "")
        model.labor_hours = data.get("labor_hours", model.labor_hours)
        model.cost_parts = data.get("cost_parts", model.cost_parts)
        model.cost_labor = data.get("cost_labor", model.cost_labor)
        model.cost_total = (model.cost_parts or 0) + (model.cost_labor or 0)
        model.version = (model.version or 0) + 1
        if model.device_id:
            device = self.db.query(MedicalDeviceModel).filter_by(id=model.device_id).with_for_update().first()
            if device:
                device.status = DeviceStatus.AVAILABLE.value
                device.last_pm_date = datetime.now(UTC)
                if device.pm_frequency_days:
                    device.next_pm_due = datetime.now(UTC) + timedelta(days=device.pm_frequency_days)
                device.version = (device.version or 0) + 1
        self.db.commit()
        self.db.refresh(model)
        return self._work_order_from_model(model)

    # ---- Calibrations ----

    def record_calibration(self, data: dict[str, Any]) -> CalibrationRecord:
        model = CalibrationRecordModel(**{k: v for k, v in data.items() if hasattr(CalibrationRecordModel, k)})
        model.calibration_number = _generate_cal_number(self.db)
        self.db.add(model)
        if model.device_id:
            device = self.db.query(MedicalDeviceModel).filter_by(id=model.device_id).first()
            if device:
                device.last_calibration_date = model.calibration_date
                if model.passed and device.calibration_frequency_days:
                    device.next_calibration_due = model.calibration_date + timedelta(days=device.calibration_frequency_days)
        self.db.commit()
        self.db.refresh(model)
        return CalibrationRecord(id=model.id, device_id=model.device_id, calibration_number=model.calibration_number,
                                  status=model.status, passed=model.passed or False, calibration_date=model.calibration_date)

    # ---- Safety Inspections ----

    def record_safety_inspection(self, data: dict[str, Any]) -> SafetyInspection:
        model = SafetyInspectionModel(**{k: v for k, v in data.items() if hasattr(SafetyInspectionModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return SafetyInspection(id=model.id, device_id=model.device_id, overall_result=model.overall_result,
                                 inspection_date=model.inspection_date, inspected_by=model.inspected_by or "")

    # ---- Device Incidents ----

    def report_incident(self, data: dict[str, Any]) -> DeviceIncident:
        model = DeviceIncidentModel(**{k: v for k, v in data.items() if hasattr(DeviceIncidentModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return DeviceIncident(id=model.id, device_id=model.device_id, incident_type=model.incident_type or "",
                               severity=model.severity or "minor", description=model.description or "")

    def list_incidents(self, device_id: str | None = None, skip: int = 0, limit: int = 100) -> list[DeviceIncident]:
        query = self.db.query(DeviceIncidentModel).filter(DeviceIncidentModel.is_deleted.isnot(True))
        if device_id:
            query = query.filter_by(device_id=device_id)
        query = query.order_by(DeviceIncidentModel.incident_date.desc()).offset(skip).limit(limit)
        return [DeviceIncident(id=m.id, device_id=m.device_id, incident_type=m.incident_type or "",
                                severity=m.severity or "minor", description=m.description or "",
                                status=m.status or "open") for m in query.all()]

    # ---- Recalls ----

    def issue_recall(self, data: dict[str, Any]) -> DeviceRecall:
        model = DeviceRecallModel(**{k: v for k, v in data.items() if hasattr(DeviceRecallModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return DeviceRecall(id=model.id, device_id=model.device_id, recall_class=model.recall_class or "class_ii",
                             recall_reason=model.recall_reason or "", status=model.status or "open")

    # ---- Technicians ----

    def register_technician(self, data: dict[str, Any]) -> Technician:
        model = TechnicianModel(**{k: v for k, v in data.items() if hasattr(TechnicianModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return Technician(id=model.id, full_name=model.full_name, specialization=model.specialization or "")

    def list_technicians(self, available: bool | None = None, skip: int = 0, limit: int = 100) -> list[Technician]:
        query = self.db.query(TechnicianModel).filter(TechnicianModel.is_deleted.isnot(True))
        if available is not None:
            query = query.filter_by(is_available=available)
        return [Technician(id=m.id, full_name=m.full_name, specialization=m.specialization or "",
                           is_available=m.is_available) for m in query.offset(skip).limit(limit).all()]

    # ---- Vendors ----

    def register_vendor(self, data: dict[str, Any]) -> Vendor:
        model = VendorModel(**{k: v for k, v in data.items() if hasattr(VendorModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return Vendor(id=model.id, vendor_name=model.vendor_name, vendor_type=model.vendor_type)

    # ---- Maintenance Schedule ----

    def create_maintenance_schedule(self, data: dict[str, Any]) -> DeviceMaintenanceSchedule:
        model = MaintenanceScheduleModel(**{k: v for k, v in data.items() if hasattr(MaintenanceScheduleModel, k)})
        if not model.next_due_date:
            model.next_due_date = datetime.now(UTC) + timedelta(days=model.frequency_days or 180)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return DeviceMaintenanceSchedule(id=model.id, device_id=model.device_id,
                                          maintenance_type=model.maintenance_type,
                                          frequency_days=model.frequency_days,
                                          next_due_date=model.next_due_date)

    # ---- Dashboard ----

    def get_dashboard_stats(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        total_devices = self.db.query(MedicalDeviceModel).filter(MedicalDeviceModel.is_deleted.isnot(True)).count()
        active_devices = self.db.query(MedicalDeviceModel).filter_by(status="available", is_deleted=False).count()
        maintenance = self.db.query(MedicalDeviceModel).filter(
            MedicalDeviceModel.status.in_(["under_maintenance", "out_of_service"]),
            MedicalDeviceModel.is_deleted.isnot(True),
        ).count()
        overdue_pm = self.db.query(MedicalDeviceModel).filter(
            MedicalDeviceModel.requires_pm.is_(True),
            MedicalDeviceModel.next_pm_due < now,
            MedicalDeviceModel.is_deleted.isnot(True),
        ).count()
        overdue_cal = self.db.query(MedicalDeviceModel).filter(
            MedicalDeviceModel.requires_calibration.is_(True),
            MedicalDeviceModel.next_calibration_due < now,
            MedicalDeviceModel.is_deleted.isnot(True),
        ).count()
        open_work_orders = self.db.query(WorkOrderModel).filter(
            WorkOrderModel.status.in_(["pending", "assigned", "in_progress", "on_hold"]),
        ).count()
        open_incidents = self.db.query(DeviceIncidentModel).filter_by(status="open").count()
        return {
            "total_devices": total_devices, "active_devices": active_devices,
            "under_maintenance": maintenance, "overdue_pm": overdue_pm,
            "overdue_calibration": overdue_cal, "open_work_orders": open_work_orders,
            "open_incidents": open_incidents,
        }

    def _device_from_model(self, m: MedicalDeviceModel) -> MedicalDevice:
        return MedicalDevice(
            id=m.id, device_name=m.device_name, model=m.model or "", manufacturer=m.manufacturer or "",
            serial_number=m.serial_number or "", udi_di=m.udi_di or "", udi_pi=m.udi_pi or "",
            udi_full=m.udi_full or "", asset_tag=m.asset_tag or "", category=m.category or "other",
            risk_class=m.risk_class or "class_i", status=m.status or "available",
            location_facility_id=m.location_facility_id or "", location_department=m.location_department or "",
            location_room=m.location_room or "", owning_department=m.owning_department or "",
            warranty_status=m.warranty_status or "active",
            requires_calibration=m.requires_calibration or False,
            calibration_frequency_days=m.calibration_frequency_days or 365,
            last_calibration_date=m.last_calibration_date, next_calibration_due=m.next_calibration_due,
            requires_pm=m.requires_pm if m.requires_pm is not None else True,
            pm_frequency_days=m.pm_frequency_days or 180,
            last_pm_date=m.last_pm_date, next_pm_due=m.next_pm_due,
            lifecycle_stage=m.lifecycle_stage or "operational",
            vendor_name=m.vendor_name or "", software_version=m.software_version or "",
        )

    def _work_order_from_model(self, m: WorkOrderModel) -> WorkOrder:
        return WorkOrder(
            id=m.id, device_id=m.device_id, device_name=m.device_name or "",
            work_order_number=m.work_order_number or "", maintenance_type=m.maintenance_type or "corrective",
            priority=m.priority or "medium", status=m.status or "pending", title=m.title or "",
            description=m.description or "", reported_by=m.reported_by or "",
            assigned_to=m.assigned_to or "", problem_found=m.problem_found or "",
            action_taken=m.action_taken or "", result=m.result or "", notes=m.notes or "",
        )
