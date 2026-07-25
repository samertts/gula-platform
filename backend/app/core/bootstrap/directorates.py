from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.organization import Organization

from .ministry import MINISTRY_ORG_ID
from .models import OrganizationDef
from .organizations import seed_organizations

logger = logging.getLogger("gula.bootstrap.directorates")


IRAQ_GOVERNORATES: list[dict] = [
    {"id": "bg", "name_en": "Baghdad", "name_ar": "بغداد"},
    {"id": "bb", "name_en": "Babylon", "name_ar": "بابل"},
    {"id": "ka", "name_en": "Karbala", "name_ar": "كربلاء"},
    {"id": "nj", "name_en": "Najaf", "name_ar": "النجف"},
    {"id": "qa", "name_en": "Al-Qadisiyyah", "name_ar": "القادسية"},
    {"id": "an", "name_en": "Al-Anbar", "name_ar": "الأنبار"},
    {"id": "ba", "name_en": "Basra", "name_ar": "البصرة"},
    {"id": "mu", "name_en": "Muthanna", "name_ar": "المثنى"},
    {"id": "dq", "name_en": "Dhi Qar", "name_ar": "ذي قار"},
    {"id": "di", "name_en": "Diyala", "name_ar": "ديالى"},
    {"id": "da", "name_en": "Dohuk", "name_ar": "دهوك"},
    {"id": "ar", "name_en": "Erbil", "name_ar": "أربيل"},
    {"id": "ha", "name_en": "Halabja", "name_ar": "حلبجة"},
    {"id": "ki", "name_en": "Kirkuk", "name_ar": "كركوك"},
    {"id": "ma", "name_en": "Maysan", "name_ar": "ميسان"},
    {"id": "ni", "name_en": "Nineveh", "name_ar": "نينوى"},
    {"id": "sa", "name_en": "Saladin", "name_ar": "صلاح الدين"},
    {"id": "su", "name_en": "Sulaymaniyah", "name_ar": "السليمانية"},
    {"id": "wa", "name_en": "Wasit", "name_ar": "واسط"},
]


def build_directorate_defs(parent_org_id: str = MINISTRY_ORG_ID) -> list[OrganizationDef]:
    defs: list[OrganizationDef] = []
    for gov in IRAQ_GOVERNORATES:
        gov_id = gov["id"]
        dir_id = f"dir-{gov_id}"
        defs.append(
            OrganizationDef(
                org_id=dir_id,
                name_en=f"{gov['name_en']} Health Directorate",
                name_ar=f"مديرية صحة {gov['name_ar']}",
                org_type="directorate",
                parent_org_id=parent_org_id,
                governorate_id=gov_id,
                directorate_id=None,
                is_active=True,
            ),
        )
    return defs


def seed_health_directorates(db: Session | None = None) -> int:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    try:
        moh = (
            db.query(Organization)
            .filter(
                Organization.org_id == MINISTRY_ORG_ID,
            )
            .first()
        )
        if not moh:
            logger.error("Ministry of Health not found — seed ministry first")
            return 0

        defs = build_directorate_defs()
        created = seed_organizations(defs, db=db)
        if created:
            logger.info("Seeded %d health directorates", created)
        else:
            logger.info("All health directorates already exist")
        return created
    except Exception as exc:
        logger.error("Failed to seed health directorates: %s", exc)
        return 0
    finally:
        if own_session:
            db.close()
