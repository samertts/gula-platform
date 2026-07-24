from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.lab import Lab
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.models.sample import Sample
from app.security.auth import hash_password

logger = logging.getLogger("gula.bootstrap.demo_data")


def _deterministic_uuid(seed: str) -> UUID:
    h = hashlib.md5(seed.encode(), usedforsecurity=False)
    return uuid.UUID(h.hexdigest())


DEMO_PATIENTS: list[dict] = [
    {"full_name": "Ahmed Hassan Ali", "phone": "07700000001", "gender": "male", "age": 45},
    {"full_name": "Fatima Ibrahim Said", "phone": "07700000002", "gender": "female", "age": 32},
    {"full_name": "Mohammed Jassim Kadhim", "phone": "07700000003", "gender": "male", "age": 28},
    {"full_name": "Zainab Amer Salman", "phone": "07700000004", "gender": "female", "age": 55},
    {"full_name": "Ali Hussein Nasser", "phone": "07700000005", "gender": "male", "age": 60},
    {"full_name": "Noora Khalid Mahmood", "phone": "07700000006", "gender": "female", "age": 24},
    {"full_name": "Hassan Karim Rashid", "phone": "07700000007", "gender": "male", "age": 38},
    {"full_name": "Layla Saadoun Fadhil", "phone": "07700000008", "gender": "female", "age": 42},
    {"full_name": "Omar Younis Ibrahim", "phone": "07700000009", "gender": "male", "age": 19},
    {"full_name": "Sara Murtadha Abdul", "phone": "07700000010", "gender": "female", "age": 35},
    {"full_name": "Khalid Salim Noori", "phone": "07700000011", "gender": "male", "age": 50},
    {"full_name": "Aisha Tariq Hamid", "phone": "07700000012", "gender": "female", "age": 29},
    {"full_name": "Yasser Qasim Abdul", "phone": "07700000013", "gender": "male", "age": 33},
    {"full_name": "Mariam Falah Hassan", "phone": "07700000014", "gender": "female", "age": 67},
    {"full_name": "Rami Adel Shakir", "phone": "07700000015", "gender": "male", "age": 41},
]

DEMO_TECHNICIANS: list[dict] = [
    {"name": "Technician One", "email": "tech1@demo.gula.iq"},
    {"name": "Technician Two", "email": "tech2@demo.gula.iq"},
    {"name": "Technician Three", "email": "tech3@demo.gula.iq"},
]

DEMO_DOCTORS: list[dict] = [
    {"name": "Dr. Ahmed Al-Jubouri", "email": "doctor1@demo.gula.iq"},
    {"name": "Dr. Sarah Al-Tikriti", "email": "doctor2@demo.gula.iq"},
    {"name": "Dr. Karim Al-Maliki", "email": "doctor3@demo.gula.iq"},
]

TEST_TYPES_POOL = [
    {"code": "glucose", "name": "Glucose (Fasting)", "unit": "mg/dL", "low": 70, "high": 100},
    {"code": "hemoglobin", "name": "Hemoglobin", "unit": "g/dL", "low": 12, "high": 17},
    {"code": "wbc", "name": "White Blood Cells", "unit": "x10^3/uL", "low": 4.0, "high": 11.0},
    {"code": "platelets", "name": "Platelets", "unit": "x10^3/uL", "low": 150, "high": 400},
    {"code": "creatinine", "name": "Creatinine", "unit": "mg/dL", "low": 0.6, "high": 1.2},
    {"code": "cholesterol", "name": "Total Cholesterol", "unit": "mg/dL", "low": 125, "high": 200},
    {"code": "triglycerides", "name": "Triglycerides", "unit": "mg/dL", "low": 0, "high": 150},
    {"code": "hba1c", "name": "HbA1c", "unit": "%", "low": 4.0, "high": 5.7},
    {"code": "alt", "name": "ALT (SGPT)", "unit": "U/L", "low": 7, "high": 56},
    {"code": "ast", "name": "AST (SGOT)", "unit": "U/L", "low": 5, "high": 40},
]


