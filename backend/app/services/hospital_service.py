"""Hospital service — business logic for the National HIS Platform."""

from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.domain.exceptions import ConflictError, NotFoundError

from ..hospital.models import (
    Bed,
    BedAssignment,
    Building,
    Campus,
    Clinic,
    CostCenter,
    Floor,
    HospitalDepartment,
    HospitalMaster,
    MedicalEquipment,
    OperationTheater,
    Room,
    SurgicalSafetyChecklist,
    Unit,
)
from ..models.patient import Patient
from ..national.domain.appointment import Appointment
from ..services.audit_service import log_action

_BED_TRANSITIONS: dict[str, set[str]] = {
    "available": {"occupied", "reserved", "maintenance"},
    "occupied": {"cleaning"},
    "reserved": {"available", "occupied"},
    "cleaning": {"available", "maintenance"},
    "maintenance": {"available"},
}

_THEATER_TRANSITIONS: dict[str, set[str]] = {
    "available": {"in_use", "maintenance"},
    "in_use": {"cleaning"},
    "cleaning": {"available", "maintenance"},
    "maintenance": {"available"},
}


class HospitalService:
    """Encapsulates all hospital-domain business logic."""

    # ── Hospital CRUD ──────────────────────────────────────────────────────────

    @staticmethod
    def create_hospital(
        db: Session,
        lab_id: int,
        user_id: int,
        data: dict[str, Any],
        *,
        actor_role: str,
    ) -> HospitalMaster:
        existing = db.query(HospitalMaster).filter(
            HospitalMaster.lab_id == lab_id,
            HospitalMaster.code == data["code"],
            ~HospitalMaster.is_deleted,
        ).first()
        if existing:
            raise ConflictError(f"Hospital with code '{data['code']}' already exists")
        hospital = HospitalMaster(lab_id=lab_id, created_by=user_id, **data)
        db.add(hospital)
        db.flush()
        # These arguments were passed positionally against a signature of
        # (db, action, resource_type, resource_id, user_id, user_role, lab_id,
        # details), so resource_type received the hospital's id, resource_id
        # received the lab_id, lab_id was never recorded at all, and the payload
        # dict landed in user_role -- a varchar column, which psycopg2 refused
        # with "can't adapt type 'dict'". Every call to this route was a 500.
        log_action(
            db,
            action="hospital.create",
            resource_type="hospital",
            resource_id=hospital.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        # get_db() yields, rolls back on exception and closes -- it never commits.
        # Without this the flush above is discarded when the request ends, and the
        # route returns a populated 200 for a write that never persisted.
        db.commit()
        return hospital

    @staticmethod
    def update_hospital(
        db: Session,
        hospital_id: int,
        lab_id: int,
        user_id: int,
        data: dict[str, Any],
        *,
        actor_role: str,
    ) -> HospitalMaster:
        hospital = db.query(HospitalMaster).filter(
            HospitalMaster.id == hospital_id,
            HospitalMaster.lab_id == lab_id,
            ~HospitalMaster.is_deleted,
        ).first()
        if not hospital:
            raise NotFoundError("Hospital not found")
        for k, v in data.items():
            setattr(hospital, k, v)
        hospital.updated_by = user_id
        db.flush()
        log_action(
            db,
            action="hospital.update",
            resource_type="hospital",
            resource_id=hospital_id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        db.commit()
        return hospital

    @staticmethod
    def deactivate_hospital(
        db: Session, hospital_id: int, lab_id: int, user_id: int, *, actor_role: str,
    ) -> None:
        hospital = db.query(HospitalMaster).filter(
            HospitalMaster.id == hospital_id,
            HospitalMaster.lab_id == lab_id,
            ~HospitalMaster.is_deleted,
        ).first()
        if not hospital:
            raise NotFoundError("Hospital not found")
        hospital.is_active = False
        hospital.updated_by = user_id
        db.flush()
        log_action(
            db,
            action="hospital.deactivate",
            resource_type="hospital",
            resource_id=hospital_id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
        )
        db.commit()

    @staticmethod
    def get_hospital(db: Session, hospital_id: int, lab_id: int) -> HospitalMaster:
        hospital = db.query(HospitalMaster).filter(
            HospitalMaster.id == hospital_id,
            HospitalMaster.lab_id == lab_id,
            ~HospitalMaster.is_deleted,
        ).first()
        if not hospital:
            raise NotFoundError("Hospital not found")
        return hospital

    @staticmethod
    def list_hospitals(
        db: Session, lab_id: int, skip: int = 0, limit: int = 50,
    ) -> list[HospitalMaster]:
        return db.query(HospitalMaster).filter(
            HospitalMaster.lab_id == lab_id,
            ~HospitalMaster.is_deleted,
        ).offset(skip).limit(limit).all()

    # ── Nested entity helpers ──────────────────────────────────────────────────

    @staticmethod
    def _get_entity(db: Session, model, entity_id: int, lab_id: int, parent_filter=None):
        # ``not model.is_deleted`` is Python's ``not`` on an InstrumentedAttribute: it
        # evaluates to the literal False, which SQLAlchemy folds the whole conjunction
        # into, compiling to ``WHERE false`` and matching nothing at all.
        q = db.query(model).filter(model.id == entity_id, model.lab_id == lab_id, ~model.is_deleted)
        if parent_filter is not None:
            q = q.filter(parent_filter)
        entity = q.first()
        if not entity:
            raise NotFoundError(f"{model.__tablename__} not found")
        return entity

    # ── Campus CRUD ────────────────────────────────────────────────────────────

    @staticmethod
    def create_campus(
        db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict, *, actor_role: str,
    ) -> Campus:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        campus = Campus(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(campus)
        db.flush()
        log_action(
            db,
            action="campus.create",
            resource_type="hospital_campus",
            resource_id=campus.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        db.commit()
        return campus

    @staticmethod
    def list_campuses(db: Session, lab_id: int, hospital_id: int) -> list[Campus]:
        return db.query(Campus).filter(
            Campus.hospital_id == hospital_id, Campus.lab_id == lab_id, ~Campus.is_deleted,
        ).all()

    # ── Building CRUD ──────────────────────────────────────────────────────────

    @staticmethod
    def create_building(
        db: Session, lab_id: int, user_id: int, campus_id: int, data: dict, *, actor_role: str,
    ) -> Building:
        HospitalService._get_entity(db, Campus, campus_id, lab_id)
        building = Building(lab_id=lab_id, created_by=user_id, campus_id=campus_id, **data)
        db.add(building)
        db.flush()
        log_action(
            db,
            action="hospital.building.create",
            resource_type="hospital_building",
            resource_id=building.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        # get_db() never commits on success (it yields, rolls back on exception,
        # then closes), so a flush alone is discarded when the request ends.
        db.commit()
        return building

    @staticmethod
    def list_buildings(db: Session, lab_id: int, campus_id: int) -> list[Building]:
        return db.query(Building).filter(
            Building.campus_id == campus_id, Building.lab_id == lab_id, ~Building.is_deleted,
        ).all()

    # ── Floor CRUD ─────────────────────────────────────────────────────────────

    @staticmethod
    def create_floor(
        db: Session, lab_id: int, user_id: int, building_id: int, data: dict, *, actor_role: str,
    ) -> Floor:
        HospitalService._get_entity(db, Building, building_id, lab_id)
        floor = Floor(lab_id=lab_id, created_by=user_id, building_id=building_id, **data)
        db.add(floor)
        db.flush()
        log_action(
            db,
            action="hospital.floor.create",
            resource_type="hospital_floor",
            resource_id=floor.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        # get_db() never commits on success (it yields, rolls back on exception,
        # then closes), so a flush alone is discarded when the request ends.
        db.commit()
        return floor

    @staticmethod
    def list_floors(db: Session, lab_id: int, building_id: int) -> list[Floor]:
        return db.query(Floor).filter(
            Floor.building_id == building_id, Floor.lab_id == lab_id, ~Floor.is_deleted,
        ).all()

    # ── HospitalDepartment CRUD ────────────────────────────────────────────────────────

    @staticmethod
    def create_department(
        db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict, *, actor_role: str,
    ) -> HospitalDepartment:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        if data.get("parent_id"):
            HospitalService._get_entity(db, HospitalDepartment, data["parent_id"], lab_id, HospitalDepartment.hospital_id == hospital_id)
        dept = HospitalDepartment(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(dept)
        db.flush()
        log_action(
            db,
            action="hospital.department.create",
            resource_type="hospital_department",
            resource_id=dept.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        # get_db() never commits on success (it yields, rolls back on exception,
        # then closes), so a flush alone is discarded when the request ends.
        db.commit()
        return dept

    @staticmethod
    def list_departments(db: Session, lab_id: int, hospital_id: int, parent_id: int | None = None) -> list[HospitalDepartment]:
        q = db.query(HospitalDepartment).filter(
            HospitalDepartment.hospital_id == hospital_id, HospitalDepartment.lab_id == lab_id, ~HospitalDepartment.is_deleted,
        )
        if parent_id is not None:
            q = q.filter(HospitalDepartment.parent_id == parent_id)
        return q.all()

    # ── Clinic CRUD ────────────────────────────────────────────────────────────

    @staticmethod
    def create_clinic(
        db: Session, lab_id: int, user_id: int, department_id: int, data: dict, *, actor_role: str,
    ) -> Clinic:
        dept = HospitalService._get_entity(db, HospitalDepartment, department_id, lab_id)
        data.setdefault("hospital_id", dept.hospital_id)
        clinic = Clinic(lab_id=lab_id, created_by=user_id, department_id=department_id, **data)
        db.add(clinic)
        db.flush()
        log_action(
            db,
            action="hospital.clinic.create",
            resource_type="hospital_clinic",
            resource_id=clinic.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        # get_db() never commits on success (it yields, rolls back on exception,
        # then closes), so a flush alone is discarded when the request ends.
        db.commit()
        return clinic

    @staticmethod
    def list_clinics(db: Session, lab_id: int, department_id: int | None = None) -> list[Clinic]:
        q = db.query(Clinic).filter(Clinic.lab_id == lab_id, ~Clinic.is_deleted)
        if department_id is not None:
            q = q.filter(Clinic.department_id == department_id)
        return q.all()

    # ── Room CRUD ──────────────────────────────────────────────────────────────

    @staticmethod
    def create_room(
        db: Session, lab_id: int, user_id: int, department_id: int, data: dict, *, actor_role: str,
    ) -> Room:
        HospitalService._get_entity(db, HospitalDepartment, department_id, lab_id)
        room = Room(lab_id=lab_id, created_by=user_id, department_id=department_id, **data)
        db.add(room)
        db.flush()
        log_action(
            db,
            action="hospital.room.create",
            resource_type="hospital_room",
            resource_id=room.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        # get_db() never commits on success (it yields, rolls back on exception,
        # then closes), so a flush alone is discarded when the request ends.
        db.commit()
        return room

    @staticmethod
    def list_rooms(
        db: Session, lab_id: int, department_id: int | None = None,
        room_type: str | None = None,
    ) -> list[Room]:
        q = db.query(Room).filter(Room.lab_id == lab_id, ~Room.is_deleted)
        if department_id is not None:
            q = q.filter(Room.department_id == department_id)
        if room_type is not None:
            q = q.filter(Room.room_type == room_type)
        return q.all()

    # ── Bed CRUD + Assignment ──────────────────────────────────────────────────

    @staticmethod
    def create_bed(
        db: Session, lab_id: int, user_id: int, room_id: int, data: dict, *, actor_role: str,
    ) -> Bed:
        HospitalService._get_entity(db, Room, room_id, lab_id)
        bed = Bed(lab_id=lab_id, created_by=user_id, room_id=room_id, **data)
        db.add(bed)
        db.flush()
        log_action(
            db,
            action="hospital.bed.create",
            resource_type="hospital_bed",
            resource_id=bed.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        # get_db() never commits on success (it yields, rolls back on exception,
        # then closes), so a flush alone is discarded when the request ends.
        db.commit()
        return bed

    @staticmethod
    def list_beds(
        db: Session, lab_id: int, room_id: int | None = None,
        status: str | None = None, bed_type: str | None = None,
    ) -> list[Bed]:
        q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)
        if room_id is not None:
            q = q.filter(Bed.room_id == room_id)
        if status is not None:
            q = q.filter(Bed.status == status)
        if bed_type is not None:
            q = q.filter(Bed.bed_type == bed_type)
        return q.all()

    @staticmethod
    def assign_bed(
        db: Session,
        lab_id: int,
        user_id: int,
        bed_id: int,
        patient_id: int,
        *,
        actor_role: str,
        expected_version: int,
        reason: str | None = None,
        diagnosis: str | None = None,
    ) -> Bed:
        bed = db.query(Bed).filter(
            Bed.id == bed_id,
            Bed.lab_id == lab_id,
            ~Bed.is_deleted,
        ).with_for_update().first()
        if not bed:
            raise NotFoundError("Bed not found")
        if bed.version != expected_version:
            raise ConflictError("Bed version conflict")
        patient = db.query(Patient).filter(
            Patient.id == patient_id, Patient.lab_id == lab_id,
        ).first()
        if not patient:
            raise NotFoundError("Patient not found")
        if "occupied" not in _BED_TRANSITIONS.get(bed.status, set()):
            raise ConflictError(f"Bed cannot transition from {bed.status} to occupied")
        state_before = bed.status
        bed.status = "occupied"
        bed.current_patient_id = patient_id
        bed.version += 1
        assignment = BedAssignment(
            lab_id=lab_id, created_by=user_id,
            bed_id=bed_id, patient_id=patient_id,
            reason=reason, diagnosis=diagnosis,
            admission_date=datetime.now(UTC),
        )
        db.add(assignment)
        db.flush()
        log_action(
            db,
            action="bed.assign",
            resource_type="hospital_bed",
            resource_id=str(bed_id),
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details={
                "patient_id": patient_id,
                "reason": reason,
                "state_before": state_before,
                "state_after": bed.status,
                "version": bed.version,
            },
        )
        # Deliberately NO db.commit() here. This method runs inside
        # _run_hospital_command's ClinicalCommandGuard, which claims a receipt,
        # runs this mutation, records completion and only then commits -- and
        # rolls back if completion fails. Committing here would publish the
        # clinical change before its receipt was recorded, and the guard's
        # rollback could no longer undo it.
        return bed

    @staticmethod
    def discharge_bed(
        db: Session,
        lab_id: int,
        user_id: int,
        bed_id: int,
        *,
        actor_role: str,
        expected_version: int,
        discharge_reason: str | None = None,
    ) -> Bed:
        bed = db.query(Bed).filter(
            Bed.id == bed_id,
            Bed.lab_id == lab_id,
            ~Bed.is_deleted,
        ).with_for_update().first()
        if not bed:
            raise NotFoundError("Bed not found")
        if bed.version != expected_version:
            raise ConflictError("Bed version conflict")
        if "cleaning" not in _BED_TRANSITIONS.get(bed.status, set()):
            raise ConflictError("Bed is not currently occupied")
        active_assignment = db.query(BedAssignment).filter(
            BedAssignment.bed_id == bed_id,
            BedAssignment.discharge_date.is_(None),
        ).with_for_update().first()
        if active_assignment:
            active_assignment.discharge_date = datetime.now(UTC)
            active_assignment.discharge_reason = discharge_reason
            active_assignment.discharged_by = user_id
        state_before = bed.status
        bed.status = "cleaning"
        bed.current_patient_id = None
        bed.version += 1
        db.flush()
        log_action(
            db,
            action="bed.discharge",
            resource_type="hospital_bed",
            resource_id=str(bed_id),
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details={
                "discharge_reason": discharge_reason,
                "state_before": state_before,
                "state_after": bed.status,
                "version": bed.version,
            },
        )
        # Deliberately NO db.commit() here. This method runs inside
        # _run_hospital_command's ClinicalCommandGuard, which claims a receipt,
        # runs this mutation, records completion and only then commits -- and
        # rolls back if completion fails. Committing here would publish the
        # clinical change before its receipt was recorded, and the guard's
        # rollback could no longer undo it.
        return bed

    @staticmethod
    def transfer_bed(
        db: Session,
        lab_id: int,
        user_id: int,
        from_bed_id: int,
        to_bed_id: int,
        *,
        actor_role: str,
        from_expected_version: int,
        to_expected_version: int,
        reason: str | None = None,
    ) -> dict[str, Any]:
        if from_bed_id == to_bed_id:
            raise ConflictError("Source and target beds must be different")
        beds = db.query(Bed).filter(
            Bed.id.in_([from_bed_id, to_bed_id]),
            Bed.lab_id == lab_id,
            ~Bed.is_deleted,
        ).order_by(Bed.id).with_for_update().all()
        by_id = {bed.id: bed for bed in beds}
        source, target = by_id.get(from_bed_id), by_id.get(to_bed_id)
        if source is None or target is None:
            raise NotFoundError("Bed not found")
        if source.version != from_expected_version or target.version != to_expected_version:
            raise ConflictError("Bed version conflict")
        if source.status != "occupied" or source.current_patient_id is None:
            raise ConflictError("Source bed is not currently occupied")
        if "occupied" not in _BED_TRANSITIONS.get(target.status, set()):
            raise ConflictError(f"Target bed cannot transition from {target.status} to occupied")
        patient_id = source.current_patient_id
        active_assignment = db.query(BedAssignment).filter(
            BedAssignment.bed_id == source.id,
            BedAssignment.discharge_date.is_(None),
        ).with_for_update().first()
        if active_assignment is None:
            raise ConflictError("Source bed has no active assignment")
        now = datetime.now(UTC)
        active_assignment.discharge_date = now
        active_assignment.discharge_reason = reason or "Transferred"
        active_assignment.discharged_by = user_id
        source.status = "cleaning"
        source.current_patient_id = None
        source.version += 1
        target.status = "occupied"
        target.current_patient_id = patient_id
        target.version += 1
        db.add(BedAssignment(
            lab_id=lab_id,
            created_by=user_id,
            bed_id=to_bed_id,
            patient_id=patient_id,
            reason=reason or "Transferred",
            admission_date=now,
        ))
        db.flush()
        log_action(
            db,
            action="bed.transfer",
            resource_type="hospital_bed",
            resource_id=str(from_bed_id),
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details={
                "to_bed_id": to_bed_id,
                "patient_id": patient_id,
                "reason": reason,
                "source_state_after": source.status,
                "target_state_after": target.status,
                "source_version": source.version,
                "target_version": target.version,
            },
        )
        # Deliberately NO db.commit() here. This method runs inside
        # _run_hospital_command's ClinicalCommandGuard, which claims a receipt,
        # runs this mutation, records completion and only then commits -- and
        # rolls back if completion fails. Committing here would publish the
        # clinical change before its receipt was recorded, and the guard's
        # rollback could no longer undo it.
        return {
            "from_bed": from_bed_id,
            "to_bed": to_bed_id,
            "patient_id": patient_id,
            "from_version": source.version,
            "to_version": target.version,
        }

    @staticmethod
    def update_operation_theater_status(
        db: Session,
        lab_id: int,
        user_id: int,
        ot_id: int,
        *,
        actor_role: str,
        expected_version: int,
        next_status: str,
        surgery_id: int | None = None,
    ) -> OperationTheater:
        theater = db.query(OperationTheater).filter(
            OperationTheater.id == ot_id,
            OperationTheater.lab_id == lab_id,
            ~OperationTheater.is_deleted,
        ).with_for_update().first()
        if theater is None:
            raise NotFoundError("Operation theater not found")
        if theater.version != expected_version:
            raise ConflictError("Operation theater version conflict")
        if next_status not in _THEATER_TRANSITIONS.get(theater.status, set()):
            raise ConflictError(f"Illegal operation theater transition: {theater.status} -> {next_status}")
        if next_status == "in_use" and surgery_id is None:
            raise ConflictError("A surgery identifier is required before a theater enters use")
        if next_status != "in_use" and surgery_id is not None:
            raise ConflictError("A surgery identifier is only accepted when a theater enters use")
        if next_status == "in_use":
            checklist = db.query(SurgicalSafetyChecklist).filter(
                SurgicalSafetyChecklist.lab_id == lab_id,
                SurgicalSafetyChecklist.operation_theater_id == ot_id,
                SurgicalSafetyChecklist.surgery_id == surgery_id,
                SurgicalSafetyChecklist.completed_at.isnot(None),
                ~SurgicalSafetyChecklist.is_deleted,
            ).with_for_update().first()
            if checklist is None:
                raise ConflictError("A completed surgical safety checklist is required before theater use")
        state_before = theater.status
        theater.status = next_status
        theater.current_surgery_id = surgery_id if next_status == "in_use" else None
        theater.version += 1
        theater.updated_by = user_id
        db.flush()
        log_action(
            db,
            action="operation_theater.status_changed",
            resource_type="hospital_operation_theater",
            resource_id=str(ot_id),
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details={
                "state_before": state_before,
                "state_after": next_status,
                "surgery_id": surgery_id,
                "version": theater.version,
            },
        )
        # Deliberately NO db.commit() here. This method runs inside
        # _run_hospital_command's ClinicalCommandGuard, which claims a receipt,
        # runs this mutation, records completion and only then commits -- and
        # rolls back if completion fails. Committing here would publish the
        # clinical change before its receipt was recorded, and the guard's
        # rollback could no longer undo it.
        return theater

    @staticmethod
    def complete_surgical_safety_checklist(
        db: Session,
        lab_id: int,
        user_id: int,
        data: dict[str, Any],
        *,
        actor_role: str,
    ) -> SurgicalSafetyChecklist:
        theater_id = int(data["operation_theater_id"])
        theater = db.query(OperationTheater).filter(
            OperationTheater.id == theater_id,
            OperationTheater.lab_id == lab_id,
            ~OperationTheater.is_deleted,
        ).with_for_update().first()
        if theater is None:
            raise NotFoundError("Operation theater not found")
        if theater.status != "available":
            raise ConflictError("Safety checklist may only be completed for an available theater")
        required_checks = (
            "patient_identity_confirmed",
            "procedure_confirmed",
            "site_marked",
            "consent_verified",
            "anesthesia_assessment_complete",
            "allergy_reviewed",
            "antibiotic_prophylaxis_confirmed",
            "blood_products_confirmed",
            "imaging_reviewed",
            "team_time_out_completed",
        )
        missing = [field for field in required_checks if not data.get(field, False)]
        if missing:
            raise ConflictError(f"Surgical safety checklist is incomplete: {', '.join(missing)}")
        laterality = str(data.get("planned_laterality") or "not_applicable")
        if laterality not in {"left", "right", "bilateral", "midline", "not_applicable"}:
            raise ConflictError("Unsupported surgical laterality")
        checklist = SurgicalSafetyChecklist(
            lab_id=lab_id,
            created_by=user_id,
            operation_theater_id=theater_id,
            surgery_id=int(data["surgery_id"]),
            patient_id=int(data["patient_id"]),
            procedure_name=str(data["procedure_name"]).strip(),
            procedure_site=str(data["procedure_site"]).strip(),
            planned_laterality=laterality,
            completed_at=datetime.now(UTC),
            completed_by=user_id,
            notes=data.get("notes"),
            **dict.fromkeys(required_checks, True),
        )
        if not checklist.procedure_name or not checklist.procedure_site:
            raise ConflictError("Procedure name and site are required")
        db.add(checklist)
        db.flush()
        log_action(
            db,
            action="surgery.safety_checklist.completed",
            resource_type="hospital_surgical_safety_checklist",
            resource_id=str(checklist.id),
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details={
                "operation_theater_id": theater_id,
                "surgery_id": checklist.surgery_id,
                "patient_id": checklist.patient_id,
                "procedure_site": checklist.procedure_site,
            },
        )
        # Deliberately NO db.commit() here. This method runs inside
        # _run_hospital_command's ClinicalCommandGuard, which claims a receipt,
        # runs this mutation, records completion and only then commits -- and
        # rolls back if completion fails. Committing here would publish the
        # clinical change before its receipt was recorded, and the guard's
        # rollback could no longer undo it.
        return checklist

    @staticmethod
    def bed_occupancy_stats(db: Session, lab_id: int, hospital_id: int | None = None) -> dict[str, Any]:
        q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)
        if hospital_id is not None:
            q = q.join(Room).join(HospitalDepartment).filter(HospitalDepartment.hospital_id == hospital_id)
        total = q.count()
        available = q.filter(Bed.status == "available").count()
        occupied = q.filter(Bed.status == "occupied").count()
        reserved = q.filter(Bed.status == "reserved").count()
        maintenance = q.filter(Bed.status == "maintenance").count()
        cleaning = q.filter(Bed.status == "cleaning").count()
        occupancy_rate = round((occupied / total) * 100, 1) if total > 0 else 0.0
        return {
            "total": total,
            "available": available,
            "occupied": occupied,
            "reserved": reserved,
            "maintenance": maintenance,
            "cleaning": cleaning,
            "occupancy_rate": occupancy_rate,
        }

    # ── Unit CRUD ──────────────────────────────────────────────────────────────

    @staticmethod
    def create_unit(
        db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict, *, actor_role: str,
    ) -> Unit:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        unit = Unit(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(unit)
        db.flush()
        log_action(
            db,
            action="hospital.unit.create",
            resource_type="hospital_unit",
            resource_id=unit.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        # get_db() never commits on success (it yields, rolls back on exception,
        # then closes), so a flush alone is discarded when the request ends.
        db.commit()
        return unit

    @staticmethod
    def list_units(db: Session, lab_id: int, hospital_id: int) -> list[Unit]:
        return db.query(Unit).filter(
            Unit.hospital_id == hospital_id, Unit.lab_id == lab_id, ~Unit.is_deleted,
        ).all()

    # ── Operation Theater CRUD ─────────────────────────────────────────────────

    @staticmethod
    def create_ot(
        db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict, *, actor_role: str,
    ) -> OperationTheater:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        ot = OperationTheater(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(ot)
        db.flush()
        log_action(
            db,
            action="hospital.operation_theater.create",
            resource_type="hospital_operation_theater",
            resource_id=ot.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        # get_db() never commits on success (it yields, rolls back on exception,
        # then closes), so a flush alone is discarded when the request ends.
        db.commit()
        return ot

    @staticmethod
    def list_operation_theaters(db: Session, lab_id: int, hospital_id: int) -> list[OperationTheater]:
        return db.query(OperationTheater).filter(
            OperationTheater.hospital_id == hospital_id,
            OperationTheater.lab_id == lab_id,
            ~OperationTheater.is_deleted,
        ).all()

    # ── Medical Equipment CRUD ─────────────────────────────────────────────────

    @staticmethod
    def create_equipment(
        db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict, *, actor_role: str,
    ) -> MedicalEquipment:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        equip = MedicalEquipment(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(equip)
        db.flush()
        log_action(
            db,
            action="hospital.equipment.create",
            resource_type="hospital_equipment",
            resource_id=equip.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        # get_db() never commits on success (it yields, rolls back on exception,
        # then closes), so a flush alone is discarded when the request ends.
        db.commit()
        return equip

    @staticmethod
    def list_equipment(
        db: Session, lab_id: int, hospital_id: int,
        category: str | None = None, status: str | None = None,
    ) -> list[MedicalEquipment]:
        q = db.query(MedicalEquipment).filter(
            MedicalEquipment.hospital_id == hospital_id,
            MedicalEquipment.lab_id == lab_id,
            ~MedicalEquipment.is_deleted,
        )
        if category:
            q = q.filter(MedicalEquipment.category == category)
        if status:
            q = q.filter(MedicalEquipment.status == status)
        return q.all()

    # ── Cost Center CRUD ───────────────────────────────────────────────────────

    @staticmethod
    def create_cost_center(
        db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict, *, actor_role: str,
    ) -> CostCenter:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        cc = CostCenter(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(cc)
        db.flush()
        log_action(
            db,
            action="hospital.cost_center.create",
            resource_type="hospital_cost_center",
            resource_id=cc.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        # get_db() never commits on success (it yields, rolls back on exception,
        # then closes), so a flush alone is discarded when the request ends.
        db.commit()
        return cc

    @staticmethod
    def list_cost_centers(db: Session, lab_id: int, hospital_id: int) -> list[CostCenter]:
        return db.query(CostCenter).filter(
            CostCenter.hospital_id == hospital_id,
            CostCenter.lab_id == lab_id,
            ~CostCenter.is_deleted,
        ).all()

    # ── Dashboard / KPIs ───────────────────────────────────────────────────────

    @staticmethod
    def dashboard(db: Session, lab_id: int, hospital_id: int) -> dict[str, Any]:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        dept_count = db.query(func.count(HospitalDepartment.id)).filter(
            HospitalDepartment.hospital_id == hospital_id,
            HospitalDepartment.lab_id == lab_id,
            ~HospitalDepartment.is_deleted,
        ).scalar() or 0
        clinic_count = db.query(func.count(Clinic.id)).filter(
            Clinic.hospital_id == hospital_id,
            ~Clinic.is_deleted,
        ).scalar() or 0
        room_count = db.query(func.count(Room.id)).filter(
            Room.department_id.in_(
                db.query(HospitalDepartment.id).filter(
                    HospitalDepartment.hospital_id == hospital_id,
                    HospitalDepartment.lab_id == lab_id,
                    ~HospitalDepartment.is_deleted,
                ),
            ),
            ~Room.is_deleted,
        ).scalar() or 0
        bed_count = db.query(func.count(Bed.id)).filter(
            Bed.lab_id == lab_id,
            ~Bed.is_deleted,
        ).scalar() or 0
        occupied_beds = db.query(func.count(Bed.id)).filter(
            Bed.lab_id == lab_id,
            Bed.status == "occupied",
            ~Bed.is_deleted,
        ).scalar() or 0
        equipment_count = db.query(func.count(MedicalEquipment.id)).filter(
            MedicalEquipment.hospital_id == hospital_id,
            MedicalEquipment.lab_id == lab_id,
            ~MedicalEquipment.is_deleted,
        ).scalar() or 0
        operational_equipment = db.query(func.count(MedicalEquipment.id)).filter(
            MedicalEquipment.hospital_id == hospital_id,
            MedicalEquipment.lab_id == lab_id,
            MedicalEquipment.status == "operational",
            ~MedicalEquipment.is_deleted,
        ).scalar() or 0
        ot_count = db.query(func.count(OperationTheater.id)).filter(
            OperationTheater.hospital_id == hospital_id,
            OperationTheater.lab_id == lab_id,
            ~OperationTheater.is_deleted,
        ).scalar() or 0
        available_ot = db.query(func.count(OperationTheater.id)).filter(
            OperationTheater.hospital_id == hospital_id,
            OperationTheater.lab_id == lab_id,
            OperationTheater.status == "available",
            ~OperationTheater.is_deleted,
        ).scalar() or 0
        return {
            "hospital_id": hospital_id,
            "departments": dept_count,
            "clinics": clinic_count,
            "rooms": room_count,
            "beds": {"total": bed_count, "occupied": occupied_beds},
            "equipment": {"total": equipment_count, "operational": operational_equipment},
            "operation_theaters": {"total": ot_count, "available": available_ot},
        }

    # ── Appointment management (reuses existing Appointment model) ─────────────

    @staticmethod
    def list_appointments(
        db: Session, lab_id: int, hospital_id: int | None = None,
        patient_id: int | None = None, skip: int = 0, limit: int = 50,
    ) -> list[Appointment]:
        q = db.query(Appointment).filter(Appointment.lab_id == lab_id)
        if patient_id is not None:
            q = q.filter(Appointment.patient_id == patient_id)
        return q.order_by(Appointment.scheduled_date.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def create_appointment(
        db: Session, lab_id: int, user_id: int, data: dict[str, Any], *, actor_role: str,
    ) -> Appointment:
        apt = Appointment(lab_id=lab_id, **data)
        db.add(apt)
        db.flush()
        log_action(
            db,
            action="appointment.create",
            resource_type="hospital_appointment",
            resource_id=apt.id,
            user_id=user_id,
            user_role=actor_role,
            lab_id=lab_id,
            details=data,
        )
        db.commit()
        return apt
