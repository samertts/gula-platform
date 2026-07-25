from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.organization import Facility, Organization

from .models import FacilityDef

logger = logging.getLogger("gula.bootstrap.facilities")


def seed_facilities(
    facilities: list[FacilityDef],
    db: Session | None = None,
) -> int:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    created = 0
    try:
        for fdef in facilities:
            existing = (
                db.query(Facility)
                .filter(
                    Facility.facility_id == fdef.facility_id,
                )
                .first()
            )
            if existing:
                continue
            org = (
                db.query(Organization)
                .filter(
                    Organization.org_id == fdef.organization_id,
                )
                .first()
            )
            if not org:
                logger.warning(
                    "Organization %s not found — skipping facility %s",
                    fdef.organization_id,
                    fdef.facility_id,
                )
                continue
            fac = Facility(
                facility_id=fdef.facility_id,
                name_en=fdef.name_en,
                name_ar=fdef.name_ar,
                facility_type=fdef.facility_type,
                organization_id=org.id,
                is_active=fdef.is_active,
            )
            db.add(fac)
            created += 1

        if created:
            db.commit()
            logger.info("Seeded %d facilities", created)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed facilities: %s", exc)
        raise
    finally:
        if own_session:
            db.close()

    return created


def seed_platform_facilities(db: Session | None = None) -> int:
    from .models import (
        PLATFORM_DIRECTORATE_NAME_EN,
        PLATFORM_HOSPITAL_NAME_AR,
        PLATFORM_HOSPITAL_NAME_EN,
        PLATFORM_LAB_NAME,
        PLATFORM_ORG_NAME_EN,
    )

    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    created = 0
    try:
        platform_org = (
            db.query(Organization)
            .filter(
                Organization.name_en == PLATFORM_ORG_NAME_EN,
            )
            .first()
        )
        if not platform_org:
            logger.warning("Platform organization not found — skipping platform facilities")
            return 0

        platform_dir = (
            db.query(Organization)
            .filter(
                Organization.name_en == PLATFORM_DIRECTORATE_NAME_EN,
            )
            .first()
        )

        platform_hospital_org = (
            db.query(Organization)
            .filter(
                Organization.name_en == PLATFORM_HOSPITAL_NAME_EN,
            )
            .first()
        )

        facilities: list[FacilityDef] = []

        if platform_dir:
            facilities.append(
                FacilityDef(
                    facility_id="fac-platform-lab",
                    name_en=f"{PLATFORM_LAB_NAME} Laboratory",
                    name_ar=f"مختبر {PLATFORM_LAB_NAME}",
                    facility_type="laboratory",
                    organization_id=platform_dir.org_id,
                    is_active=True,
                ),
            )
            facilities.append(
                FacilityDef(
                    facility_id="fac-platform-blood-bank",
                    name_en=f"{PLATFORM_LAB_NAME} Blood Bank",
                    name_ar=f"بنك الدم - {PLATFORM_LAB_NAME}",
                    facility_type="blood_bank",
                    organization_id=platform_dir.org_id,
                    is_active=True,
                ),
            )
            facilities.append(
                FacilityDef(
                    facility_id="fac-platform-ph-lab",
                    name_en=f"{PLATFORM_LAB_NAME} Public Health Lab",
                    name_ar=f"مختبر الصحة العامة - {PLATFORM_LAB_NAME}",
                    facility_type="public_health_lab",
                    organization_id=platform_dir.org_id,
                    is_active=True,
                ),
            )
            facilities.append(
                FacilityDef(
                    facility_id="fac-platform-forensic-lab",
                    name_en=f"{PLATFORM_LAB_NAME} Forensic Laboratory",
                    name_ar=f"مختبر الطب العدلي - {PLATFORM_LAB_NAME}",
                    facility_type="forensic_lab",
                    organization_id=platform_dir.org_id,
                    is_active=True,
                ),
            )
            facilities.append(
                FacilityDef(
                    facility_id="fac-platform-ref-lab",
                    name_en=f"{PLATFORM_LAB_NAME} Reference Laboratory",
                    name_ar=f"مختبر مرجعي - {PLATFORM_LAB_NAME}",
                    facility_type="reference_lab",
                    organization_id=platform_dir.org_id,
                    is_active=True,
                ),
            )
            facilities.append(
                FacilityDef(
                    facility_id="fac-platform-research-lab",
                    name_en=f"{PLATFORM_LAB_NAME} Research Laboratory",
                    name_ar=f"مختبر أبحاث - {PLATFORM_LAB_NAME}",
                    facility_type="research_lab",
                    organization_id=platform_dir.org_id,
                    is_active=True,
                ),
            )

        if platform_hospital_org:
            facilities.append(
                FacilityDef(
                    facility_id="fac-platform-hospital",
                    name_en=PLATFORM_HOSPITAL_NAME_EN,
                    name_ar=PLATFORM_HOSPITAL_NAME_AR,
                    facility_type="hospital",
                    organization_id=platform_hospital_org.org_id,
                    is_active=True,
                ),
            )

        created = seed_facilities(facilities, db=db)
    finally:
        if own_session:
            db.close()

    return created
