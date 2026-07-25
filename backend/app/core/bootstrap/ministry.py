from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.organization import Organization

from .models import NATIONAL_ORG_NAME_AR, NATIONAL_ORG_NAME_EN, NATIONAL_ORG_TYPE
from .organizations import seed_organizations

logger = logging.getLogger("gula.bootstrap.ministry")


MINISTRY_ORG_ID = "org-iraq-moh"


def seed_ministry_of_health(db: Session | None = None) -> bool:
    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    try:
        existing = (
            db.query(Organization)
            .filter(
                Organization.org_id == MINISTRY_ORG_ID,
            )
            .first()
        )
        if existing:
            logger.info("Ministry of Health already exists (org_id=%s)", MINISTRY_ORG_ID)
            return True

        from .models import OrganizationDef

        moh = OrganizationDef(
            org_id=MINISTRY_ORG_ID,
            name_en=NATIONAL_ORG_NAME_EN,
            name_ar=NATIONAL_ORG_NAME_AR,
            org_type=NATIONAL_ORG_TYPE,
            parent_org_id=None,
            governorate_id=None,
            directorate_id=None,
            is_active=True,
        )
        created = seed_organizations([moh], db=db)
        if created:
            logger.info("Ministry of Health created (org_id=%s)", MINISTRY_ORG_ID)
        return True
    except Exception as exc:
        logger.error("Failed to seed Ministry of Health: %s", exc)
        return False
    finally:
        if own_session:
            db.close()
