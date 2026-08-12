from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.radiology.enums import DeviceStatus
from app.radiology.models import (
    MPPS,
    DICOMStorage,
    ModalityDevice,
    RadiologyExam,
    RadiologyOrder,
    WorklistEntry,
)

logger = logging.getLogger("gula.radiology.device")

HL7_SIU_STATUS_MAP = {
    "SCHEDULED": "scheduled",
    "ARRIVED": "arrived",
    "CHECKED_IN": "checked_in",
    "STARTED": "in_progress",
    "COMPLETED": "completed",
    "CANCELLED": "cancelled",
    "NO_SHOW": "no_show",
}


# ==============================================================================
# ModalityWorklistService
# ==============================================================================


class ModalityWorklistService:
    def __init__(self, db: Session):
        self.db = db

    def generate_worklist(self, modality_device_id: str) -> list[dict[str, Any]]:
        device = self.db.query(ModalityDevice).filter(
            ModalityDevice.id == modality_device_id,
            ModalityDevice.is_active,
            ~ModalityDevice.is_deleted,
        ).first()
        if not device:
            logger.warning("Worklist requested for unknown/inactive device: %s", modality_device_id)
            return []

        exams = self.db.query(RadiologyExam).filter(
            RadiologyExam.modality == device.modality_type,
            RadiologyExam.status.in_(["scheduled", "checked_in"]),
            ~RadiologyExam.is_deleted,
        ).all()

        worklist: list[dict[str, Any]] = []
        for exam in exams:
            order = None
            if exam.order_id:
                order = self.db.query(RadiologyOrder).filter(RadiologyOrder.id == exam.order_id).first()

            entry = self._build_worklist_entry(device, exam, order)
            self._persist_worklist_entry(device.id, exam, entry)
            worklist.append(entry)

        logger.info("Generated worklist for device %s: %d items", device.device_name, len(worklist))
        return worklist

    def _build_worklist_entry(self, device: ModalityDevice, exam: RadiologyExam, order: RadiologyOrder | None) -> dict[str, Any]:
        return {
            "AccessionNumber": exam.accession_number,
            "PatientID": exam.patient_id,
            "PatientName": "",
            "PatientSex": "",
            "PatientBirthDate": "",
            "RequestedProcedureID": exam.id,
            "RequestedProcedureDescription": exam.exam_name or "",
            "ScheduledProcedureStepStartDate": exam.created_at.strftime("%Y%m%d") if exam.created_at else "",
            "ScheduledProcedureStepStartTime": exam.created_at.strftime("%H%M%S") if exam.created_at else "",
            "ScheduledStationAETitle": device.ae_title or "",
            "ScheduledStationName": device.device_name,
            "Modality": device.modality_type.value.upper(),
            "PerformedStationAETitle": device.ae_title or "",
            "ReferringPhysicianName": "",
            "ClinicalIndication": order.clinical_indication if order else "",
        }

    def _persist_worklist_entry(self, device_id: str, exam: RadiologyExam, entry_data: dict[str, Any]) -> None:
        existing = self.db.query(WorklistEntry).filter(
            WorklistEntry.accession_number == exam.accession_number,
            WorklistEntry.modality_device_id == device_id,
            ~WorklistEntry.is_deleted,
        ).first()
        if existing:
            existing.status = "scheduled"
            existing.updated_at = datetime.now(UTC)
        else:
            entry = WorklistEntry(
                modality_device_id=device_id,
                exam_id=exam.id,
                accession_number=exam.accession_number,
                patient_id=exam.patient_id,
                modality=exam.modality,
                scheduled_datetime=exam.created_at or datetime.now(UTC),
                status="scheduled",
                metadata=entry_data,
            )
            self.db.add(entry)
        self.db.commit()

    def get_worklist_for_device(
        self,
        device_id: str,
        patient_ids: set[str] | None = None,
    ) -> list[WorklistEntry]:
        query = self.db.query(WorklistEntry).filter(
            WorklistEntry.modality_device_id == device_id,
            WorklistEntry.status == "scheduled",
            ~WorklistEntry.is_deleted,
        )
        if patient_ids is not None:
            query = query.filter(WorklistEntry.patient_id.in_(patient_ids))
        return query.order_by(WorklistEntry.scheduled_datetime.asc()).all()

    def process_siu_message(self, hl7_siu: dict[str, Any]) -> bool:
        accession = hl7_siu.get("accession_number", "")
        hl7_status = hl7_siu.get("status", "").upper()
        mapped_status = HL7_SIU_STATUS_MAP.get(hl7_status, "scheduled")

        entry = self.db.query(WorklistEntry).filter(
            WorklistEntry.accession_number == accession,
            ~WorklistEntry.is_deleted,
        ).first()
        if entry:
            entry.status = mapped_status
            entry.updated_at = datetime.now(UTC)
            self.db.commit()
            logger.info("SIU update for %s: %s -> %s", accession, hl7_status, mapped_status)
            return True

        exam = self.db.query(RadiologyExam).filter(
            RadiologyExam.accession_number == accession,
            ~RadiologyExam.is_deleted,
        ).first()
        if exam:
            try:
                exam.status = mapped_status
                self.db.commit()
                logger.info("SIU update for exam %s: %s", accession, mapped_status)
                return True
            except Exception as exc:
                logger.error("SIU update failed: %s", exc)
                return False
        return False


