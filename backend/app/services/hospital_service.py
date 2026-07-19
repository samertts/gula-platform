"""Hospital service — business logic for the National HIS Platform."""

from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC

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
    Unit,
)
from ..models.organization import Appointment
from ..models.patient import Patient
from ..services.audit_service import log_action


class HospitalService:
    """Encapsulates all hospital-domain business logic."""

    # ── Hospital CRUD ──────────────────────────────────────────────────────────

    @staticmethod
    def create_hospital(
        db: Session,
        lab_id: int,
        user_id: int,
        data: dict[str, Any],
    ) -> HospitalMaster:
        existing = db.query(HospitalMaster).filter(
            HospitalMaster.lab_id == lab_id,
            HospitalMaster.code == data["code"],
            ~HospitalMaster.is_deleted,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Hospital with code '{data['code']}' already exists",
                detail_ar=f"مستشفى برمز '{data['code']}' موجود بالفعل",
            )
        hospital = HospitalMaster(lab_id=lab_id, created_by=user_id, **data)
        db.add(hospital)
        db.flush()
        log_action(db, "hospital.create", hospital.id, lab_id, user_id, data)
        return hospital

    @staticmethod
    def update_hospital(
        db: Session,
        hospital_id: int,
        lab_id: int,
        user_id: int,
        data: dict[str, Any],
    ) -> HospitalMaster:
        hospital = db.query(HospitalMaster).filter(
            HospitalMaster.id == hospital_id,
            HospitalMaster.lab_id == lab_id,
            ~HospitalMaster.is_deleted,
        ).first()
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        for k, v in data.items():
            setattr(hospital, k, v)
        hospital.updated_by = user_id
        db.flush()
        log_action(db, "hospital.update", hospital_id, lab_id, user_id, data)
        return hospital

    @staticmethod
    def deactivate_hospital(
        db: Session, hospital_id: int, lab_id: int, user_id: int,
    ) -> None:
        hospital = db.query(HospitalMaster).filter(
            HospitalMaster.id == hospital_id,
            HospitalMaster.lab_id == lab_id,
            ~HospitalMaster.is_deleted,
        ).first()
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        hospital.is_active = False
        hospital.updated_by = user_id
        db.flush()
        log_action(db, "hospital.deactivate", hospital_id, lab_id, user_id)

    @staticmethod
    def get_hospital(db: Session, hospital_id: int, lab_id: int) -> HospitalMaster:
        hospital = db.query(HospitalMaster).filter(
            HospitalMaster.id == hospital_id,
            HospitalMaster.lab_id == lab_id,
            ~HospitalMaster.is_deleted,
        ).first()
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
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
        q = db.query(model).filter(model.id == entity_id, model.lab_id == lab_id, not model.is_deleted)
        if parent_filter is not None:
            q = q.filter(parent_filter)
        entity = q.first()
        if not entity:
            raise HTTPException(status_code=404, detail=f"{model.__tablename__} not found")
        return entity

    # ── Campus CRUD ────────────────────────────────────────────────────────────

    @staticmethod
    def create_campus(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> Campus:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        campus = Campus(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(campus)
        db.flush()
        log_action(db, "campus.create", campus.id, lab_id, user_id, data)
        return campus

    @staticmethod
    def list_campuses(db: Session, lab_id: int, hospital_id: int) -> list[Campus]:
        return db.query(Campus).filter(
            Campus.hospital_id == hospital_id, Campus.lab_id == lab_id, ~Campus.is_deleted,
        ).all()

    # ── Building CRUD ──────────────────────────────────────────────────────────

    @staticmethod
    def create_building(db: Session, lab_id: int, user_id: int, campus_id: int, data: dict) -> Building:
        HospitalService._get_entity(db, Campus, campus_id, lab_id)
        building = Building(lab_id=lab_id, created_by=user_id, campus_id=campus_id, **data)
        db.add(building)
        db.flush()
        return building

    @staticmethod
    def list_buildings(db: Session, lab_id: int, campus_id: int) -> list[Building]:
        return db.query(Building).filter(
            Building.campus_id == campus_id, Building.lab_id == lab_id, ~Building.is_deleted,
        ).all()

    # ── Floor CRUD ─────────────────────────────────────────────────────────────

    @staticmethod
    def create_floor(db: Session, lab_id: int, user_id: int, building_id: int, data: dict) -> Floor:
        HospitalService._get_entity(db, Building, building_id, lab_id)
        floor = Floor(lab_id=lab_id, created_by=user_id, building_id=building_id, **data)
        db.add(floor)
        db.flush()
        return floor

    @staticmethod
    def list_floors(db: Session, lab_id: int, building_id: int) -> list[Floor]:
        return db.query(Floor).filter(
            Floor.building_id == building_id, Floor.lab_id == lab_id, ~Floor.is_deleted,
        ).all()

    # ── HospitalDepartment CRUD ────────────────────────────────────────────────────────

    @staticmethod
    def create_department(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> HospitalDepartment:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        if data.get("parent_id"):
            HospitalService._get_entity(db, HospitalDepartment, data["parent_id"], lab_id, HospitalDepartment.hospital_id == hospital_id)
        dept = HospitalDepartment(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(dept)
        db.flush()
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
    def create_clinic(db: Session, lab_id: int, user_id: int, department_id: int, data: dict) -> Clinic:
        dept = HospitalService._get_entity(db, HospitalDepartment, department_id, lab_id)
        data.setdefault("hospital_id", dept.hospital_id)
        clinic = Clinic(lab_id=lab_id, created_by=user_id, department_id=department_id, **data)
        db.add(clinic)
        db.flush()
        return clinic

    @staticmethod
    def list_clinics(db: Session, lab_id: int, department_id: int | None = None) -> list[Clinic]:
        q = db.query(Clinic).filter(Clinic.lab_id == lab_id, ~Clinic.is_deleted)
        if department_id is not None:
            q = q.filter(Clinic.department_id == department_id)
        return q.all()

    # ── Room CRUD ──────────────────────────────────────────────────────────────

    @staticmethod
    def create_room(db: Session, lab_id: int, user_id: int, department_id: int, data: dict) -> Room:
        HospitalService._get_entity(db, HospitalDepartment, department_id, lab_id)
        room = Room(lab_id=lab_id, created_by=user_id, department_id=department_id, **data)
        db.add(room)
        db.flush()
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
    def create_bed(db: Session, lab_id: int, user_id: int, room_id: int, data: dict) -> Bed:
        HospitalService._get_entity(db, Room, room_id, lab_id)
        bed = Bed(lab_id=lab_id, created_by=user_id, room_id=room_id, **data)
        db.add(bed)
        db.flush()
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
        db: Session, lab_id: int, user_id: int, bed_id: int, patient_id: int,
        reason: str | None = None, diagnosis: str | None = None,
    ) -> Bed:
        bed = HospitalService._get_entity(db, Bed, bed_id, lab_id)
        patient = db.query(Patient).filter(
            Patient.id == patient_id, Patient.lab_id == lab_id,
        ).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        if bed.status != "available":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Bed is currently {bed.status}",
                detail_ar=f"السرير حالياً {bed.status}",
            )
        bed.status = "occupied"
        bed.current_patient_id = patient_id
        assignment = BedAssignment(
            lab_id=lab_id, created_by=user_id,
            bed_id=bed_id, patient_id=patient_id,
            reason=reason, diagnosis=diagnosis,
            admission_date=datetime.now(UTC),
        )
        db.add(assignment)
        db.flush()
        log_action(db, "bed.assign", bed_id, lab_id, user_id, {
            "patient_id": patient_id, "reason": reason,
        })
        return bed

    @staticmethod
    def discharge_bed(
        db: Session, lab_id: int, user_id: int, bed_id: int,
        discharge_reason: str | None = None,
    ) -> Bed:
        bed = HospitalService._get_entity(db, Bed, bed_id, lab_id)
        if bed.status != "occupied":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bed is not currently occupied",
                detail_ar="السرير غير مشغول حالياً",
            )
        active_assignment = db.query(BedAssignment).filter(
            BedAssignment.bed_id == bed_id,
            BedAssignment.discharge_date.is_(None),
        ).first()
        if active_assignment:
            active_assignment.discharge_date = datetime.now(UTC)
            active_assignment.discharge_reason = discharge_reason
            active_assignment.discharged_by = user_id
        bed.status = "cleaning"
        bed.current_patient_id = None
        db.flush()
        log_action(db, "bed.discharge", bed_id, lab_id, user_id, {
            "discharge_reason": discharge_reason,
        })
        return bed

    @staticmethod
    def transfer_bed(
        db: Session, lab_id: int, user_id: int,
        from_bed_id: int, to_bed_id: int,
        reason: str | None = None,
    ) -> dict[str, Any]:
        source = HospitalService.discharge_bed(db, lab_id, user_id, from_bed_id, reason)
        target = HospitalService._get_entity(db, Bed, to_bed_id, lab_id)
        if target.status != "available":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Target bed is {target.status}",
            )
        patient_id = source.current_patient_id
        target.status = "occupied"
        target.current_patient_id = patient_id
        assignment = BedAssignment(
            lab_id=lab_id, created_by=user_id,
            bed_id=to_bed_id, patient_id=patient_id,
            reason=reason or "Transferred",
            admission_date=datetime.now(UTC),
        )
        db.add(assignment)
        db.flush()
        return {"from_bed": from_bed_id, "to_bed": to_bed_id, "patient_id": patient_id}

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
    def create_unit(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> Unit:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        unit = Unit(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(unit)
        db.flush()
        return unit

    @staticmethod
    def list_units(db: Session, lab_id: int, hospital_id: int) -> list[Unit]:
        return db.query(Unit).filter(
            Unit.hospital_id == hospital_id, Unit.lab_id == lab_id, ~Unit.is_deleted,
        ).all()

    # ── Operation Theater CRUD ─────────────────────────────────────────────────

    @staticmethod
    def create_ot(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> OperationTheater:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        ot = OperationTheater(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(ot)
        db.flush()
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
    def create_equipment(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> MedicalEquipment:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        equip = MedicalEquipment(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(equip)
        db.flush()
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
    def create_cost_center(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> CostCenter:
        HospitalService.get_hospital(db, hospital_id, lab_id)
        cc = CostCenter(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)
        db.add(cc)
        db.flush()
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
                )
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
        db: Session, lab_id: int, user_id: int, data: dict[str, Any],
    ) -> Appointment:
        apt = Appointment(lab_id=lab_id, **data)
        db.add(apt)
        db.flush()
        log_action(db, "appointment.create", apt.id, lab_id, user_id, data)
        return apt
