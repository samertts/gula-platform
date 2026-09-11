from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.identity.models.niam_organization import NIAMOrganization
from app.identity.models.person import Person


def seed_master_admin(session: Session) -> str:
    admin_id = str(uuid.uuid4())
    admin = Person(
        id=admin_id,
        given_name="Master",
        family_name="Admin",
        full_name_ar="مدير النظام",
        email="admin@niam.gula.iq",
        is_active=True,
    )
    session.add(admin)
    session.flush()
    return admin.id


def seed_platform_organization(session: Session) -> str:
    org_id = str(uuid.uuid4())
    org = NIAMOrganization(
        id=org_id,
        org_id="GULA-PLATFORM",
        name_en="GULA National Digital Health Platform",
        name_ar="منصة جولا الوطنية للصحة الرقمية",
        org_type="ministry",
        status="active",
        is_active=True,
    )
    session.add(org)
    session.flush()
    return org.id
