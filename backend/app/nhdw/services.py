from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC

from ..hospital.models import Bed, Room
from ..hospital.models import HospitalDepartment as Department
from ..models.patient import Patient
from ..services.audit_service import log_action
from ..services.patient_service import create_patient as _create_patient
from ..services.patient_service import get_patient_by_id
from ..services.patient_service import list_patients as _list_patients
from .enums import AdmissionType, AlertSeverity, ClinicalTaskStatus, QueueStatus
from .models import (
    Admission,
    CarePlan,
    ClinicalTask,
    DashboardConfiguration,
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


class NHDWService:

    @staticmethod
    def register_patient(db: Session, lab_id: int, user_id: int, data: dict) -> Patient:
        data.setdefault("lab_id", lab_id)
        return _create_patient(db, lab_id, user_id, data)

    @staticmethod
    def get_patient(db: Session, patient_id: int, lab_id: int) -> Patient:
        patient = get_patient_by_id(db, patient_id, lab_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient

    @staticmethod
    def search_patients(db: Session, lab_id: int, search: str | None = None, skip: int = 0, limit: int = 50) -> dict:
        return _list_patients(db, lab_id, search, skip, limit)

    @staticmethod
    def create_admission(db: Session, lab_id: int, user_id: int, data: dict) -> Admission:
        patient_id = data.get("patient_id")
        bed_id = data.get("bed_id")
        if bed_id:
            bed = db.query(Bed).filter(
                Bed.id == bed_id, Bed.lab_id == lab_id, ~Bed.is_deleted,
            ).first()
            if not bed:
                raise HTTPException(
                    status_code=404, detail="Bed not found",
                    detail_ar="السرير غير موجود",
                )
            if bed.status != "available":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Bed is currently {bed.status}",
                    detail_ar=f"السرير حالياً {bed.status}",
                )
            bed.status = "occupied"
            bed.current_patient_id = patient_id
        if data.get("department_id"):
            dept = db.query(Department).filter(
                Department.id == data["department_id"],
                Department.lab_id == lab_id,
                ~Department.is_deleted,
            ).first()
            if not dept:
                raise HTTPException(status_code=404, detail="Department not found")
        admission = Admission(lab_id=lab_id, created_by=user_id, **data)
        db.add(admission)
        db.flush()
        log_action(db, "nhdw.admission.create", admission.id, lab_id, user_id, data)
        return admission

    @staticmethod
    def get_admission(db: Session, admission_id: str, lab_id: int) -> Admission:
        admission = db.query(Admission).filter(
            Admission.id == admission_id,
            Admission.lab_id == lab_id,
            ~Admission.is_deleted,
        ).first()
        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")
        return admission

    @staticmethod
    def update_admission(db: Session, lab_id: int, user_id: int, admission_id: str, data: dict) -> Admission:
        admission = NHDWService.get_admission(db, admission_id, lab_id)
        for k, v in data.items():
            if k == "metadata":
                k = "metadata_"
            if hasattr(admission, k):
                setattr(admission, k, v)
        admission.updated_by = user_id
        db.flush()
        log_action(db, "nhdw.admission.update", admission_id, lab_id, user_id, data)
        return admission

    @staticmethod
    def list_admissions(
        db: Session, lab_id: int, department_id: int | None = None,
        status: str | None = None, skip: int = 0, limit: int = 50,
    ) -> list[Admission]:
        q = db.query(Admission).filter(
            Admission.lab_id == lab_id, ~Admission.is_deleted,
        )
        if department_id is not None:
            q = q.filter(Admission.department_id == department_id)
        if status is not None:
            q = q.filter(Admission.status == status)
        return q.order_by(Admission.admission_date.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_active_admissions(db: Session, lab_id: int, department_id: int | None = None) -> list[Admission]:
        q = db.query(Admission).filter(
            Admission.lab_id == lab_id,
            ~Admission.is_deleted,
            Admission.discharge_date.is_(None),
        )
        if department_id is not None:
            q = q.filter(Admission.department_id == department_id)
        return q.order_by(Admission.admission_date.desc()).all()

    @staticmethod
    def get_admission_history(db: Session, patient_id: int, lab_id: int) -> list[Admission]:
        return db.query(Admission).filter(
            Admission.patient_id == patient_id,
            Admission.lab_id == lab_id,
            ~Admission.is_deleted,
        ).order_by(Admission.admission_date.desc()).all()

    @staticmethod
    def discharge_patient(
        db: Session, lab_id: int, user_id: int, admission_id: str, data: dict,
    ) -> Discharge:
        admission = NHDWService.get_admission(db, admission_id, lab_id)
        if admission.discharge_date is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient already discharged",
                detail_ar="المريض تم تخريجه بالفعل",
            )
        if admission.bed_id:
            bed = db.query(Bed).filter(
                Bed.id == admission.bed_id, Bed.lab_id == lab_id,
            ).first()
            if bed:
                bed.status = "cleaning"
                bed.current_patient_id = None
        admission.discharge_date = data.get("discharge_date", datetime.now(UTC))
        discharge = Discharge(
            lab_id=lab_id, created_by=user_id,
            admission_id=admission_id, patient_id=admission.patient_id,
            discharged_by=user_id, **data,
        )
        db.add(discharge)
        db.flush()
        log_action(db, "nhdw.discharge.create", discharge.id, lab_id, user_id, data)
        return discharge

    @staticmethod
    def transfer_patient(
        db: Session, lab_id: int, user_id: int, admission_id: str, data: dict,
    ) -> Transfer:
        admission = NHDWService.get_admission(db, admission_id, lab_id)
        if admission.discharge_date is not None:
            raise HTTPException(status_code=409, detail="Admission already discharged")
        to_dept = db.query(Department).filter(
            Department.id == data["to_department_id"],
            Department.lab_id == lab_id,
            ~Department.is_deleted,
        ).first()
        if not to_dept:
            raise HTTPException(status_code=404, detail="Target department not found")
        from_room_id = admission.room_id
        from_bed_id = admission.bed_id
        if data.get("to_bed_id"):
            new_bed = db.query(Bed).filter(Bed.id == data["to_bed_id"]).first()
            if new_bed and new_bed.status == "available":
                if from_bed_id:
                    old_bed = db.query(Bed).filter(Bed.id == from_bed_id).first()
                    if old_bed:
                        old_bed.status = "available"
                        old_bed.current_patient_id = None
                new_bed.status = "occupied"
                new_bed.current_patient_id = admission.patient_id
                admission.bed_id = data["to_bed_id"]
        admission.department_id = data["to_department_id"]
        admission.room_id = data.get("to_room_id", from_room_id)
        transfer = Transfer(
            lab_id=lab_id, created_by=user_id,
            patient_id=admission.patient_id,
            from_department_id=admission.department_id,
            to_department_id=data["to_department_id"],
            from_room_id=from_room_id, to_room_id=data.get("to_room_id"),
            from_bed_id=from_bed_id, to_bed_id=data.get("to_bed_id"),
            from_doctor_id=data.get("from_doctor_id"),
            to_doctor_id=data.get("to_doctor_id"),
            reason=data.get("reason", "Transfer"),
            clinical_summary=data.get("clinical_summary"),
            transferred_by=user_id,
            transfer_type=data.get("transfer_type", "intra_hospital"),
            status="completed",
        )
        db.add(transfer)
        db.flush()
        log_action(db, "nhdw.transfer.create", transfer.id, lab_id, user_id, data)
        return transfer

    @staticmethod
    def add_queue_entry(db: Session, lab_id: int, user_id: int, data: dict) -> QueueEntry:
        entry = QueueEntry(lab_id=lab_id, created_by=user_id, **data)
        db.add(entry)
        db.flush()
        log_action(db, "nhdw.queue.add", entry.id, lab_id, user_id, data)
        return entry

    @staticmethod
    def list_queue(
        db: Session, lab_id: int, department_id: int | None = None,
        queue_date: date | None = None, status: QueueStatus | None = None,
        skip: int = 0, limit: int = 50,
    ) -> list[QueueEntry]:
        q = db.query(QueueEntry).filter(
            QueueEntry.lab_id == lab_id, ~QueueEntry.is_deleted,
        )
        if department_id is not None:
            q = q.filter(QueueEntry.department_id == department_id)
        if queue_date is not None:
            q = q.filter(QueueEntry.queue_date == queue_date)
        else:
            q = q.filter(QueueEntry.queue_date == date.today())
        if status is not None:
            q = q.filter(QueueEntry.status == status)
        return q.order_by(QueueEntry.priority, QueueEntry.check_in_time).offset(skip).limit(limit).all()

    @staticmethod
    def serve_queue_entry(db: Session, lab_id: int, user_id: int, entry_id: str) -> QueueEntry:
        return NHDWService._update_queue_status(db, lab_id, user_id, entry_id, QueueStatus.SEEN)

    @staticmethod
    def complete_queue_entry(db: Session, lab_id: int, user_id: int, entry_id: str) -> QueueEntry:
        return NHDWService._update_queue_status(db, lab_id, user_id, entry_id, QueueStatus.COMPLETED)

    @staticmethod
    def no_show_queue_entry(db: Session, lab_id: int, user_id: int, entry_id: str) -> QueueEntry:
        return NHDWService._update_queue_status(db, lab_id, user_id, entry_id, QueueStatus.NO_SHOW)

    @staticmethod
    def cancel_queue_entry(db: Session, lab_id: int, user_id: int, entry_id: str) -> QueueEntry:
        return NHDWService._update_queue_status(db, lab_id, user_id, entry_id, QueueStatus.CANCELLED)

    @staticmethod
    def _update_queue_status(db: Session, lab_id: int, user_id: int, entry_id: str, status: QueueStatus) -> QueueEntry:
        entry = db.query(QueueEntry).filter(
            QueueEntry.id == entry_id,
            QueueEntry.lab_id == lab_id,
            ~QueueEntry.is_deleted,
        ).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Queue entry not found")
        now = datetime.now(UTC)
        if status == QueueStatus.SEEN and not entry.seen_time:
            entry.seen_time = now
        elif status == QueueStatus.COMPLETED:
            entry.completed_time = now
            if entry.check_in_time and entry.completed_time:
                diff = (entry.completed_time - entry.check_in_time).total_seconds() / 60.0
                entry.total_wait_minutes = int(diff)
        entry.status = status
        db.flush()
        log_action(db, "nhdw.queue.status", entry_id, lab_id, user_id, {"status": status.value})
        return entry

    @staticmethod
    def get_wait_times(db: Session, lab_id: int, department_id: int | None = None) -> dict:
        q = db.query(QueueEntry).filter(
            QueueEntry.lab_id == lab_id,
            ~QueueEntry.is_deleted,
            QueueEntry.status.in_([QueueStatus.COMPLETED, QueueStatus.SEEN]),
            QueueEntry.check_in_time.isnot(None),
        )
        if department_id is not None:
            q = q.filter(QueueEntry.department_id == department_id)
        entries = q.all()
        if not entries:
            return {"average_wait_minutes": 0, "total_served": 0}
        waits = []
        for e in entries:
            end = e.completed_time or e.seen_time
            if end and e.check_in_time:
                waits.append(int((end - e.check_in_time).total_seconds() / 60.0))
        avg = round(sum(waits) / len(waits), 1) if waits else 0
        return {"average_wait_minutes": avg, "total_served": len(waits)}

    @staticmethod
    def add_waiting_list(db: Session, lab_id: int, user_id: int, data: dict) -> WaitingListEntry:
        entry = WaitingListEntry(lab_id=lab_id, created_by=user_id, **data)
        db.add(entry)
        db.flush()
        log_action(db, "nhdw.waiting_list.add", entry.id, lab_id, user_id, data)
        return entry

    @staticmethod
    def list_waiting_list(
        db: Session, lab_id: int, department_id: int | None = None,
        status: str | None = None, skip: int = 0, limit: int = 50,
    ) -> list[WaitingListEntry]:
        q = db.query(WaitingListEntry).filter(
            WaitingListEntry.lab_id == lab_id, ~WaitingListEntry.is_deleted,
        )
        if department_id is not None:
            q = q.filter(WaitingListEntry.department_id == department_id)
        if status is not None:
            q = q.filter(WaitingListEntry.status == status)
        return q.order_by(WaitingListEntry.priority, WaitingListEntry.listed_date).offset(skip).limit(limit).all()

    @staticmethod
    def convert_waiting_to_admission(db: Session, lab_id: int, user_id: int, entry_id: str, data: dict) -> Admission:
        entry = db.query(WaitingListEntry).filter(
            WaitingListEntry.id == entry_id,
            WaitingListEntry.lab_id == lab_id,
            ~WaitingListEntry.is_deleted,
        ).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Waiting list entry not found")
        data.setdefault("patient_id", entry.patient_id)
        data.setdefault("department_id", entry.department_id)
        data.setdefault("admission_type", AdmissionType.ELECTIVE)
        admission = NHDWService.create_admission(db, lab_id, user_id, data)
        entry.status = "served"
        db.flush()
        log_action(db, "nhdw.waiting_list.convert", entry_id, lab_id, user_id, {"admission_id": admission.id})
        return admission

    @staticmethod
    def create_clinical_task(db: Session, lab_id: int, user_id: int, data: dict) -> ClinicalTask:
        task = ClinicalTask(lab_id=lab_id, created_by=user_id, assigned_by=user_id, **data)
        db.add(task)
        db.flush()
        log_action(db, "nhdw.task.create", task.id, lab_id, user_id, data)
        return task

    @staticmethod
    def update_clinical_task(db: Session, lab_id: int, user_id: int, task_id: str, data: dict) -> ClinicalTask:
        task = db.query(ClinicalTask).filter(
            ClinicalTask.id == task_id,
            ClinicalTask.lab_id == lab_id,
            ~ClinicalTask.is_deleted,
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Clinical task not found")
        for k, v in data.items():
            if hasattr(task, k):
                setattr(task, k, v)
        task.updated_by = user_id
        db.flush()
        log_action(db, "nhdw.task.update", task_id, lab_id, user_id, data)
        return task

    @staticmethod
    def assign_clinical_task(db: Session, lab_id: int, user_id: int, task_id: str, assign_to: int) -> ClinicalTask:
        task = db.query(ClinicalTask).filter(
            ClinicalTask.id == task_id,
            ClinicalTask.lab_id == lab_id,
            ~ClinicalTask.is_deleted,
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Clinical task not found")
        task.assigned_to = assign_to
        task.status = ClinicalTaskStatus.ASSIGNED
        task.updated_by = user_id
        db.flush()
        log_action(db, "nhdw.task.assign", task_id, lab_id, user_id, {"assigned_to": assign_to})
        return task

    @staticmethod
    def complete_clinical_task(db: Session, lab_id: int, user_id: int, task_id: str) -> ClinicalTask:
        task = db.query(ClinicalTask).filter(
            ClinicalTask.id == task_id,
            ClinicalTask.lab_id == lab_id,
            ~ClinicalTask.is_deleted,
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Clinical task not found")
        task.status = ClinicalTaskStatus.COMPLETED
        task.completed_at = datetime.now(UTC)
        task.completed_by = user_id
        db.flush()
        log_action(db, "nhdw.task.complete", task_id, lab_id, user_id)
        return task

    @staticmethod
    def defer_clinical_task(db: Session, lab_id: int, user_id: int, task_id: str) -> ClinicalTask:
        task = db.query(ClinicalTask).filter(
            ClinicalTask.id == task_id,
            ClinicalTask.lab_id == lab_id,
            ~ClinicalTask.is_deleted,
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Clinical task not found")
        task.status = ClinicalTaskStatus.DEFERRED
        task.updated_by = user_id
        db.flush()
        return task

    @staticmethod
    def list_clinical_tasks(
        db: Session, lab_id: int, assigned_to: int | None = None,
        status: ClinicalTaskStatus | None = None,
        patient_id: int | None = None, skip: int = 0, limit: int = 50,
    ) -> list[ClinicalTask]:
        q = db.query(ClinicalTask).filter(
            ClinicalTask.lab_id == lab_id, ~ClinicalTask.is_deleted,
        )
        if assigned_to is not None:
            q = q.filter(ClinicalTask.assigned_to == assigned_to)
        if status is not None:
            q = q.filter(ClinicalTask.status == status)
        if patient_id is not None:
            q = q.filter(ClinicalTask.patient_id == patient_id)
        return q.order_by(ClinicalTask.due_date.asc().nullslast()).offset(skip).limit(limit).all()

    @staticmethod
    def get_tasks_by_patient(db: Session, patient_id: int, lab_id: int) -> list[ClinicalTask]:
        return db.query(ClinicalTask).filter(
            ClinicalTask.patient_id == patient_id,
            ClinicalTask.lab_id == lab_id,
            ~ClinicalTask.is_deleted,
        ).order_by(ClinicalTask.created_at.desc()).all()

    @staticmethod
    def get_tasks_by_nurse(db: Session, assigned_to: int, lab_id: int) -> list[ClinicalTask]:
        return db.query(ClinicalTask).filter(
            ClinicalTask.assigned_to == assigned_to,
            ClinicalTask.lab_id == lab_id,
            ~ClinicalTask.is_deleted,
        ).order_by(ClinicalTask.due_date.asc().nullslast()).all()

    @staticmethod
    def create_ward_round(db: Session, lab_id: int, user_id: int, data: dict) -> WardRound:
        ward_round = WardRound(lab_id=lab_id, created_by=user_id, **data)
        db.add(ward_round)
        db.flush()
        log_action(db, "nhdw.ward_round.create", ward_round.id, lab_id, user_id, data)
        return ward_round

    @staticmethod
    def add_ward_round_participant(db: Session, lab_id: int, round_id: str, participant: dict) -> WardRound:
        ward_round = db.query(WardRound).filter(
            WardRound.id == round_id,
            WardRound.lab_id == lab_id,
            ~WardRound.is_deleted,
        ).first()
        if not ward_round:
            raise HTTPException(status_code=404, detail="Ward round not found")
        participants = ward_round.participants or []
        participants.append(participant)
        ward_round.participants = participants
        db.flush()
        return ward_round

    @staticmethod
    def update_ward_round_findings(db: Session, lab_id: int, user_id: int, round_id: str, data: dict) -> WardRound:
        ward_round = db.query(WardRound).filter(
            WardRound.id == round_id,
            WardRound.lab_id == lab_id,
            ~WardRound.is_deleted,
        ).first()
        if not ward_round:
            raise HTTPException(status_code=404, detail="Ward round not found")
        for k, v in data.items():
            if hasattr(ward_round, k):
                setattr(ward_round, k, v)
        ward_round.updated_by = user_id
        db.flush()
        return ward_round

    @staticmethod
    def list_ward_rounds(
        db: Session, lab_id: int, department_id: int | None = None,
        patient_id: int | None = None,
        from_date: datetime | None = None, to_date: datetime | None = None,
        skip: int = 0, limit: int = 50,
    ) -> list[WardRound]:
        q = db.query(WardRound).filter(
            WardRound.lab_id == lab_id, ~WardRound.is_deleted,
        )
        if department_id is not None:
            q = q.filter(WardRound.department_id == department_id)
        if patient_id is not None:
            q = q.filter(WardRound.patient_id == patient_id)
        if from_date is not None:
            q = q.filter(WardRound.round_date >= from_date)
        if to_date is not None:
            q = q.filter(WardRound.round_date <= to_date)
        return q.order_by(WardRound.round_date.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_ward_round(db: Session, round_id: str, lab_id: int) -> WardRound:
        ward_round = db.query(WardRound).filter(
            WardRound.id == round_id,
            WardRound.lab_id == lab_id,
            ~WardRound.is_deleted,
        ).first()
        if not ward_round:
            raise HTTPException(status_code=404, detail="Ward round not found")
        return ward_round

    @staticmethod
    def create_care_plan(db: Session, lab_id: int, user_id: int, data: dict) -> CarePlan:
        care_plan = CarePlan(lab_id=lab_id, created_by=user_id, **data)
        db.add(care_plan)
        db.flush()
        log_action(db, "nhdw.care_plan.create", care_plan.id, lab_id, user_id, data)
        return care_plan

    @staticmethod
    def get_care_plans(db: Session, patient_id: int, lab_id: int) -> list[CarePlan]:
        return db.query(CarePlan).filter(
            CarePlan.patient_id == patient_id,
            CarePlan.lab_id == lab_id,
            ~CarePlan.is_deleted,
        ).order_by(CarePlan.start_date.desc()).all()

    @staticmethod
    def update_care_plan(db: Session, lab_id: int, user_id: int, plan_id: str, data: dict) -> CarePlan:
        plan = db.query(CarePlan).filter(
            CarePlan.id == plan_id,
            CarePlan.lab_id == lab_id,
            ~CarePlan.is_deleted,
        ).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Care plan not found")
        for k, v in data.items():
            if hasattr(plan, k):
                setattr(plan, k, v)
        plan.updated_by = user_id
        db.flush()
        log_action(db, "nhdw.care_plan.update", plan_id, lab_id, user_id, data)
        return plan

    @staticmethod
    def review_care_plan(db: Session, lab_id: int, user_id: int, plan_id: str, review_notes: str | None = None) -> CarePlan:
        plan = db.query(CarePlan).filter(
            CarePlan.id == plan_id,
            CarePlan.lab_id == lab_id,
            ~CarePlan.is_deleted,
        ).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Care plan not found")
        plan.review_date = datetime.now(UTC)
        if review_notes:
            plan.notes = (plan.notes or "") + f"\n[Review by {user_id}]: {review_notes}"
        plan.updated_by = user_id
        db.flush()
        log_action(db, "nhdw.care_plan.review", plan_id, lab_id, user_id)
        return plan

    @staticmethod
    def occupancy_dashboard(db: Session, lab_id: int, department_id: int | None = None) -> dict:
        q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)
        if department_id is not None:
            q = q.join(Room).filter(Room.department_id == department_id)
        total = q.count()
        available = q.filter(Bed.status == "available").count()
        occupied = q.filter(Bed.status == "occupied").count()
        reserved = q.filter(Bed.status == "reserved").count()
        maintenance = q.filter(Bed.status == "maintenance").count()
        cleaning = q.filter(Bed.status == "cleaning").count()
        rate = round((occupied / total) * 100, 1) if total > 0 else 0.0
        return {
            "total_beds": total, "available": available, "occupied": occupied,
            "reserved": reserved, "maintenance": maintenance, "cleaning": cleaning,
            "occupancy_rate_percent": rate,
        }

    @staticmethod
    def room_occupancy_by_department(db: Session, lab_id: int) -> list[dict]:
        depts = db.query(Department).filter(
            Department.lab_id == lab_id, ~Department.is_deleted,
        ).all()
        result = []
        for dept in depts:
            total = db.query(func.count(Bed.id)).join(Room).filter(
                Room.department_id == dept.id,
                Bed.lab_id == lab_id,
                ~Bed.is_deleted,
            ).scalar() or 0
            occupied = db.query(func.count(Bed.id)).join(Room).filter(
                Room.department_id == dept.id,
                Bed.lab_id == lab_id,
                ~Bed.is_deleted,
                Bed.status == "occupied",
            ).scalar() or 0
            result.append({
                "department_id": dept.id, "department_name": dept.name,
                "total_beds": total, "occupied_beds": occupied,
                "occupancy_rate": round((occupied / total) * 100, 1) if total > 0 else 0.0,
            })
        return result

    @staticmethod
    def send_message(db: Session, lab_id: int, user_id: int, data: dict) -> HospitalMessage:
        msg = HospitalMessage(lab_id=lab_id, created_by=user_id, sender_id=user_id, **data)
        db.add(msg)
        db.flush()
        log_action(db, "nhdw.message.send", msg.id, lab_id, user_id, data)
        return msg

    @staticmethod
    def list_messages(
        db: Session, lab_id: int, user_id: int,
        direction: str = "received", skip: int = 0, limit: int = 50,
    ) -> list[HospitalMessage]:
        q = db.query(HospitalMessage).filter(
            HospitalMessage.lab_id == lab_id, ~HospitalMessage.is_deleted,
        )
        if direction == "received":
            q = q.filter(HospitalMessage.recipient_id == user_id)
        else:
            q = q.filter(HospitalMessage.sender_id == user_id)
        return q.order_by(HospitalMessage.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_message(db: Session, message_id: str, lab_id: int) -> HospitalMessage:
        msg = db.query(HospitalMessage).filter(
            HospitalMessage.id == message_id,
            HospitalMessage.lab_id == lab_id,
            ~HospitalMessage.is_deleted,
        ).first()
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
        return msg

    @staticmethod
    def mark_message_read(db: Session, lab_id: int, user_id: int, message_id: str) -> HospitalMessage:
        msg = db.query(HospitalMessage).filter(
            HospitalMessage.id == message_id,
            HospitalMessage.lab_id == lab_id,
            HospitalMessage.recipient_id == user_id,
        ).first()
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
        msg.is_read = True
        msg.read_at = datetime.now(UTC)
        db.flush()
        return msg

    @staticmethod
    def get_message_thread(db: Session, message_id: str, lab_id: int) -> list[HospitalMessage]:
        root = db.query(HospitalMessage).filter(
            HospitalMessage.id == message_id,
            HospitalMessage.lab_id == lab_id,
            ~HospitalMessage.is_deleted,
        ).first()
        if not root:
            raise HTTPException(status_code=404, detail="Message not found")
        result = [root]
        replies = db.query(HospitalMessage).filter(
            HospitalMessage.parent_message_id == message_id,
            HospitalMessage.lab_id == lab_id,
            ~HospitalMessage.is_deleted,
        ).order_by(HospitalMessage.created_at.asc()).all()
        result.extend(replies)
        return result

    @staticmethod
    def create_alert(db: Session, lab_id: int, user_id: int, data: dict) -> HospitalAlert:
        alert = HospitalAlert(lab_id=lab_id, created_by=user_id, triggered_by=user_id, **data)
        db.add(alert)
        db.flush()
        log_action(db, "nhdw.alert.create", alert.id, lab_id, user_id, data)
        return alert

    @staticmethod
    def list_alerts(
        db: Session, lab_id: int, severity: AlertSeverity | None = None,
        is_resolved: bool | None = None, skip: int = 0, limit: int = 50,
    ) -> list[HospitalAlert]:
        q = db.query(HospitalAlert).filter(
            HospitalAlert.lab_id == lab_id, ~HospitalAlert.is_deleted,
        )
        if severity is not None:
            q = q.filter(HospitalAlert.severity == severity)
        if is_resolved is not None:
            q = q.filter(HospitalAlert.is_resolved == is_resolved)
        return q.order_by(HospitalAlert.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def acknowledge_alert(db: Session, lab_id: int, user_id: int, alert_id: str) -> HospitalAlert:
        alert = db.query(HospitalAlert).filter(
            HospitalAlert.id == alert_id,
            HospitalAlert.lab_id == lab_id,
            ~HospitalAlert.is_deleted,
        ).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        acknowledged = alert.acknowledged_by or []
        if user_id not in acknowledged:
            acknowledged.append(user_id)
        alert.acknowledged_by = acknowledged
        db.flush()
        return alert

    @staticmethod
    def resolve_alert(db: Session, lab_id: int, user_id: int, alert_id: str) -> HospitalAlert:
        alert = db.query(HospitalAlert).filter(
            HospitalAlert.id == alert_id,
            HospitalAlert.lab_id == lab_id,
            ~HospitalAlert.is_deleted,
        ).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        alert.is_resolved = True
        alert.resolved_at = datetime.now(UTC)
        alert.resolved_by = user_id
        db.flush()
        log_action(db, "nhdw.alert.resolve", alert_id, lab_id, user_id)
        return alert

    @staticmethod
    def escalate_alert(db: Session, lab_id: int, user_id: int, alert_id: str) -> HospitalAlert:
        alert = db.query(HospitalAlert).filter(
            HospitalAlert.id == alert_id,
            HospitalAlert.lab_id == lab_id,
            ~HospitalAlert.is_deleted,
        ).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        if alert.severity == AlertSeverity.INFO:
            alert.severity = AlertSeverity.WARNING
        elif alert.severity == AlertSeverity.WARNING:
            alert.severity = AlertSeverity.CRITICAL
        elif alert.severity == AlertSeverity.CRITICAL:
            alert.severity = AlertSeverity.EMERGENCY
        alert.updated_by = user_id
        db.flush()
        return alert

    @staticmethod
    def create_telemedicine_session(db: Session, lab_id: int, user_id: int, data: dict) -> TelemedicineSession:
        session = TelemedicineSession(lab_id=lab_id, created_by=user_id, **data)
        db.add(session)
        db.flush()
        log_action(db, "nhdw.telemedicine.create", session.id, lab_id, user_id, data)
        return session

    @staticmethod
    def list_telemedicine_sessions(
        db: Session, lab_id: int, patient_id: int | None = None,
        provider_id: int | None = None, status: str | None = None,
        skip: int = 0, limit: int = 50,
    ) -> list[TelemedicineSession]:
        q = db.query(TelemedicineSession).filter(
            TelemedicineSession.lab_id == lab_id,
            ~TelemedicineSession.is_deleted,
        )
        if patient_id is not None:
            q = q.filter(TelemedicineSession.patient_id == patient_id)
        if provider_id is not None:
            q = q.filter(TelemedicineSession.provider_id == provider_id)
        if status is not None:
            q = q.filter(TelemedicineSession.status == status)
        return q.order_by(TelemedicineSession.scheduled_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def start_telemedicine_session(db: Session, lab_id: int, session_id: str) -> TelemedicineSession:
        session = db.query(TelemedicineSession).filter(
            TelemedicineSession.id == session_id,
            TelemedicineSession.lab_id == lab_id,
            ~TelemedicineSession.is_deleted,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session.started_at = datetime.now(UTC)
        session.status = "in_progress"
        db.flush()
        return session

    @staticmethod
    def end_telemedicine_session(db: Session, lab_id: int, session_id: str, data: dict | None = None) -> TelemedicineSession:
        session = db.query(TelemedicineSession).filter(
            TelemedicineSession.id == session_id,
            TelemedicineSession.lab_id == lab_id,
            ~TelemedicineSession.is_deleted,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session.ended_at = datetime.now(UTC)
        session.status = "completed"
        if data:
            if data.get("notes"):
                session.notes = data["notes"]
            if data.get("recording_url"):
                session.recording_url = data["recording_url"]
        db.flush()
        return session

    @staticmethod
    def record_telemedicine_session(db: Session, lab_id: int, user_id: int, session_id: str, data: dict) -> TelemedicineSession:
        session = db.query(TelemedicineSession).filter(
            TelemedicineSession.id == session_id,
            TelemedicineSession.lab_id == lab_id,
            ~TelemedicineSession.is_deleted,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        for k, v in data.items():
            if hasattr(session, k):
                setattr(session, k, v)
        session.updated_by = user_id
        db.flush()
        return session

    @staticmethod
    def create_resource_schedule(db: Session, lab_id: int, user_id: int, data: dict) -> ResourceSchedule:
        schedule = ResourceSchedule(lab_id=lab_id, created_by=user_id, **data)
        db.add(schedule)
        db.flush()
        log_action(db, "nhdw.resource_schedule.create", schedule.id, lab_id, user_id, data)
        return schedule

    @staticmethod
    def update_resource_schedule(db: Session, lab_id: int, user_id: int, schedule_id: str, data: dict) -> ResourceSchedule:
        schedule = db.query(ResourceSchedule).filter(
            ResourceSchedule.id == schedule_id,
            ResourceSchedule.lab_id == lab_id,
            ~ResourceSchedule.is_deleted,
        ).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        for k, v in data.items():
            if hasattr(schedule, k):
                setattr(schedule, k, v)
        schedule.updated_by = user_id
        db.flush()
        return schedule

    @staticmethod
    def list_resource_schedules(
        db: Session, lab_id: int, resource_type: str | None = None,
        resource_id: int | None = None, scheduled_date: date | None = None,
        skip: int = 0, limit: int = 50,
    ) -> list[ResourceSchedule]:
        q = db.query(ResourceSchedule).filter(
            ResourceSchedule.lab_id == lab_id,
            ~ResourceSchedule.is_deleted,
        )
        if resource_type is not None:
            q = q.filter(ResourceSchedule.resource_type == resource_type)
        if resource_id is not None:
            q = q.filter(ResourceSchedule.resource_id == resource_id)
        if scheduled_date is not None:
            q = q.filter(ResourceSchedule.scheduled_date == scheduled_date)
        return q.order_by(ResourceSchedule.start_time.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def save_dashboard_config(db: Session, lab_id: int, user_id: int, data: dict) -> DashboardConfiguration:
        existing = db.query(DashboardConfiguration).filter(
            DashboardConfiguration.user_id == user_id,
            DashboardConfiguration.lab_id == lab_id,
            ~DashboardConfiguration.is_deleted,
        ).first()
        if existing:
            existing.config_json = data.get("config_json", existing.config_json)
            existing.role = data.get("role", existing.role)
            existing.department_id = data.get("department_id", existing.department_id)
            existing.is_default = data.get("is_default", existing.is_default)
            existing.updated_by = user_id
            db.flush()
            log_action(db, "nhdw.dashboard_config.update", existing.id, lab_id, user_id, data)
            return existing
        config = DashboardConfiguration(
            lab_id=lab_id, created_by=user_id, user_id=user_id, **data,
        )
        db.add(config)
        db.flush()
        log_action(db, "nhdw.dashboard_config.create", config.id, lab_id, user_id, data)
        return config

    @staticmethod
    def get_dashboard_config(db: Session, lab_id: int, role: str) -> DashboardConfiguration | None:
        config = db.query(DashboardConfiguration).filter(
            DashboardConfiguration.role == role,
            DashboardConfiguration.lab_id == lab_id,
            ~DashboardConfiguration.is_deleted,
        ).first()
        if config:
            return config
        return db.query(DashboardConfiguration).filter(
            DashboardConfiguration.is_default,
            DashboardConfiguration.lab_id == lab_id,
            ~DashboardConfiguration.is_deleted,
        ).first()

    @staticmethod
    def create_shift_report(db: Session, lab_id: int, user_id: int, data: dict) -> ShiftReport:
        report = ShiftReport(lab_id=lab_id, created_by=user_id, report_author=user_id, **data)
        db.add(report)
        db.flush()
        log_action(db, "nhdw.shift_report.create", report.id, lab_id, user_id, data)
        return report

    @staticmethod
    def list_shift_reports(
        db: Session, lab_id: int, department_id: int | None = None,
        shift_type: str | None = None, shift_date: date | None = None,
        skip: int = 0, limit: int = 50,
    ) -> list[ShiftReport]:
        q = db.query(ShiftReport).filter(
            ShiftReport.lab_id == lab_id, ~ShiftReport.is_deleted,
        )
        if department_id is not None:
            q = q.filter(ShiftReport.department_id == department_id)
        if shift_type is not None:
            q = q.filter(ShiftReport.shift_type == shift_type)
        if shift_date is not None:
            q = q.filter(ShiftReport.shift_date == shift_date)
        return q.order_by(ShiftReport.shift_date.desc(), ShiftReport.start_time.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def hospital_kpis(db: Session, lab_id: int, days: int = 30) -> dict:
        from .kpi import (
            admission_rate,
            average_length_of_stay,
            bed_occupancy_rate,
            discharge_rate,
            readmission_rate_30d,
            transfer_rate,
        )
        return {
            "bed_occupancy": bed_occupancy_rate(db, lab_id),
            "average_length_of_stay": average_length_of_stay(db, lab_id),
            "admissions_30d": admission_rate(db, lab_id, days),
            "discharges_30d": discharge_rate(db, lab_id, days),
            "transfers_30d": transfer_rate(db, lab_id, days),
            "readmissions_30d": readmission_rate_30d(db, lab_id, days),
        }

    @staticmethod
    def admin_dashboard(db: Session, lab_id: int) -> dict:
        from .kpi import (
            admission_rate,
            bed_occupancy_rate,
            discharge_rate,
            occupancy_by_department,
            transfer_rate,
        )
        return {
            "occupancy": bed_occupancy_rate(db, lab_id),
            "occupancy_by_department": occupancy_by_department(db, lab_id),
            "admissions_today": admission_rate(db, lab_id, 1)["total_admissions"],
            "discharges_today": discharge_rate(db, lab_id, 1)["total_discharges"],
            "transfers_today": transfer_rate(db, lab_id, 1)["total_transfers"],
            "active_admissions": db.query(func.count(Admission.id)).filter(
                Admission.lab_id == lab_id,
                ~Admission.is_deleted,
                Admission.discharge_date.is_(None),
            ).scalar() or 0,
        }

    @staticmethod
    def executive_dashboard(db: Session, lab_id: int) -> dict:
        from .kpi import (
            admission_rate,
            average_length_of_stay,
            bed_occupancy_rate,
            discharge_rate,
            emergency_wait_times,
            or_utilization_rate,
            readmission_rate_30d,
            transfer_rate,
        )
        return {
            "occupancy": bed_occupancy_rate(db, lab_id),
            "alos": average_length_of_stay(db, lab_id),
            "admissions_30d": admission_rate(db, lab_id, 30)["total_admissions"],
            "discharges_30d": discharge_rate(db, lab_id, 30)["total_discharges"],
            "transfers_30d": transfer_rate(db, lab_id, 30)["total_transfers"],
            "readmission_rate_30d": readmission_rate_30d(db, lab_id, 30),
            "or_utilization": or_utilization_rate(db, lab_id),
            "emergency_wait_times": emergency_wait_times(db, lab_id, 7),
            "active_admissions": db.query(func.count(Admission.id)).filter(
                Admission.lab_id == lab_id,
                ~Admission.is_deleted,
                Admission.discharge_date.is_(None),
            ).scalar() or 0,
        }

    @staticmethod
    def clinical_dashboard(db: Session, lab_id: int) -> dict:
        pending_tasks = db.query(func.count(ClinicalTask.id)).filter(
            ClinicalTask.lab_id == lab_id,
            ~ClinicalTask.is_deleted,
            ClinicalTask.status == ClinicalTaskStatus.PENDING,
        ).scalar() or 0
        active_admissions = db.query(func.count(Admission.id)).filter(
            Admission.lab_id == lab_id,
            ~Admission.is_deleted,
            Admission.discharge_date.is_(None),
        ).scalar() or 0
        today_queue = db.query(func.count(QueueEntry.id)).filter(
            QueueEntry.lab_id == lab_id,
            ~QueueEntry.is_deleted,
            QueueEntry.queue_date == date.today(),
        ).scalar() or 0
        return {
            "pending_tasks": pending_tasks,
            "active_admissions": active_admissions,
            "today_queue_count": today_queue,
        }
