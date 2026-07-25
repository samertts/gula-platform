from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.organization import Facility, Organization

from .ministry import MINISTRY_ORG_ID

logger = logging.getLogger("gula.bootstrap.laboratories")


LAB_TYPES: list[dict] = [
    {
        "type": "public_health_lab",
        "name_en": "Public Health Laboratory",
        "name_ar": "مختبر الصحة العامة",
    },
    {"type": "blood_bank", "name_en": "Blood Bank", "name_ar": "بنك الدم"},
    {
        "type": "forensic_lab",
        "name_en": "Forensic Medicine Laboratory",
        "name_ar": "مختبر الطب العدلي",
    },
    {"type": "reference_lab", "name_en": "Reference Laboratory", "name_ar": "مختبر مرجعي"},
    {"type": "research_lab", "name_en": "Research Laboratory", "name_ar": "مختبر أبحاث"},
    {"type": "training_center", "name_en": "Training Center", "name_ar": "مركز تدريب"},
    {"type": "hospital_lab", "name_en": "Hospital Laboratory", "name_ar": "مختبر مستشفى"},
    {"type": "phc_lab", "name_en": "PHC Laboratory", "name_ar": "مختبر رعاية أولية"},
    {"type": "private_lab", "name_en": "Private Laboratory", "name_ar": "مختبر خاص"},
]


def seed_laboratory_types(db: Session | None = None) -> int:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    created = 0
    try:
        moh = (
            db.query(Organization)
            .filter(
                Organization.org_id == MINISTRY_ORG_ID,
            )
            .first()
        )

        for lt in LAB_TYPES:
            fac_id = f"lab-type-{lt['type']}"
            existing = (
                db.query(Facility)
                .filter(
                    Facility.facility_id == fac_id,
                )
                .first()
            )
            if existing:
                continue
            if moh:
                fac = Facility(
                    facility_id=fac_id,
                    name_en=lt["name_en"],
                    name_ar=lt["name_ar"],
                    facility_type=lt["type"],
                    organization_id=moh.id,
                    is_active=True,
                )
                db.add(fac)
                created += 1

        if created:
            db.commit()
            logger.info("Seeded %d laboratory type definitions", created)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed laboratory types: %s", exc)
        raise
    finally:
        if own_session:
            db.close()

    return created