# ==============================================================================
# MPPSHandler
# ==============================================================================


class MPPSHandler:
    def __init__(self, db: Session):
        self.db = db

    def process_mpps(self, mpps_data: dict[str, Any]) -> MPPS | None:
        accession_number = mpps_data.get("accession_number", "")
        mpps_status = mpps_data.get("status", "")

        worklist_entry = self.db.query(WorklistEntry).filter(
            WorklistEntry.accession_number == accession_number,
            ~WorklistEntry.is_deleted,
        ).first()

        exam = self.db.query(RadiologyExam).filter(
            RadiologyExam.accession_number == accession_number,
            ~RadiologyExam.is_deleted,
        ).first()

        mpps = MPPS(
            worklist_entry_id=worklist_entry.id if worklist_entry else None,
            exam_id=exam.id if exam else None,
            status=mpps_status,
            performed_steps=mpps_data.get("performed_steps", []),
            notes=mpps_data.get("notes"),
            metadata=mpps_data.get("metadata", {}),
        )

        if mpps_status == "IN_PROGRESS":
            mpps.started_at = datetime.now(UTC)
        elif mpps_status in ("COMPLETED", "DISCONTINUED"):
            mpps.completed_at = datetime.now(UTC)

        self.db.add(mpps)

        if exam and mpps_status == "COMPLETED":
            exam.status = "completed"
            exam.completed_at = datetime.now(UTC)
            exam.series_count = mpps_data.get("series_count", exam.series_count or 0)
            exam.images_count = mpps_data.get("images_count", exam.images_count or 0)

        if worklist_entry and mpps_status in ("COMPLETED", "DISCONTINUED"):
            worklist_entry.status = "completed" if mpps_status == "COMPLETED" else "discontinued"
            worklist_entry.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(mpps)
        logger.info("MPPS processed for %s: %s", accession_number, mpps_status)
        return mpps

    def get_mpps_by_exam(self, exam_id: str) -> list[MPPS]:
        return self.db.query(MPPS).filter(
            MPPS.exam_id == exam_id,
            ~MPPS.is_deleted,
        ).order_by(MPPS.created_at.desc()).all()


# ==============================================================================
# DeviceMonitoringService
# ==============================================================================


