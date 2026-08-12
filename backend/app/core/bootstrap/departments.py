from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.lab import Lab

logger = logging.getLogger("gula.bootstrap.departments")

STANDARD_DEPARTMENTS: list[dict] = [
    {"code": "chem", "name_en": "Clinical Chemistry", "name_ar": "الكيمياء السريرية"},
    {"code": "hema", "name_en": "Hematology", "name_ar": "أمراض الدم"},
    {"code": "micro", "name_en": "Microbiology", "name_ar": "علم الأحياء الدقيقة"},
    {"code": "para", "name_en": "Parasitology", "name_ar": "علم الطفيليات"},
    {"code": "sero", "name_en": "Serology", "name_ar": "المصلية"},
    {"code": "immuno", "name_en": "Immunology", "name_ar": "علم المناعة"},
    {"code": "urine", "name_en": "Urinalysis", "name_ar": "تحليل البول"},
    {"code": "coag", "name_en": "Coagulation", "name_ar": "تجلط الدم"},
    {"code": "endo", "name_en": "Endocrinology", "name_ar": "الغدد الصماء"},
    {"code": "mol", "name_en": "Molecular Biology", "name_ar": "البيولوجيا الجزيئية"},
    {"code": "gen", "name_en": "Genetics", "name_ar": "علم الوراثة"},
    {"code": "tox", "name_en": "Toxicology", "name_ar": "علم السموم"},
    {"code": "histo", "name_en": "Histopathology", "name_ar": "علم الأنسجة المرضية"},
    {"code": "cyto", "name_en": "Cytopathology", "name_ar": "علم الخلايا المرضية"},
    {"code": "phleb", "name_en": "Phlebotomy", "name_ar": "سحب الدم"},
    {"code": "qa", "name_en": "Quality Assurance", "name_ar": "ضمان الجودة"},
]


def seed_departments(db: Session | None = None) -> int:
    from app.lims.models import Department

    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    created = 0
    try:
        labs = db.query(Lab).filter(Lab.is_active).all()
        if not labs:
            logger.info("No active labs found — skipping department seeding")
            return 0

        for lab in labs:
            for dept in STANDARD_DEPARTMENTS:
                existing = db.query(Department).filter(
                    Department.lab_id == lab.id,
                    Department.code == dept["code"],
                ).first()
                if existing:
                    continue
                dep = Department(
                    lab_id=lab.id,
                    code=dept["code"],
                    name=dept["name_en"],
                    name_ar=dept["name_ar"],
                    description=dept["name_en"],
                    is_active=True,
                    sort_order=STANDARD_DEPARTMENTS.index(dept),
                )
                db.add(dep)
                created += 1

        if created:
            db.commit()
            logger.info("Seeded %d departments across %d labs", created, len(labs))
    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed departments: %s", exc)
        raise
    finally:
        if own_session:
            db.close()

    return created
