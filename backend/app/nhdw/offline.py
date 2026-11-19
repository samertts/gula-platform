from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.orm import Session

from app._compat import UTC
from shared.models import serialize_columns

from ..database import Base
from ..services.audit_service import log_action


def _get_model_class(table_name: str):
    from .models import (
        Admission,
        CarePlan,
        ClinicalTask,
        Discharge,
        HospitalAlert,
        HospitalMessage,
        QueueEntry,
        ResourceSchedule,
        ShiftReport,
        TelemedicineSession,
        Transfer,
        WaitingListEntry,
        WardRound,
    )
    mapping = {
        "nhdw_admissions": Admission,
        "nhdw_discharges": Discharge,
        "nhdw_transfers": Transfer,
        "nhdw_queue_entries": QueueEntry,
        "nhdw_waiting_list_entries": WaitingListEntry,
        "nhdw_clinical_tasks": ClinicalTask,
        "nhdw_ward_rounds": WardRound,
        "nhdw_care_plans": CarePlan,
        "nhdw_hospital_alerts": HospitalAlert,
        "nhdw_hospital_messages": HospitalMessage,
        "nhdw_telemedicine_sessions": TelemedicineSession,
        "nhdw_resource_schedules": ResourceSchedule,
        "nhdw_shift_reports": ShiftReport,
    }
    return mapping.get(table_name)


class SyncStatus:
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"


class OfflineChange(Base):
    __tablename__ = "nhdw_offline_changes"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(26), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    data = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    device_id = Column(String(100), nullable=False, index=True)
    sync_status = Column(String(20), nullable=False, default=SyncStatus.PENDING, index=True)


