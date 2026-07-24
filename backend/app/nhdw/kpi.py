from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC

from ..hospital.models import Bed, OperationTheater, Room
from ..hospital.models import HospitalDepartment as Department
from .models import Admission, Discharge, QueueEntry, Transfer


def bed_occupancy_rate(db: Session, lab_id: int, department_id: int | None = None, date_range: tuple[datetime, datetime] | None = None) -> dict:
    q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)
    if department_id is not None:
        q = q.join(Room).filter(Room.department_id == department_id)
    total = q.count()
    occupied = q.filter(Bed.status == "occupied").count()
    rate = round((occupied / total) * 100, 1) if total > 0 else 0.0
    return {
        "total_beds": total,
        "occupied_beds": occupied,
        "occupancy_rate_percent": rate,
        "available_beds": total - occupied,
        "department_id": department_id,
    }


def average_length_of_stay(db: Session, lab_id: int, department_id: int | None = None, date_range: tuple[datetime, datetime] | None = None) -> dict:
    q = db.query(
        func.avg(
            func.extract("epoch", Discharge.discharge_date - Admission.admission_date) / 86400.0,
        ),
    ).join(Admission, Discharge.admission_id == Admission.id).filter(
        Admission.lab_id == lab_id,
        ~Admission.is_deleted,
        Discharge.discharge_date.isnot(None),
    )
    if department_id is not None:
        q = q.filter(Admission.department_id == department_id)
    if date_range is not None:
        q = q.filter(Discharge.discharge_date.between(date_range[0], date_range[1]))
    avg_days = q.scalar()
    return {
        "average_length_of_stay_days": round(float(avg_days), 2) if avg_days else 0.0,
        "department_id": department_id,
    }


def admission_rate(db: Session, lab_id: int, days: int = 30, department_id: int | None = None, date_range: tuple[datetime, datetime] | None = None) -> dict:
    since = date_range[0] if date_range is not None else datetime.now(UTC) - timedelta(days=days)
    q = db.query(func.count(Admission.id)).filter(
        Admission.lab_id == lab_id,
        ~Admission.is_deleted,
        Admission.admission_date >= since,
    )
    if department_id is not None:
        q = q.filter(Admission.department_id == department_id)
    if date_range is not None:
        q = q.filter(Admission.admission_date <= date_range[1])
    total = q.scalar() or 0
    return {
        "period_days": days,
        "total_admissions": total,
        "daily_average": round(total / days, 2) if days > 0 else 0.0,
        "department_id": department_id,
    }


def discharge_rate(db: Session, lab_id: int, days: int = 30, department_id: int | None = None, date_range: tuple[datetime, datetime] | None = None) -> dict:
    since = date_range[0] if date_range is not None else datetime.now(UTC) - timedelta(days=days)
    q = db.query(func.count(Discharge.id)).join(
        Admission, Discharge.admission_id == Admission.id,
    ).filter(
        Admission.lab_id == lab_id,
        ~Admission.is_deleted,
        Discharge.discharge_date >= since,
    )
    if department_id is not None:
        q = q.filter(Admission.department_id == department_id)
    if date_range is not None:
        q = q.filter(Discharge.discharge_date <= date_range[1])
    total = q.scalar() or 0
    return {
        "period_days": days,
        "total_discharges": total,
        "daily_average": round(total / days, 2) if days > 0 else 0.0,
        "department_id": department_id,
    }


def transfer_rate(db: Session, lab_id: int, days: int = 30, department_id: int | None = None, date_range: tuple[datetime, datetime] | None = None) -> dict:
    since = date_range[0] if date_range is not None else datetime.now(UTC) - timedelta(days=days)
    q = db.query(func.count(Transfer.id)).filter(
        Transfer.lab_id == lab_id,
        ~Transfer.is_deleted,
        Transfer.transfer_date >= since,
    )
    if department_id is not None:
        q = q.filter(
            (Transfer.from_department_id == department_id) | (Transfer.to_department_id == department_id),
        )
    if date_range is not None:
        q = q.filter(Transfer.transfer_date <= date_range[1])
    total = q.scalar() or 0
    return {
        "period_days": days,
        "total_transfers": total,
        "daily_average": round(total / days, 2) if days > 0 else 0.0,
        "department_id": department_id,
    }


def readmission_rate_30d(db: Session, lab_id: int, days: int = 30, department_id: int | None = None, date_range: tuple[datetime, datetime] | None = None) -> dict:
    thirty_days_ago = datetime.now(UTC) - timedelta(days=days)
    ninety_days_ago = datetime.now(UTC) - timedelta(days=days + 30)
    if date_range is not None:
        thirty_days_ago = date_range[0]
        ninety_days_ago = date_range[0] - timedelta(days=30)
    discharged = db.query(Discharge.admission_id).join(
        Admission, Discharge.admission_id == Admission.id,
    ).filter(
        Admission.lab_id == lab_id,
        ~Admission.is_deleted,
        Discharge.discharge_date.between(ninety_days_ago, thirty_days_ago),
    )
    if department_id is not None:
        discharged = discharged.filter(Admission.department_id == department_id)
    discharged_ids = [r[0] for r in discharged.all()]
    if not discharged_ids:
        return {"readmission_rate_percent": 0.0, "total_discharged": 0, "readmissions": 0, "period_days": days}
    readmissions = db.query(func.count(Admission.id)).filter(
        Admission.lab_id == lab_id,
        ~Admission.is_deleted,
        Admission.patient_id.in_(
            db.query(Admission.patient_id).filter(Admission.id.in_(discharged_ids)),
        ),
        Admission.admission_date > thirty_days_ago,
    ).scalar() or 0
    total_discharged = len(discharged_ids)
    rate = round((readmissions / total_discharged) * 100, 2) if total_discharged > 0 else 0.0
    return {
        "readmission_rate_percent": rate,
        "total_discharged": total_discharged,
        "readmissions": readmissions,
        "period_days": days,
    }