class DeviceMonitoringService:
    def __init__(self, db: Session):
        self.db = db

    def register_device(
        self,
        device_id: str,
        device_name: str,
        modality_type: str,
        device_model: str | None = None,
        manufacturer: str | None = None,
        site_name: str | None = None,
        department_id: str | None = None,
        ip_address: str | None = None,
        ae_title: str | None = None,
        port: int | None = None,
        dicom_protocol: str | None = None,
        software_version: str | None = None,
        serial_number: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ModalityDevice:
        device = ModalityDevice(
            device_id=device_id,
            device_name=device_name,
            device_model=device_model,
            manufacturer=manufacturer,
            modality_type=modality_type.upper(),
            site_name=site_name,
            department_id=department_id,
            ip_address=ip_address,
            ae_title=ae_title,
            port=port,
            dicom_protocol=dicom_protocol,
            is_active=True,
            status=DeviceStatus.OFFLINE,
            software_version=software_version,
            serial_number=serial_number,
            metadata=metadata or {},
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        logger.info("Device registered: %s (%s)", device_name, modality_type)
        return device

    def record_heartbeat(self, device_id: str) -> ModalityDevice | None:
        device = self.db.query(ModalityDevice).filter(
            ModalityDevice.device_id == device_id,
            ~ModalityDevice.is_deleted,
        ).first()
        if not device:
            return None
        device.last_connection = datetime.now(UTC)
        device.status = DeviceStatus.ONLINE
        self.db.commit()
        self.db.refresh(device)
        return device

    def mark_device_offline(self, device_id: str) -> ModalityDevice | None:
        device = self.db.query(ModalityDevice).filter(
            ModalityDevice.device_id == device_id,
            ~ModalityDevice.is_deleted,
        ).first()
        if not device:
            return None
        device.status = DeviceStatus.OFFLINE
        self.db.commit()
        self.db.refresh(device)
        return device

    def update_device_status(self, device_id: str, status: DeviceStatus) -> ModalityDevice | None:
        device = self.db.query(ModalityDevice).filter(
            ModalityDevice.device_id == device_id,
            ~ModalityDevice.is_deleted,
        ).first()
        if not device:
            return None
        device.status = status
        if status == DeviceStatus.ONLINE:
            device.last_connection = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(device)
        return device

    def get_device(self, device_id: str) -> ModalityDevice | None:
        return self.db.query(ModalityDevice).filter(
            ModalityDevice.device_id == device_id,
            ~ModalityDevice.is_deleted,
        ).first()

    def get_device_by_id(self, pk_id: str) -> ModalityDevice | None:
        return self.db.query(ModalityDevice).filter(
            ModalityDevice.id == pk_id,
            ~ModalityDevice.is_deleted,
        ).first()

    def list_devices(self, modality_type: str | None = None, status: str | None = None) -> list[ModalityDevice]:
        q = self.db.query(ModalityDevice).filter(~ModalityDevice.is_deleted)
        if modality_type:
            q = q.filter(ModalityDevice.modality_type == modality_type.upper())
        if status:
            q = q.filter(ModalityDevice.status == status)
        return q.all()

    def get_device_health(self) -> dict[str, Any]:
        total = self.db.query(ModalityDevice).filter(~ModalityDevice.is_deleted).count()
        online = self.db.query(ModalityDevice).filter(
            ModalityDevice.status == DeviceStatus.ONLINE,
            ~ModalityDevice.is_deleted,
        ).count()
        offline = self.db.query(ModalityDevice).filter(
            ModalityDevice.status == DeviceStatus.OFFLINE,
            ~ModalityDevice.is_deleted,
        ).count()
        error = self.db.query(ModalityDevice).filter(
            ModalityDevice.status == DeviceStatus.ERROR,
            ~ModalityDevice.is_deleted,
        ).count()
        maintenance = self.db.query(ModalityDevice).filter(
            ModalityDevice.status == DeviceStatus.MAINTENANCE,
            ~ModalityDevice.is_deleted,
        ).count()
        return {
            "total": total,
            "online": online,
            "offline": offline,
            "error": error,
            "maintenance": maintenance,
            "uptime_pct": round((online / total * 100) if total else 0, 2),
        }

    def detect_stale_devices(self, stale_minutes: int = 10) -> list[ModalityDevice]:
        cutoff = datetime.now(UTC) - __import__("datetime").timedelta(minutes=stale_minutes)
        stale = self.db.query(ModalityDevice).filter(
            ModalityDevice.last_connection < cutoff,
            ModalityDevice.status == DeviceStatus.ONLINE,
            ~ModalityDevice.is_deleted,
        ).all()
        for device in stale:
            device.status = DeviceStatus.OFFLINE
            logger.warning("Device marked offline (stale): %s", device.device_name)
        if stale:
            self.db.commit()
        return stale

    def check_storage_capacity(self, device_id: str, threshold_bytes: int = 1073741824) -> dict[str, Any]:
        total_stored = self.db.query(DICOMStorage).filter(
            ~DICOMStorage.is_deleted,
        ).with_entities(DICOMStorage.file_size).all()
        used = sum(r[0] or 0 for r in total_stored)
        return {
            "device_id": device_id,
            "used_bytes": used,
            "threshold_bytes": threshold_bytes,
            "exceeded": used > threshold_bytes,
        }


# ==============================================================================
# DicomGatewayService
# ==============================================================================


class DicomGatewayService:
    def __init__(
        self,
        db: Session,
        gateway_endpoint: str = "http://pacs-gateway:8042",
        ae_title: str = "GULA_GATEWAY",
    ):
        self.db = db
        self.gateway_endpoint = gateway_endpoint
        self.ae_title = ae_title

    def proxy_c_find(self, target_device_id: str, query: dict[str, Any]) -> list[dict[str, Any]]:
        device = self.db.query(ModalityDevice).filter(
            ModalityDevice.id == target_device_id,
            ModalityDevice.is_active,
            ~ModalityDevice.is_deleted,
        ).first()
        if not device:
            logger.warning("C-FIND proxy: target device %s not found", target_device_id)
            return []
        logger.info("Proxying C-FIND to %s [%s]", device.device_name, device.ip_address)
        return []

    def proxy_c_move(self, target_device_id: str, study_uid: str, destination_ae: str) -> bool:
        device = self.db.query(ModalityDevice).filter(
            ModalityDevice.id == target_device_id,
            ModalityDevice.is_active,
            ~ModalityDevice.is_deleted,
        ).first()
        if not device:
            return False
        logger.info("Proxying C-MOVE %s from %s to %s", study_uid, device.device_name, destination_ae)
        return True

    def proxy_c_store(self, target_device_id: str, dicom_data: bytes) -> bool:
        device = self.db.query(ModalityDevice).filter(
            ModalityDevice.id == target_device_id,
            ModalityDevice.is_active,
            ~ModalityDevice.is_deleted,
        ).first()
        if not device:
            return False
        logger.info("Proxying C-STORE %d bytes to %s", len(dicom_data), device.device_name)
        return True

    def get_device_info(self, device_id: str) -> dict[str, Any] | None:
        device = self.db.query(ModalityDevice).filter(
            ModalityDevice.id == device_id,
            ~ModalityDevice.is_deleted,
        ).first()
        if not device:
            return None
        return {
            "device_id": device.device_id,
            "device_name": device.device_name,
            "ae_title": device.ae_title,
            "ip_address": device.ip_address,
            "port": device.port,
            "modality": device.modality_type.value if hasattr(device.modality_type, "value") else str(device.modality_type),
            "status": device.status.value if hasattr(device.status, "value") else str(device.status),
            "is_active": device.is_active,
        }
