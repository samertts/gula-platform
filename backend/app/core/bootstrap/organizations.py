from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.organization import Organization

from .models import OrganizationDef

logger = logging.getLogger("gula.bootstrap.organizations")


def seed_organizations(
    orgs: list[OrganizationDef],
    db: Session | None = None,
) -> int:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    created = 0
    try:
        for odef in orgs:
            existing = db.query(Organization).filter(
                Organization.org_id == odef.org_id
            ).first()
            if existing:
                continue
            org = Organization(
                org_id=odef.org_id,
                name_en=odef.name_en,
                name_ar=odef.name_ar,
                org_type=odef.org_type,
                parent_org_id=odef.parent_org_id,
                governorate_id=odef.governorate_id,
                directorate_id=odef.directorate_id,
                is_active=odef.is_active,
            )
            db.add(org)
            created += 1

        if created:
            db.commit()
            logger.info("Seeded %d organizations", created)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed organizations: %s", exc)
        raise
    finally:
        if own_session:
            db.close()

    return created


def get_organization(db: Session, org_id: str) -> Optional[Organization]:
    return db.query(Organization).filter(Organization.org_id == org_id).first()