def emergency_wait_times(db: Session, lab_id: int, days: int = 7, date_range: tuple[datetime, datetime] | None = None) -> dict:
    since = date_range[0] if date_range is not None else datetime.now(UTC) - timedelta(days=days)
    entries = db.query(
        QueueEntry.check_in_time,
        QueueEntry.seen_time,
    ).filter(
        QueueEntry.lab_id == lab_id,
        ~QueueEntry.is_deleted,
        QueueEntry.check_in_time.isnot(None),
        QueueEntry.seen_time.isnot(None),
        QueueEntry.queue_date >= since.date(),
    ).all()
    wait_times = []
    for entry in entries:
        delta = (entry.seen_time - entry.check_in_time).total_seconds() / 60.0
        if delta >= 0:
            wait_times.append(delta)
    if not wait_times:
        return {
            "period_days": days,
            "average_wait_minutes": 0.0,
            "median_wait_minutes": 0.0,
            "p95_wait_minutes": 0.0,
            "p99_wait_minutes": 0.0,
            "max_wait_minutes": 0.0,
        }
    sorted_times = sorted(wait_times)
    n = len(sorted_times)
    return {
        "period_days": days,
        "average_wait_minutes": round(sum(wait_times) / n, 1),
        "median_wait_minutes": round(sorted_times[n // 2], 1),
        "p95_wait_minutes": round(sorted_times[int(n * 0.95)], 1) if n > 1 else round(sorted_times[-1], 1),
        "p99_wait_minutes": round(sorted_times[int(n * 0.99)], 1) if n > 1 else round(sorted_times[-1], 1),
        "max_wait_minutes": round(sorted_times[-1], 1),
    }


def or_utilization_rate(db: Session, lab_id: int, days: int = 30, hospital_id: int | None = None, date_range: tuple[datetime, datetime] | None = None) -> dict:
    q = db.query(func.count(OperationTheater.id)).filter(
        OperationTheater.lab_id == lab_id,
        ~OperationTheater.is_deleted,
    )
    if hospital_id is not None:
        q = q.filter(OperationTheater.hospital_id == hospital_id)
    total_ors = q.scalar() or 0
    in_use = db.query(func.count(OperationTheater.id)).filter(
        OperationTheater.lab_id == lab_id,
        ~OperationTheater.is_deleted,
        OperationTheater.status == "in_use",
    )
    if hospital_id is not None:
        in_use = in_use.filter(OperationTheater.hospital_id == hospital_id)
    in_use_count = in_use.scalar() or 0
    utilization = round((in_use_count / total_ors) * 100, 1) if total_ors > 0 else 0.0
    return {
        "total_operation_theaters": total_ors,
        "in_use": in_use_count,
        "utilization_rate_percent": utilization,
    }


def bed_turnover_interval(db: Session, lab_id: int, department_id: int | None = None, date_range: tuple[datetime, datetime] | None = None) -> dict:
    q = db.query(func.count(Discharge.id)).join(
        Admission, Discharge.admission_id == Admission.id,
    ).filter(
        Admission.lab_id == lab_id,
        ~Admission.is_deleted,
    )
    if department_id is not None:
        q = q.filter(Admission.department_id == department_id)
    if date_range is not None:
        q = q.filter(Discharge.discharge_date.between(date_range[0], date_range[1]))
    total_discharges = q.scalar() or 0
    bed_q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)
    if department_id is not None:
        bed_q = bed_q.join(Room).filter(Room.department_id == department_id)
    total_beds = bed_q.count()
    interval = round((total_beds * 30.0) / total_discharges, 2) if total_discharges > 0 else 0.0
    return {
        "bed_turnover_interval_days": interval,
        "total_discharges": total_discharges,
        "total_beds": total_beds,
        "department_id": department_id,
    }


def occupancy_by_department(db: Session, lab_id: int) -> list[dict]:
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
        rate = round((occupied / total) * 100, 1) if total > 0 else 0.0
        result.append({
            "department_id": dept.id,
            "department_name": dept.name,
            "department_name_ar": dept.name_ar,
            "total_beds": total,
            "occupied_beds": occupied,
            "available_beds": total - occupied,
            "occupancy_rate_percent": rate,
        })
    return result


def executive_summary(db: Session, lab_id: int) -> dict:
    occ = bed_occupancy_rate(db, lab_id)
    alos = average_length_of_stay(db, lab_id)
    adm = admission_rate(db, lab_id, 30)
    dis = discharge_rate(db, lab_id, 30)
    trf = transfer_rate(db, lab_id, 30)
    readm = readmission_rate_30d(db, lab_id, 30)
    ewt = emergency_wait_times(db, lab_id, 7)
    oru = or_utilization_rate(db, lab_id, 30)
    occ_by_dept = occupancy_by_department(db, lab_id)
    active_admissions = db.query(func.count(Admission.id)).filter(
        Admission.lab_id == lab_id,
        ~Admission.is_deleted,
    ).scalar() or 0
    return {
        "bed_occupancy": occ,
        "average_length_of_stay": alos,
        "admissions_30d": adm,
        "discharges_30d": dis,
        "transfers_30d": trf,
        "readmission_rate_30d": readm,
        "emergency_wait_times": ewt,
        "or_utilization": oru,
        "occupancy_by_department": occ_by_dept,
        "active_admissions": active_admissions,
    }