def seed_demo_data(db: Session | None = None) -> dict[str, int]:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    counts: dict[str, int] = {
        "patients": 0,
        "technicians": 0,
        "doctors": 0,
        "orders": 0,
        "samples": 0,
        "results": 0,
    }

    try:
        lab = db.query(Lab).filter(Lab.is_active).first()
        if not lab:
            logger.warning("No active lab found — skipping demo data")
            return counts

        existing_patients = db.query(Patient).count()
        if existing_patients > 5:
            logger.info("Demo data appears to already exist (%d patients) — skipping", existing_patients)
            return counts

        for pd in DEMO_PATIENTS:
            patient = Patient(
                lab_id=lab.id,
                full_name=pd["full_name"],
                phone=pd["phone"],
                gender=pd["gender"],
                age=pd["age"],
                national_id_hash=None,
            )
            db.add(patient)
            db.flush()
            counts["patients"] += 1

        demo_password = hash_password("Demo@123")
        for td in DEMO_TECHNICIANS:
            existing = db.query(LabUser).filter(LabUser.email == td["email"]).first()
            if not existing:
                tech = LabUser(
                    lab_id=lab.id,
                    name=td["name"],
                    email=td["email"],
                    password_hash=demo_password,
                    role="technician",
                    is_active=True,
                )
                db.add(tech)
                db.flush()
                counts["technicians"] += 1

        for dd in DEMO_DOCTORS:
            existing = db.query(LabUser).filter(LabUser.email == dd["email"]).first()
            if not existing:
                doctor = LabUser(
                    lab_id=lab.id,
                    name=dd["name"],
                    email=dd["email"],
                    password_hash=demo_password,
                    role="doctor",
                    is_active=True,
                )
                db.add(doctor)
                db.flush()
                counts["doctors"] += 1

        patients = db.query(Patient).filter(Patient.lab_id == lab.id).all()
        now = datetime.now(timezone.utc)

        for i, patient in enumerate(patients):
            test = TEST_TYPES_POOL[i % len(TEST_TYPES_POOL)]
            order_ref = f"DEMO-ORD-{i+1:04d}"

            existing_order = db.query(LabOrder).filter(
                LabOrder.order_id == order_ref,
            ).first()
            if existing_order:
                continue

            order = LabOrder(
                lab_id=lab.id,
                patient_id=patient.id,
                order_id=order_ref,
                test_code=test["code"],
                test_name=test["name"],
                status="completed",
                created_at=now - timedelta(days=i * 2),
                collection_date=now - timedelta(days=i * 2),
            )
            db.add(order)
            db.flush()
            counts["orders"] += 1

            sample = Sample(
                lab_id=lab.id,
                order_id=order.id,
                patient_id=patient.id,
                sample_type="blood",
                status="collected",
                collected_at=now - timedelta(days=i * 2),
            )
            db.add(sample)
            db.flush()
            counts["samples"] += 1

            import random
            result_value = round(
                random.uniform(test["low"] * 0.8, test["high"] * 1.2), 1,
            )
            result = LabResult(
                lab_id=lab.id,
                order_id=order.id,
                patient_id=patient.id,
                test_code=test["code"],
                test_name=test["name"],
                result=str(result_value),
                unit=test["unit"],
                normal_range_low=test["low"],
                normal_range_high=test["high"],
                status="verified",
                verified_by="demo_system",
                verified_at=now - timedelta(days=i * 2, hours=-2),
            )
            db.add(result)
            counts["results"] += 1

        db.commit()
        logger.info(
            "Demo data seeded: %(patients)d patients, %(technicians)d technicians, "
            "%(doctors)d doctors, %(orders)d orders, %(samples)d samples, %(results)d results",
            counts,
        )
    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed demo data: %s", exc)
        raise
    finally:
        if own_session:
            db.close()

    return counts