class SyncBatch:
    def __init__(
        self,
        changes: list[OfflineChange],
        device_id: str,
        last_sync_timestamp: datetime | None = None,
        batch_id: str | None = None,
    ):
        self.changes = changes
        self.device_id = device_id
        self.last_sync_timestamp = last_sync_timestamp or datetime.now(UTC)
        self.batch_id = batch_id or str(int(datetime.now(UTC).timestamp()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "device_id": self.device_id,
            "last_sync_timestamp": self.last_sync_timestamp.isoformat(),
            "changes": [
                {
                    "id": c.id,
                    "entity_type": c.entity_type,
                    "entity_id": c.entity_id,
                    "action": c.action,
                    "data": c.data,
                    "timestamp": c.timestamp.isoformat(),
                }
                for c in self.changes
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SyncBatch:
        changes_dicts = d.get("changes", [])
        changes = []
        for cd in changes_dicts:
            change = OfflineChange(
                id=cd.get("id", 0),
                entity_type=cd["entity_type"],
                entity_id=cd["entity_id"],
                action=cd["action"],
                data=cd.get("data"),
                timestamp=datetime.fromisoformat(cd["timestamp"]) if cd.get("timestamp") else datetime.now(UTC),
                device_id=d["device_id"],
                sync_status=SyncStatus.PENDING,
            )
            changes.append(change)
        return cls(
            changes=changes,
            device_id=d["device_id"],
            last_sync_timestamp=datetime.fromisoformat(d["last_sync_timestamp"]) if d.get("last_sync_timestamp") else None,
            batch_id=d.get("batch_id"),
        )


class OfflineService:

    @staticmethod
    def record_change(
        db: Session,
        entity_type: str,
        entity_id: str,
        action: str,
        data: dict[str, Any] | None,
        device_id: str,
    ) -> OfflineChange:
        change = OfflineChange(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            data=data,
            device_id=device_id,
            sync_status=SyncStatus.PENDING,
        )
        db.add(change)
        db.flush()
        return change

    @staticmethod
    def prepare_batch(db: Session, device_id: str, last_sync: datetime | None = None) -> SyncBatch:
        q = db.query(OfflineChange).filter(
            OfflineChange.device_id == device_id,
            OfflineChange.sync_status == SyncStatus.PENDING,
        )
        if last_sync is not None:
            q = q.filter(OfflineChange.timestamp > last_sync)
        changes = q.order_by(OfflineChange.timestamp.asc()).all()
        return SyncBatch(
            changes=changes,
            device_id=device_id,
            last_sync_timestamp=last_sync or datetime.now(UTC),
        )

    @staticmethod
    def apply_batch(db: Session, lab_id: int, user_id: int, batch: SyncBatch) -> dict[str, Any]:
        applied = 0
        conflicts = 0
        for change in batch.changes:
            model = _get_model_class(change.entity_type)
            if model is None:
                continue
            existing = db.query(model).filter(
                model.id == change.entity_id,
                model.lab_id == lab_id,
            ).first()
            if existing and change.action == "upsert":
                remote_updated = change.data.get("updated_at", "")
                local_updated = existing.updated_at.isoformat() if existing.updated_at else ""
                if remote_updated and local_updated and remote_updated > local_updated:
                    for k, v in change.data.items():
                        if k not in ("id", "lab_id", "created_at", "created_by", "version"):
                            setattr(existing, k, v)
                    existing.updated_by = user_id
                    db.flush()
                    applied += 1
                elif remote_updated and local_updated and remote_updated <= local_updated:
                    conflicts += 1
                else:
                    for k, v in change.data.items():
                        if k not in ("id", "lab_id", "created_at", "created_by", "version"):
                            setattr(existing, k, v)
                    existing.updated_by = user_id
                    db.flush()
                    applied += 1
            elif not existing and change.action == "upsert":
                data = {k: v for k, v in change.data.items() if k not in ("id",)}
                data.setdefault("lab_id", lab_id)
                data.setdefault("created_by", user_id)
                instance = model(**data, id=change.entity_id)
                db.add(instance)
                db.flush()
                applied += 1
            elif existing and change.action == "delete":
                existing.soft_delete()
                db.flush()
                applied += 1
            change_in_db = db.query(OfflineChange).filter(OfflineChange.id == change.id).first()
            if change_in_db:
                change_in_db.sync_status = SyncStatus.CONFLICT if conflicts > 0 else SyncStatus.SYNCED
        db.flush()
        log_action(db, "nhdw.sync.apply_batch", 0, lab_id, user_id, {
            "applied": applied, "conflicts": conflicts, "device_id": batch.device_id,
        })
        return {"applied": applied, "conflicts": conflicts}

    @staticmethod
    def resolve_conflict(
        db: Session,
        lab_id: int,
        user_id: int,
        local_data: dict[str, Any],
        remote_data: dict[str, Any],
    ) -> dict[str, Any]:
        local_ts = local_data.get("updated_at", "")
        remote_ts = remote_data.get("updated_at", "")
        winner = remote_data if remote_ts >= local_ts else local_data
        log_action(db, "nhdw.sync.resolve_conflict", 0, lab_id, user_id, {
            "strategy": "last_write_wins",
            "local_timestamp": local_ts,
            "remote_timestamp": remote_ts,
            "winner": "remote" if remote_ts >= local_ts else "local",
        })
        return winner

    @staticmethod
    def delta_sync(
        db: Session,
        lab_id: int,
        device_id: str,
        entity_types: list[str] | None = None,
        since: datetime | None = None,
    ) -> SyncBatch:
        tables = entity_types or [
            "nhdw_admissions", "nhdw_discharges", "nhdw_transfers",
            "nhdw_queue_entries", "nhdw_waiting_list_entries",
            "nhdw_clinical_tasks", "nhdw_ward_rounds", "nhdw_care_plans",
            "nhdw_hospital_alerts", "nhdw_hospital_messages",
            "nhdw_telemedicine_sessions", "nhdw_resource_schedules",
            "nhdw_shift_reports",
        ]
        sync_from = since or datetime(2000, 1, 1, tzinfo=UTC)
        changes: list[OfflineChange] = []
        for table_name in tables:
            model = _get_model_class(table_name)
            if model is None:
                continue
            records = db.query(model).filter(
                model.lab_id == lab_id,
                model.updated_at >= sync_from,
            ).all()
            for rec in records:
                # Resolved through the mapper, not through `col.name`: a column named
                # `metadata` is mapped as `metadata_`, and reading it by its physical
                # name yields the declarative MetaData registry instead of the value.
                # All 13 tables synced here carry that column. See IA-005.
                data = serialize_columns(rec)
                change = OfflineChange(
                    entity_type=table_name,
                    entity_id=rec.id,
                    action="upsert",
                    data=data,
                    device_id=device_id,
                    sync_status=SyncStatus.PENDING,
                    timestamp=rec.updated_at or datetime.now(UTC),
                )
                changes.append(change)
        return SyncBatch(
            changes=changes,
            device_id=device_id,
            last_sync_timestamp=datetime.now(UTC),
        )
