"""Seed the GULA Platform's own organizations (org → directorate → hospital)."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.organization import Organization

from .models import (
    PLATFORM_DIRECTORATE_NAME_AR,
    PLATFORM_DIRECTORATE_NAME_EN,
    PLATFORM_HOSPITAL_NAME_AR,
    PLATFORM_HOSPITAL_NAME_EN,
    PLATFORM_ORG_NAME_AR,
    PLATFORM_ORG_NAME_EN,
)

logger = logging.getLogger("gula.bootstrap.platform_orgs")

PLATFORM_ORG_ID = "org-gula-platform"
PLATFORM_DIRECTORATE_ID = "dir-gula-platform"
PLATFORM_HOSPITAL_ID = "hosp-gula-platform"


def _seed_org(db: Session, org_id: str, name_en: str, name_ar: str, org_type: str,
              parent_org_id: str | None) -> int:
    existing = db.query(Organization).filter(Organization.org_id == org_id).first()
    if existing:
        return 0
    db.add(
        Organization(
            org_id=org_id,
            name_en=name_en,
            name_ar=name_ar,
            org_type=org_type,
            parent_org_id=parent_org_id,
            is_active=True,
        )
    )
    return 1


def seed_platform_organizations(db: Session | None = None) -> int:
    """Seed GULA's own org hierarchy so platform facilities can attach."""
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    created = 0
    try:
        created += _seed_org(
            db, PLATFORM_ORG_ID, PLATFORM_ORG_NAME_EN, PLATFORM_ORG_NAME_AR,
            "platform", None,
        )
        created += _seed_org(
            db, PLATFORM_DIRECTORATE_ID, PLATFORM_DIRECTORATE_NAME_EN,
            PLATFORM_DIRECTORATE_NAME_AR, "directorate", PLATFORM_ORG_ID,
        )
        created += _seed_org(
            db, PLATFORM_HOSPITAL_ID, PLATFORM_HOSPITAL_NAME_EN,
            PLATFORM_HOSPITAL_NAME_AR, "hospital", PLATFORM_DIRECTORATE_ID,
        )
        if created:
            db.commit()
            logger.info("Seeded %d platform organizations", created)
        return created
    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed platform organizations: %s", exc)
        return 0
    finally:
        if own_session:
            db.close()
